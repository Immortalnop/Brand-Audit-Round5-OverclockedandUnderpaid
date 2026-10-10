"""Bounded, standard-library PDF text extraction.

Works only on bytes already fetched by the shared Transport; it never touches the
network. Supported subset: indirect objects and object streams, FlateDecode,
ASCIIHexDecode and ASCII85Decode streams, page-tree traversal with inherited
resources, per-font ToUnicode CMaps, simple single-byte fonts, form XObjects, and
the Tj, TJ, ' and " text operators.

Anything outside that subset is reported, never guessed: an encrypted file is
'encrypted', a file with text operators that cannot be mapped to Unicode is
'unsupported', and a file whose pages draw no text at all is 'no_text_layer'.
Every stage is capped (decoded bytes, objects, pages, text length, wall clock) so
a hostile or oversized file costs bounded time and memory.
"""
import base64
import re
import zlib
from time import monotonic

MAX_OBJECTS = 20_000
MAX_PAGES = 300
MAX_DECODED_PER_STREAM = 4_000_000
MAX_DECODED_TOTAL = 16_000_000
MAX_CONTENT_BYTES = 6_000_000
MAX_TEXT_CHARS = 20_000
MAX_DEPTH = 48
DEFAULT_TIME_BUDGET_S = 4.0

_WS = b"\x00\t\n\x0c\r "
_DELIMS = b"()<>[]{}/%"
_REGULAR = rb"[^\x00\t\n\x0c\r ()<>\[\]{}/%]"
_TOKEN_RE = re.compile(
    rb"(?P<ws>[\x00\t\n\x0c\r ]+)"
    rb"|(?P<comment>%[^\r\n]*)"
    rb"|(?P<dopen><<)|(?P<dclose>>>)"
    rb"|(?P<aopen>\[)|(?P<aclose>\])"
    rb"|(?P<lit>\()"
    rb"|(?P<hex><[0-9A-Fa-f\x00\t\n\x0c\r ]*>)"
    rb"|(?P<name>/" + _REGULAR + rb"*)"
    rb"|(?P<num>[+-]?(?:\d+\.\d*|\.\d+|\d+)(?!" + _REGULAR + rb"))"
    rb"|(?P<kw>" + _REGULAR + rb"+)"
    rb"|(?P<other>[{}<>)])")
_OBJ_RE = re.compile(rb"(?<![0-9])(\d{1,10})[\x00\t\n\x0c\r ]+(\d{1,5})[\x00\t\n\x0c\r ]+obj(?!" + _REGULAR + rb")")
_LIT_SPECIAL = re.compile(rb"[\\()]")
_ESCAPES = {ord("n"): 10, ord("r"): 13, ord("t"): 9, ord("b"): 8, ord("f"): 12,
            ord("("): 40, ord(")"): 41, ord("\\"): 92}
_NAME_ESCAPE = re.compile(rb"#([0-9A-Fa-f]{2})")


class _PdfError(Exception):
    pass


class _Budget(Exception):
    pass


class Ref:
    __slots__ = ("num",)

    def __init__(self, num):
        self.num = num


class Keyword(bytes):
    pass


def _name(raw):
    return _NAME_ESCAPE.sub(lambda m: bytes([int(m.group(1), 16)]), raw[1:]).decode("latin-1")


def _read_literal(data, pos):
    """Parse a literal string starting just after '('. Returns (bytes, end)."""
    out = bytearray()
    depth = 1
    n = len(data)
    while pos < n:
        match = _LIT_SPECIAL.search(data, pos)
        if match is None:
            out += data[pos:]
            return bytes(out), n
        out += data[pos:match.start()]
        pos = match.start()
        char = data[pos]
        if char == 0x5C:
            pos += 1
            if pos >= n:
                break
            char = data[pos]
            if char in _ESCAPES:
                out.append(_ESCAPES[char])
                pos += 1
            elif 0x30 <= char <= 0x37:
                value = 0
                end = pos
                while end < n and end < pos + 3 and 0x30 <= data[end] <= 0x37:
                    value = value * 8 + data[end] - 0x30
                    end += 1
                out.append(value & 0xFF)
                pos = end
            elif char == 0x0D:
                pos += 1
                if pos < n and data[pos] == 0x0A:
                    pos += 1
            elif char == 0x0A:
                pos += 1
            else:
                out.append(char)
                pos += 1
            continue
        if char == 0x28:
            depth += 1
        else:
            depth -= 1
            if depth == 0:
                return bytes(out), pos + 1
        out.append(char)
        pos += 1
    return bytes(out), n


