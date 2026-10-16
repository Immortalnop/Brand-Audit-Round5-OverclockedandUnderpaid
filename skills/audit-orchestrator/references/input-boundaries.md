# Input and numeric boundaries

The default runtime remains standard-library-only. `common/json_boundary.py`
is shared by agent loading, report/packet reads, acquisition JSON-LD extraction
and output validation.

Public file reads request at most the byte limit plus one and reject excess:

| Input | Limit |
| --- | --- |
| Agent handoff | 2 MiB |
| Evidence packet supplied for merge | 512 KiB |
| Saved report | 50 MiB |

UTF-8, UTF-8 BOM and BOM-declared UTF-16 are accepted; output is UTF-8. Invalid
Unicode, duplicate keys and nonfinite numbers are rejected. No arbitrary object
is converted to text to make it a valid semantic value. Nesting is limited to
40 levels, traversal to 300,000 nodes, and generic collections to 10,000 members.
Generic strings are limited to 200,000 characters. Agent strings are limited to
2,000 characters and generic agent collections to 100 members; narrower existing
check-specific limits apply to sources, queries, references and entities.

The report renderer checks its known contracts and safely renders missing optional
fields. Wrong roots/member types produce normal errors. Packet registries reject
duplicate IDs before semantic use. Envelopes validate all nested types before set
construction or hash lookups. JSON and Markdown writers replace their destination
only after a complete successful UTF-8 write; rejected input preserves existing
files. Validation and rendering make no network requests.

JSON-LD records extraction states and per-block diagnostics. Non-JSON NaN and
Infinity tokens are malformed. Syntactically legal numbers outside supported
range, excessive nesting and excessive collections are processing limitations.
Duplicate keys are ambiguity, not a claim that the JSON grammar forbids them.
Other usable blocks remain in the immutable snapshot. New diagnostics do not
yet constitute the complete Phase 5 schema/absence repair.

Numbers support at most 100 significant decimal digits and adjusted decimal
exponents from -100 through 100; numeric token text is limited to 128 characters.
Integer JSON tokens support at most 100 digits. General snapshot/report numbers
remain JSON integer/float values. `common/money.py` uses bounded Decimal locally
for monetary comparisons, preserving signs, decimals, exponents and zero while
rejecting booleans, nonfinite values and junk. Visible money supports documented
US/EU grouping and two-place comma decimals; markup money accepts decimal/exponent
numbers rather than arbitrary currency text. The compatibility `parse_price`
helper returns a bounded float; native markup comparisons use Decimal.

These choices follow JSON's allowance for processor range limits and Python's
explicit hooks for constants and object pairs. They do not claim full JSON-LD
conformance. See [RFC 8259](https://www.rfc-editor.org/rfc/rfc8259) and
[Python JSON documentation](https://docs.python.org/3.14/library/json.html).

JSON floating literals must also round-trip through their retained float string
without changing the Decimal value; otherwise they are a processing limitation.
Textual monetary values retain the bounded Decimal precision directly.
