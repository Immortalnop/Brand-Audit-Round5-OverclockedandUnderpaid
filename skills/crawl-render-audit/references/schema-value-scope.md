# Limited schema.org value interpretation

The native audit interprets a bounded subset of values, rather than claiming full
JSON-LD conformance. It never fetches a remote context. Recognized schema.org
contexts, simple inline base/vocabulary/prefix definitions and `@id` / `@vocab`
coercion are supported. Unknown remote contexts, scoped contexts and structured
value forms outside that subset are limitations. A foreign namespace with the
same local type name cannot establish schema.org applicability for new value rules.

Monetary values preserve signs and exponent meaning using bounded Decimal values;
booleans and arbitrary text are rejected. Processor range limits are limitations.
Visible values additionally allow the documented unambiguous decimal/grouping
forms. Currency validation checks uppercase three-letter **format**, without
claiming verified ISO membership. Zero and non-HTTP IRIs are not universally invalid.
Calendar checks verify supported ISO Date/DateTime dates, times and offsets;
other formats remain unassessed. Publication/update dates keep the existing
`structured-date-invalid` rule; malformed JSON keeps `malformed-jsonld`.

An Organization with only its name has no universal missing-required defect.
Consumer eligibility must name its use case. Google's Organization guide has no
required properties; its Product snippet requirements apply to that specific
Search feature. Enrichment opportunities remain optional.

Sources: [JSON-LD 1.1](https://www.w3.org/TR/json-ld11/),
[Google Organization](https://developers.google.com/search/docs/appearance/structured-data/organization),
[Google Product snippets](https://developers.google.com/search/docs/appearance/structured-data/product-snippet).