class _Lexer:
    def __init__(self, data, pos=0):
        self.data = data
        self.pos = pos

    def next(self):
        """Next significant token as (kind, value), or None at end of data."""
        data = self.data
        while True:
            match = _TOKEN_RE.match(data, self.pos)
            if match is None:
                if self.pos >= len(data):
                    return None
                self.pos += 1
                continue
            kind = match.lastgroup
            self.pos = match.end()
            if kind in ("ws", "comment"):
                continue
            if kind == "lit":
                value, self.pos = _read_literal(data, self.pos)
                return ("str", value)
            if kind == "hex":
                digits = re.sub(rb"[^0-9A-Fa-f]", b"", match.group(0))
                if len(digits) % 2:
                    digits += b"0"
                return ("str", bytes.fromhex(digits.decode("ascii")))
            if kind == "name":
                return ("name", _name(match.group(0)))
            if kind == "num":
                text = match.group(0)
                if b"." in text:
                    try:
                        return ("num", float(text))
                    except ValueError:
                        return ("num", 0.0)
                return ("num", int(text))
            if kind == "kw":
                return ("kw", Keyword(match.group(0)))
            return (kind, match.group(0))


def _parse(lexer, token, depth=0):
    """Parse one PDF object whose first token is `token`."""
    if token is None:
        raise _PdfError("unexpected end of data")
    if depth > MAX_DEPTH:
        raise _PdfError("nesting too deep")
    kind, value = token
    if kind == "dopen":
        result = {}
        while True:
            key = lexer.next()
            if key is None:
                raise _PdfError("unterminated dictionary")
            if key[0] == "dclose":
                return result
            if key[0] != "name":
                continue
            item = lexer.next()
            if item is not None and item[0] == "dclose":
                result[key[1]] = None
                return result
            result[key[1]] = _parse(lexer, item, depth + 1)
    if kind == "aopen":
        result = []
        while True:
            item = lexer.next()
            if item is None:
                raise _PdfError("unterminated array")
            if item[0] == "aclose":
                return result
            result.append(_parse(lexer, item, depth + 1))
    if kind == "num" and isinstance(value, int) and value >= 0:
        saved = lexer.pos
        second = lexer.next()
        if second is not None and second[0] == "num" and isinstance(second[1], int):
            third = lexer.next()
            if third is not None and third[0] == "kw" and third[1] == b"R":
                return Ref(value)
        lexer.pos = saved
        return value
    if kind == "kw":
        if value == b"true":
            return True
        if value == b"false":
            return False
        if value == b"null":
            return None
        return value
    if kind in ("num", "str", "name"):
        return value
    return None


def _ascii_hex(data):
    digits = re.sub(rb"[^0-9A-Fa-f]", b"", data.split(b">", 1)[0])
    if len(digits) % 2:
        digits += b"0"
    return bytes.fromhex(digits.decode("ascii"))


def _ascii85(data):
    body = data.strip()
    if body.startswith(b"<~"):
        body = body[2:]
    body = body.split(b"~>", 1)[0]
    return base64.a85decode(body, adobe=False, ignorechars=_WS)


