# Nomenclátor data notes

Essential source caveats for maintainers and automated tools. See the
[technical documentation](docs-site/docs/technical-details/normalization-and-diffs.md)
for detailed comparison rules and the
[update runbook](docs-site/docs/operations/monthly-update.md) for collection steps.

## Source and provenance

- Use the full CSV export from the Ministerio de Sanidad's
  [Nomenclátor de Facturación](https://www.sanidad.gob.es/profesionales/nomenclator.do).
  It includes medicines and financed health products, not just medicines.
- The download URL serves the current release, not a fixed month. Check the
  publication month before and after downloading; never relabel a current
  export as a missing historical month. Localized pages can have stale headings.
- Preserve source bytes and checksum metadata. `sources/archive/` holds archived
  downloads; `data/snapshots/<month>/metadata.json` records snapshot provenance.
- June 2026 was recovered as official XLS through Internet Archive and converted
  deterministically to CSV (trimmed cell edges and mapped legacy headers).
  The same conversion reproduced August's official CSV byte-for-byte. June is
  marked as derived CSV, not preserved original CSV bytes.
- July 2026's official CSV was recovered through Common Crawl. Archives are
  transport providers; the Ministry remains the data authority. Exact filenames,
  hashes, and retrieval details belong in metadata, not this document.

## Rules that matter

- Match presentations by six-digit Código Nacional, stored as text. Preserve
  the official product name; do not guess separate medicine/presentation fields.
- CSV input is UTF-8 with 20 columns, `DD/MM/YYYY` dates, decimal prices, and
  `SI`/`NO` flags. Keep field mappings in code rather than duplicating them here.
- Normalize whitespace and empty cells (`null`), convert dates to ISO format,
  and use exact decimal strings for prices—never floating point.
- Sort and deduplicate active ingredients before comparing. Source ordering
  alone is not a meaningful change. Preserve capitalization and warn on unknown
  flag values instead of guessing.
- Validate before publishing. Parse only the new release when appending;
  preserve existing snapshots and comparisons.

## Missing months and interpretation

October 2026 is unavailable. **September → November 2026 is a one-time
exception**, explicitly enabled with `--allow-gap`; all other gaps remain
blocked. No October snapshot is inferred. The app warns that these are net
differences across two months: their exact month cannot be determined, and
intermediate changes that were reversed cannot be detected.

An addition or removal means presence or absence between the compared exports,
not a clinical or legal conclusion. `Estado` and listing/removal dates remain
independent source fields. These comparisons are not dispensing, reimbursement,
substitution, or treatment advice.
