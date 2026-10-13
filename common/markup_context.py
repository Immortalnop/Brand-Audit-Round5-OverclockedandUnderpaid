"""Conservative context from delivered markup; no computed CSS or browser state."""
from html.parser import HTMLParser
import re


def in_chrome(frames):
    return any(f['tag'] in ('header', 'nav', 'footer', 'announcement-bar', 'page-header')
               or f['a'].get('role', '').lower() in ('banner', 'navigation', 'contentinfo')
               for f in frames)


class InlineDisplay(HTMLParser):
    """Only unconditional, simple display:none rules with no competing display
    declaration qualify. Conditional/compound overrides veto the simple rule.
    External styles and dynamic state remain unmeasured.
    """
    def __init__(self):
        super().__init__()
        self.styles = []
        self.current = None
        self.conditional = False
        self.chars = 0
        self.hidden = set()

    def handle_starttag(self, tag, attrs):
        if tag == 'style':
            a = dict(attrs)
            self.current = []
            self.conditional = bool(a.get('media') and a.get('media') != 'all')

    def handle_data(self, data):
        if self.current is not None and self.chars < 200000:
            self.current.append(data[:200000-self.chars])
            self.chars += len(data)

    def handle_endtag(self, tag):
        if tag == 'style' and self.current is not None:
            self.styles.append((''.join(self.current),self.conditional))
            self.current = None

    def scan(self, html):
        self.feed(html)
        candidates, veto = set(), set()
        # A truncated stylesheet could contain an unseen override.
        if self.chars >= 200000: return self
        for css, conditional in self.styles:
            css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
            # Depth distinguishes unconditional rules from @media/@supports.
            depth, depths = 0, []
            for c in css:
                depths.append(depth)
                if c == '{': depth += 1
                elif c == '}': depth = max(0, depth-1)
            for match in re.finditer(r'([^{}]+)\{([^{}]*)\}', css):
                selectors, declarations = match.groups()
                display = re.findall(r'(?:^|;)\s*display\s*:\s*([^;]+)', declarations, re.I)
                if not display: continue
                tokens = set(re.findall(r'[.#][\w-]+', selectors))
                none = re.fullmatch(r'none\s*(?:!important\s*)?', display[-1].strip(), re.I)
                if not none or len(display) > 1:
                    veto.update(tokens)
                    continue
                if conditional or depths[match.start()] != 0: continue
                for selector in selectors.split(','):
                    selector = selector.strip()
                    if re.fullmatch(r'[.#][\w-]+', selector): candidates.add(selector)
        self.hidden = candidates-veto
        return self

    def matches(self, attrs):
        # An explicit inline display declaration takes precedence here; complex
        # stylesheet cascades are deliberately not inferred.
        if re.search(r'(?:^|;)\s*display\s*:', attrs.get('style', ''), re.I): return False
        tokens = {'.'+c for c in attrs.get('class', '').split()}
        if attrs.get('id'): tokens.add('#'+attrs['id'])
        return bool(tokens & self.hidden)