class _Document:
    def __init__(self, data, time_budget_s):
        self.data = data
        self.raw = {}
        self.cache = {}
        self.decoded_total = 0
        self.deadline = monotonic() + time_budget_s
        self.fonts = {}
        self.cmaps = {}
        self.stats = {"text_ops": 0, "codes": 0, "unmapped": 0, "images": 0,
                      "unsupported_filters": 0, "content_errors": 0, "time_limited": False}

    def check_time(self):
        if monotonic() > self.deadline:
            self.stats["time_limited"] = True
            raise _Budget()

    # ----- object table -------------------------------------------------
    def index(self):
        data = self.data
        pos = 0
        count = 0
        while count < MAX_OBJECTS:
            match = _OBJ_RE.search(data, pos)
            if match is None:
                break
            count += 1
            if count % 512 == 0:
                self.check_time()
            num = int(match.group(1))
            lexer = _Lexer(data, match.end())
            try:
                value = _parse(lexer, lexer.next())
            except (_PdfError, ValueError, RecursionError):
                pos = match.end()
                continue
            stream = None
            after = lexer.pos
            following = lexer.next()
            if following is not None and following[0] == "kw" and following[1] == b"stream":
                start = lexer.pos
                if data[start:start + 2] == b"\r\n":
                    start += 2
                elif data[start:start + 1] in (b"\n", b"\r"):
                    start += 1
                length = value.get("Length") if isinstance(value, dict) else None
                end = -1
                if isinstance(length, int) and 0 <= length <= len(data) - start:
                    probe = data.find(b"endstream", start + length, start + length + 64)
                    if probe != -1:
                        end = start + length
                if end == -1:
                    end = data.find(b"endstream", start)
                    if end == -1:
                        end = len(data)
                stream = data[start:end]
                after = end + len(b"endstream")
            self.raw[num] = (value, stream)
            pos = max(after, match.end())
        self._expand_object_streams()

    def _expand_object_streams(self):
        for num, (value, stream) in list(self.raw.items()):
            if not (isinstance(value, dict) and value.get("Type") == "ObjStm" and stream is not None):
                continue
            try:
                decoded = self.decode_stream(value, stream)
            except _Budget:
                return
            if decoded is None:
                continue
            count = self.resolve(value.get("N"))
            first = self.resolve(value.get("First"))
            if not isinstance(count, int) or not isinstance(first, int) or count > MAX_OBJECTS:
                continue
            header = _Lexer(decoded[:first])
            pairs = []
            for _ in range(count):
                a, b = header.next(), header.next()
                if not a or not b or a[0] != "num" or b[0] != "num":
                    break
                pairs.append((a[1], b[1]))
            for objnum, offset in pairs:
                if not isinstance(objnum, int) or not isinstance(offset, int) or objnum in self.raw:
                    continue
                lexer = _Lexer(decoded, first + offset)
                try:
                    self.raw[objnum] = (_parse(lexer, lexer.next()), None)
                except (_PdfError, ValueError, RecursionError):
                    continue

    def resolve(self, value, hops=0):
        while isinstance(value, Ref) and hops < 32:
            entry = self.raw.get(value.num)
            value = entry[0] if entry else None
            hops += 1
        return value

    def stream_of(self, value):
        """(dict, decoded bytes) for a stream reference, or (dict, None)."""
        if isinstance(value, Ref):
            entry = self.raw.get(value.num)
            if entry is None:
                return None, None
            key = value.num
            if key not in self.cache:
                self.cache[key] = self.decode_stream(entry[0], entry[1]) if entry[1] is not None else None
            return entry[0], self.cache[key]
        return (value if isinstance(value, dict) else None), None

    # ----- stream filters ------------------------------------------------
    def decode_stream(self, info, raw):
        if raw is None or not isinstance(info, dict):
            return None
        filters = self.resolve(info.get("Filter"))
        if filters is None:
            filters = []
        elif not isinstance(filters, list):
            filters = [filters]
        params = self.resolve(info.get("DecodeParms"))
        param_list = params if isinstance(params, list) else [params] * len(filters)
        data = raw
        for index, name in enumerate(self.resolve(f) for f in filters):
            param = self.resolve(param_list[index]) if index < len(param_list) else None
            if isinstance(param, dict) and isinstance(self.resolve(param.get("Predictor")), int) \
                    and self.resolve(param.get("Predictor")) > 1:
                self.stats["unsupported_filters"] += 1
                return None
            try:
                if name in ("FlateDecode", "Fl"):
                    data = self._inflate(data)
                elif name in ("ASCIIHexDecode", "AHx"):
                    data = _ascii_hex(data)
                elif name in ("ASCII85Decode", "A85"):
                    data = _ascii85(data)
                else:
                    self.stats["unsupported_filters"] += 1
                    return None
            except (ValueError, zlib.error):
                return None
            if data is None:
                return None
        return data

    def _inflate(self, raw):
        allowed = min(MAX_DECODED_PER_STREAM, MAX_DECODED_TOTAL - self.decoded_total)
        if allowed <= 0:
            raise _Budget()
        decoder = zlib.decompressobj()
        chunks = []
        size = 0
        try:
            for offset in range(0, len(raw), 65536):
                chunk = decoder.decompress(raw[offset:offset + 65536], allowed - size)
                chunks.append(chunk)
                size += len(chunk)
                if size >= allowed or decoder.unconsumed_tail or decoder.eof:
                    break
        except zlib.error:
            if not chunks:
                return None
        self.decoded_total += size
        return b"".join(chunks)

    # ----- fonts ---------------------------------------------------------
    def font(self, ref):
        key = ref.num if isinstance(ref, Ref) else id(ref)
        if key in self.fonts:
            return self.fonts[key]
        info = self.resolve(ref)
        font = {"cmap": None, "lengths": (1,), "two_byte": False}
        if isinstance(info, dict):
            font["two_byte"] = info.get("Subtype") == "Type0"
            to_unicode = info.get("ToUnicode")
            if isinstance(to_unicode, Ref):
                font["cmap"], font["lengths"] = self.cmap(to_unicode)
            if font["two_byte"] and not font["cmap"]:
                font["lengths"] = (2,)
        self.fonts[key] = font
        return font

    def cmap(self, ref):
        if ref.num in self.cmaps:
            return self.cmaps[ref.num]
        _, data = self.stream_of(ref)
        mapping = {}
        lengths = set()
        if data:
            text = data.decode("latin-1")
            for block in re.findall(r"begincodespacerange(.*?)endcodespacerange", text, re.S):
                for low in re.findall(r"<([0-9A-Fa-f]+)>\s*<[0-9A-Fa-f]+>", block):
                    lengths.add(max(1, len(low) // 2))
            for block in re.findall(r"beginbfchar(.*?)endbfchar", text, re.S):
                for src, dst in re.findall(r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]*)>", block):
                    if len(mapping) < 100_000:
                        mapping[bytes.fromhex(_even(src))] = _utf16(dst)
                        lengths.add(len(src) // 2 or 1)
            for block in re.findall(r"beginbfrange(.*?)endbfrange", text, re.S):
                for low, high, rest in re.findall(
                        r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*(<[0-9A-Fa-f]*>|\[[^\]]*\])", block):
                    width = len(low) // 2 or 1
                    start, stop = int(low, 16), int(high, 16)
                    if stop < start or stop - start > 65535:
                        continue
                    lengths.add(width)
                    if rest.startswith("["):
                        targets = re.findall(r"<([0-9A-Fa-f]*)>", rest)
                        for offset, dst in enumerate(targets[:stop - start + 1]):
                            mapping[(start + offset).to_bytes(width, "big")] = _utf16(dst)
                    else:
                        dst = rest[1:-1]
                        base = int(dst, 16) if dst else 0
                        dst_width = max(2, len(dst) // 2)
                        for offset in range(stop - start + 1):
                            if len(mapping) >= 100_000:
                                break
                            value = (base + offset).to_bytes(dst_width, "big", signed=False) \
                                if base + offset < 256 ** dst_width else b""
                            mapping[(start + offset).to_bytes(width, "big")] = \
                                value.decode("utf-16-be", "replace") if value else ""
        result = (mapping or None, tuple(sorted(lengths or {1}, reverse=True)))
        self.cmaps[ref.num] = result
        return result

    def decode_text(self, raw, font):
        self.stats["text_ops"] += 1
        if font is None or (not font["cmap"] and not font["two_byte"]):
            self.stats["codes"] += len(raw)
            return raw.decode("cp1252", "replace")
        cmap = font["cmap"]
        if not cmap:
            codes = max(1, len(raw) // 2)
            self.stats["codes"] += codes
            self.stats["unmapped"] += codes
            return ""
        out = []
        pos = 0
        while pos < len(raw):
            for width in font["lengths"]:
                code = raw[pos:pos + width]
                if len(code) == width and code in cmap:
                    out.append(cmap[code])
                    pos += width
                    break
            else:
                width = font["lengths"][-1]
                if not font["two_byte"] and width == 1:
                    out.append(raw[pos:pos + 1].decode("cp1252", "replace"))
                else:
                    self.stats["unmapped"] += 1
                pos += width
            self.stats["codes"] += 1
        return "".join(out)

    # ----- pages and content --------------------------------------------
    def pages(self):
        catalog = None
        for value, _ in self.raw.values():
            if isinstance(value, dict) and value.get("Type") == "Catalog":
                catalog = value
        found = []
        seen = set()

        def walk(node_ref, inherited, depth):
            if len(found) >= MAX_PAGES or depth > 32:
                return
            key = node_ref.num if isinstance(node_ref, Ref) else None
            if key is not None:
                if key in seen:
                    return
                seen.add(key)
            node = self.resolve(node_ref)
            if not isinstance(node, dict):
                return
            resources = node.get("Resources", inherited)
            if node.get("Type") == "Pages" or "Kids" in node:
                for kid in self.resolve(node.get("Kids")) or []:
                    walk(kid, resources, depth + 1)
            else:
                found.append((node, resources))

        if catalog is not None:
            walk(catalog.get("Pages"), None, 0)
        if not found:
            for num in sorted(self.raw):
                value = self.raw[num][0]
                if isinstance(value, dict) and value.get("Type") == "Page" and len(found) < MAX_PAGES:
                    found.append((value, self._inherited_resources(value)))
        return found

    def _inherited_resources(self, page):
        node = page
        for _ in range(32):
            if not isinstance(node, dict):
                return None
            if "Resources" in node:
                return node["Resources"]
            node = self.resolve(node.get("Parent"))
        return None

    def page_content(self, page):
        contents = page.get("Contents")
        refs = self.resolve(contents) if isinstance(contents, Ref) and isinstance(self.resolve(contents), list) else contents
        refs = refs if isinstance(refs, list) else [refs]
        parts = []
        for ref in refs:
            _, data = self.stream_of(ref)
            if data:
                parts.append(data)
        return b"\n".join(parts)

    def run_content(self, data, resources, out, depth=0, budget=None):
        """Interpret a content stream, appending decoded text to `out`."""
        if depth > 4 or not data:
            return
        budget = budget if budget is not None else [MAX_CONTENT_BYTES]
        if budget[0] <= 0:
            return
        budget[0] -= len(data)
        resources = self.resolve(resources)
        resources = resources if isinstance(resources, dict) else {}
        fonts = self.resolve(resources.get("Font"))
        fonts = fonts if isinstance(fonts, dict) else {}
        xobjects = self.resolve(resources.get("XObject"))
        xobjects = xobjects if isinstance(xobjects, dict) else {}
        lexer = _Lexer(data)
        operands = []
        font = None
        steps = 0
        # Layout tracking: a separator is written only when the text position moved
        # since the last string, a newline only when the baseline changed. Text that
        # a generator splits across BT/ET blocks on one line therefore stays on one
        # line, and a word split across consecutive strings is not broken apart.
        layout = {"y": 0.0, "line_start_y": 0.0, "last_y": None, "moved": False, "newline": False}

        def emit(text):
            if not text:
                return
            if layout["last_y"] is not None:
                if layout["newline"] or abs(layout["y"] - layout["last_y"]) > 1.0:
                    out.append("\n")
                elif layout["moved"]:
                    out.append(" ")
            out.append(text)
            layout.update(last_y=layout["y"], moved=False, newline=False)
        while True:
            steps += 1
            if steps % 4096 == 0:
                self.check_time()
                if sum(len(s) for s in out) > MAX_TEXT_CHARS * 2:
                    return
            token = lexer.next()
            if token is None:
                return
            kind, value = token
            if kind != "kw":
                try:
                    operands.append(_parse(lexer, token))
                except (_PdfError, ValueError, RecursionError):
                    self.stats["content_errors"] += 1
                    return
                if len(operands) > 64:
                    operands = operands[-8:]
                continue
            op = bytes(value)
            if op == b"BI":
                end = re.search(rb"[\x00\t\n\x0c\r ]EI(?=[\x00\t\n\x0c\r ]|$)", data[lexer.pos:])
                lexer.pos = lexer.pos + end.end() if end else len(data)
                self.stats["images"] += 1
            elif op == b"Tf" and operands:
                name = operands[0] if isinstance(operands[0], str) else None
                ref = fonts.get(name) if name else None
                font = self.font(ref) if ref is not None else None
            elif op == b"Tj" and operands and isinstance(operands[-1], bytes):
                emit(self.decode_text(operands[-1], font))
            elif op in (b"'", b'"') and operands and isinstance(operands[-1], bytes):
                layout["newline"] = True
                emit(self.decode_text(operands[-1], font))
            elif op == b"TJ" and operands and isinstance(operands[-1], list):
                for item in operands[-1]:
                    if isinstance(item, bytes):
                        emit(self.decode_text(item, font))
                    elif isinstance(item, (int, float)) and item < -180:
                        layout["moved"] = True
            elif op in (b"Td", b"TD"):
                ty = operands[1] if len(operands) >= 2 and isinstance(operands[1], (int, float)) else 0
                layout["line_start_y"] += ty
                layout.update(y=layout["line_start_y"], moved=True)
            elif op == b"Tm":
                ty = operands[5] if len(operands) >= 6 and isinstance(operands[5], (int, float)) else layout["y"]
                layout.update(y=ty, line_start_y=ty, moved=True)
            elif op == b"T*":
                layout.update(newline=True, moved=True)
            elif op == b"BT":
                layout.update(y=0.0, line_start_y=0.0, moved=True)
            elif op == b"Do" and operands and isinstance(operands[-1], str):
                ref = xobjects.get(operands[-1])
                info, form = self.stream_of(ref) if isinstance(ref, Ref) else (None, None)
                if isinstance(info, dict) and info.get("Subtype") == "Image":
                    self.stats["images"] += 1
                elif isinstance(info, dict) and info.get("Subtype") == "Form" and form:
                    out.append(" ")
                    self.run_content(form, info.get("Resources", resources), out, depth + 1, budget)
                    layout["moved"] = True
            operands = []


def _even(hex_digits):
    return hex_digits if len(hex_digits) % 2 == 0 else "0" + hex_digits


def _utf16(hex_digits):
    if not hex_digits:
        return ""
    return bytes.fromhex(_even(hex_digits)).decode("utf-16-be", "replace")


def _clean(parts):
    text = "".join(parts)
    text = "".join(ch if ch.isprintable() or ch == "\n" else " " for ch in text)
    lines = (" ".join(line.split()) for line in text.splitlines())
    return "\n".join(line for line in lines if line)


def extract_pdf_text(data, time_budget_s=DEFAULT_TIME_BUDGET_S, truncated=False):
    """Return a dict: status, text, pages, text_chars, has_images, time_limited,
    truncated. Status is one of ok, no_text_layer, unsupported, encrypted,
    not_pdf or malformed. Text is returned only when status is ok."""
    result = {"status": "malformed", "text": "", "pages": 0, "text_chars": 0,
              "has_images": False, "time_limited": False, "truncated": bool(truncated)}
    if not data or b"%PDF-" not in data[:1024]:
        result["status"] = "not_pdf"
        return result
    if re.search(rb"/Encrypt[\x00\t\n\x0c\r /<]", data):
        result["status"] = "encrypted"
        return result
    document = _Document(data, time_budget_s)
    parts = []
    try:
        document.index()
        pages = document.pages()
        result["pages"] = len(pages)
        budget = [MAX_CONTENT_BYTES]
        for page, resources in pages:
            document.check_time()
            document.run_content(document.page_content(page), resources, parts, 0, budget)
            parts.append("\n")
            if sum(len(p) for p in parts) > MAX_TEXT_CHARS * 2 or budget[0] <= 0:
                break
    except _Budget:
        pass
    except Exception:  # hostile input must never fail the audit; keep any text already read
        if not parts:
            return result
    stats = document.stats
    result["time_limited"] = stats["time_limited"]
    result["has_images"] = stats["images"] > 0 or any(
        isinstance(v, dict) and v.get("Subtype") == "Image" for v, _ in document.raw.values())
    if not result["pages"]:
        return result
    text = _clean(parts)
    if stats["text_ops"] == 0 or not text.strip():
        if stats["text_ops"] == 0 and not (stats["unsupported_filters"] or stats["content_errors"]
                                            or stats["time_limited"] or truncated):
            result["status"] = "no_text_layer"
        else:
            result["status"] = "unsupported"
        return result
    unmapped_ratio = stats["unmapped"] / stats["codes"] if stats["codes"] else 0.0
    visible = [ch for ch in text if not ch.isspace()]
    alnum_ratio = sum(ch.isalnum() for ch in visible) / len(visible)
    bad_ratio = sum(ch == "\ufffd" or "\ue000" <= ch <= "\uf8ff" for ch in visible) / len(visible)
    if unmapped_ratio > 0.3 or alnum_ratio < 0.5 or bad_ratio > 0.05:
        result["status"] = "unsupported"
        return result
    result["status"] = "ok"
    result["text"] = text[:MAX_TEXT_CHARS]
    result["text_chars"] = len(result["text"])
    return result
