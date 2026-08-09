---
sidebar_position: 1
title: Monthly update
description: Operator procedure for appending one reviewed Nomenclátor comparison.
---

# Monthly update

New Nomenclátor data is collected and reviewed locally once a month. GitHub
Pages publishes after every push to `main` and also runs on a monthly schedule.
Those deployments use committed data only: they do not look for, download, or
parse a new release.

## 1. Confirm the release

Open the [official Nomenclátor de
facturación](https://www.sanidad.gob.es/profesionales/nomenclator.do) and confirm
the displayed release month. Record any publication notes that will be needed
during review.

The download URL is mutable. Do not assume that a previously copied URL still
returns the same bytes.

## 2. Archive the new response

```bash
python3 -m nomenclator_delta collect \
  --snapshot 2026-09 \
  --source-root sources
```

Review the printed metadata. Keep both the checksum-named source file and its
metadata file in reliable storage controlled by the maintainer. Git ignores raw
source files by default, and they cannot be recovered from the deployed site.

## 3. Build the next transition

Use the committed normalized latest snapshot as the earlier side and the new
artifact as `--to-source`:

```bash
python3 -m nomenclator_delta build \
  --from 2026-08 \
  --to 2026-09 \
  --to-source sources/artifacts/2026-09/<new-sha256>.csv \
  --to-metadata sources/metadata/2026-09/<new-sha256>.json \
  --output data
```

The builder validates the existing dataset, reads its normalized August state,
and parses only the new September file. It then adds the new snapshot,
comparison, changes, and history states. A gap, overlap, or conflicting month
causes the command to fail before it replaces existing history. You may supply
`--from-metadata` to verify the earlier source, but the earlier raw CSV is not
read.

Creating a dataset from scratch is the one case that also requires
`--from-source`; see the [CLI reference](../reference/cli.md#build).

## 4. Validate and review

```bash
python3 -m nomenclator_delta validate data
pytest
```

Inspect `data/build-report.json` and the new transition file. At minimum, review:

- input and normalized record counts;
- additions, removals, changed presentations, and event types;
- all warnings and any unexpected new fields;
- source hashes and filenames for both endpoints;
- representative price, status, ingredient, and presence changes in the app.

Large movements can be legitimate, but investigate and explain them before
changing a validation threshold.

## 5. Build the complete site

```bash
cd docs-site
npm ci
npm run typecheck
npm run build
```

Before Docusaurus builds the documentation, `prebuild` packages the Spanish app
and committed JSON in `static/app/`. Serve `build/` over HTTP and test the new
month labels, summary counts, searches, histories, source links, and mobile
layout.

## 6. Commit and publish

Commit the reviewed generated changes on `main`, together with any required
parser, schema, test, or documentation updates. Pushing `main` runs CI and
publishes the site immediately. The monthly scheduled deployment republishes
the same committed files. Both validate the repository again, but neither
collects a source file nor rebuilds old comparisons.

If a reviewed dataset must be withdrawn, revert the data-producing commit and
let Pages publish the previous valid commit. Do not manually edit generated
events or histories.
