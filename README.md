<div align="center">
  <h1>nomenclator-delta</h1>
  <p><em>Historiales de cambios del Nomenclátor, presentación por presentación</em></p>
</div>

# nomenclator-delta

`nomenclator-delta` turns monthly Spanish Nomenclátor releases into searchable,
presentation-level change histories.

It downloads and preserves official Ministerio de Sanidad exports, normalizes
them by Código Nacional, creates semantic differences between consecutive
months, and publishes a Spanish-language static search app. No backend,
database, account, or tracking service is required.

The first bundled comparison is **July 2026 → August 2026**:

- 20,521 presentations in July.
- 20,559 presentations in August.
- 75 additions.
- 37 removals.
- 187 existing presentations with material changes.
- 131 changed price fields.

All counts are generated from the committed data. They are not hard-coded into
the website.

## What it answers

The app is designed around one question:

> What changed for this medicine in the Nomenclátor?

Users can search by Código Nacional, medicine name, active ingredient, or
laboratory; filter by change type; inspect additions and removals; and open a
presentation timeline showing the official before and after values.

The public interface is entirely in Spanish and uses Ministerio de Sanidad
terminology. Source code, JSON keys, tests, and developer documentation remain
in English.

## Official data source

The authoritative input is the Ministerio de Sanidad's public
[Nomenclátor de facturación](https://www.sanidad.gob.es/profesionales/nomenclator.do).
The full CSV export has 20 columns and uses Código Nacional as a unique
presentation identifier in both inspected releases.

The Ministry download URL is mutable: the same URL returns the current monthly
artifact. Collection therefore stores immutable, content-addressed files and
records the source URL, retrieval time, nominal month, original filename, MIME
type, SHA-256 digest, size, and parser version.

The July artifact was preserved from the official `sanidad.gob.es` response by
Common Crawl. Common Crawl is recorded as archive transport; the Ministerio de
Sanidad remains the data authority. The August artifact was retrieved directly
from the live official endpoint.

See [DATA_NOTES.md](DATA_NOTES.md) for the exact columns, observed source
quirks, normalization rules, provenance details, and exploratory diff.

## Quick start

Install from the repository root:

```bash
python3 -m pip install -e ".[test]"
```

Validate the committed static data and run the tests:

```bash
pytest
python3 -m nomenclator_delta validate data
```

Build and serve the deployable site:

```bash
python3 -m nomenclator_delta dist
python3 -m http.server 8000 --directory dist
```

Then open `http://localhost:8000`.

## Local monthly data workflow

Data production is intentionally separate from daily site deployment. Heavy
source work happens locally or in an explicit operator run, not during every
GitHub Pages deployment.

Archive the current official export, supplying its nominal Nomenclátor month:

```bash
python3 -m nomenclator_delta collect \
  --snapshot 2026-09 \
  --source-root sources
```

The collector prints and writes provenance metadata and stores the bytes under
`sources/artifacts/<month>/<sha256>.csv`. Raw artifacts are ignored by Git by
default; operators should retain them in durable local or external storage.

Build a consecutive comparison from the two retained official artifacts:

```bash
python3 -m nomenclator_delta build \
  --from 2026-08 \
  --to 2026-09 \
  --from-source sources/artifacts/2026-08/<sha256>.csv \
  --to-source sources/artifacts/2026-09/<sha256>.csv \
  --from-metadata sources/metadata/2026-08/<sha256>.json \
  --to-metadata sources/metadata/2026-09/<sha256>.json \
  --output data

python3 -m nomenclator_delta validate data
python3 -m nomenclator_delta dist
```

Phase 1 builds one consecutive transition. The next pipeline step will append a
new normalized snapshot and compare it only with the previous normalized month,
without reparsing the full retained history.

## CLI

```text
nomenclator-delta collect   Archive the current official CSV
nomenclator-delta build     Parse and compare two consecutive snapshots
nomenclator-delta validate  Validate generated data and references
nomenclator-delta dist      Package site/ and data/ for static hosting
```

All generated JSON is deterministic for identical source artifacts and software
versions. Collection timestamps live in provenance metadata, not in derived
content.

## Normalized schema

Each CN-level record contains:

```text
codigo_nacional
medicine_name
drug_type
generic_product_name
laboratory { code, name }
status
listed_from / listed_until
contribution
active_ingredients[]
prices { retail_with_vat, reference, homogeneous_group_minimum }
homogeneous_group { code, name }
flags { hospital_diagnosis, long_term_treatment,
        special_medical_control, orphan_medicine }
source_snapshot
source_row
```

Names are kept as the official `Nombre del producto farmacéutico`; the pipeline
does not heuristically split a presentation that the source does not split.
Prices remain exact decimal strings.

## Semantic differences and noise suppression

The pipeline emits explicit event types such as `PRODUCT_ADDED`,
`PRODUCT_REMOVED`, `PRICE_CHANGED`, `STATUS_CHANGED`, `LABORATORY_CHANGED`, and
`ACTIVE_INGREDIENT_CHANGED`. Each event includes the CN, transition, field,
before value, after value, Spanish display labels, and source references.

Normalization collapses whitespace, standardizes blank values, converts dates
to ISO form, and compares prices as exact decimals. Active-ingredient order is
treated as non-semantic. This last rule suppresses 966 false ingredient changes
in the first real comparison while preserving two genuine changes.

No fuzzy matching or inferred identity is used. Código Nacional drives the
timeline.

## Generated data

```text
data/
  metadata.json
  build-report.json
  snapshots/
    2026-07/{metadata.json,products.json}
    2026-08/{metadata.json,products.json}
  changes/
    2026-07_to_2026-08.json
  products/
    <CN>.json
  indexes/
    products.json
    changes-by-month.json
```

The product search index contains every CN found in either snapshot. Individual
history files are generated only for presentations with at least one event,
avoiding roughly 20,000 unnecessary static files for unchanged presentations.

## Validation

Publishing fails on missing critical columns, invalid or duplicate CN values,
invalid dates or prices, suspiciously small snapshots, catastrophic count
changes, metadata count mismatches, broken snapshot references, equal
before/after event values, duplicate event IDs, missing histories, or
non-chronological timelines.

Unknown source columns and unexpected flag values are preserved where possible
and reported as warnings. Source schema changes cannot pass unnoticed.

## Deployment

The Pages workflow runs daily and on `main` updates. It performs only three
operations:

1. validate the already committed generated data;
2. copy `site/` and `data/` into `dist/`;
3. deploy that static directory to GitHub Pages.

It does **not** collect a release, parse old artifacts, or rebuild historical
comparisons. Monthly data updates are deliberate local/operator work and enter
the deployment through reviewed generated-data changes.

## Scope and disclaimer

`nomenclator-delta` is informational and source-driven. It does not recommend
dispensing, reimbursement, substitution, treatment, or clinical actions; it
does not interpret prescriptions; and it does not process patient information.

It is an independent open-source project that reorganizes and compares publicly
available official data. It is not affiliated with or endorsed by the
Ministerio de Sanidad. The official Nomenclátor and official publications remain
authoritative.

## License

MIT. See [LICENSE](LICENSE).
