---
sidebar_position: 1
title: Architecture
description: Incremental monthly collection and static application deployment.
---

# How the project is organized

GitHub Actions collects new monthly releases and publishes the static app and
documentation through GitHub Pages. Maintainers can also run collection and
comparison locally, including recovery of missing historical releases.

<div className="dataFlow" aria-label="Data flow">
  <span>Official CSV</span>
  <span>Artifact archive</span>
  <span>Normalize</span>
  <span>Semantic diff</span>
  <span>Static JSON</span>
  <span>Browser app</span>
</div>

## Components

| Component | What it does |
| --- | --- |
| `collect.py` | Download the current official response and store it by checksum, together with its source details. |
| `update.py` | Check the official publication month, archive new source bytes, and append only consecutive releases. |
| `parse.py` / `normalize.py` | Enforce the known source contract and produce stable CN-level records. |
| `diff.py` | Compare consecutive months and create one event for each meaningful change. |
| `build.py` | Write snapshots, transitions, indexes, histories, metadata, and a build report. |
| `validate.py` | Check referential integrity, counts, chronology, identifiers, and event invariants. |
| `site/` | Load static JSON and provide the Spanish search interface. |
| `docs-site/` | Build the documentation and embed the packaged app at `/app/`. |

The Python package has one runtime dependency, `requests`, used only for
collection. Parsing, normalization, diffing, validation, and packaging use the
standard library.

## Producing data and publishing it

### Monthly data production

Scheduled or manual collection archives the new official export and compares
it with the latest normalized snapshot. Validation and the site build must
pass before the workflow commits the result. When adding a month, the pipeline parses
only the new raw file; it does not parse the full history again.

### Publishing the site

CI validates committed JSON, packages `site/` with `data/`, builds Docusaurus,
and deploys the static output after every push to `main`. Runs on the 1st,
5th, and 10th first check for a new release; manual runs can do so too. Raw
exports are compressed and committed under `sources/archive/`. Missing months
stop publication rather than producing a comparison across a gap.

## What the browser loads

There is no API server. The app fetches:

- project metadata and transition summaries;
- a compact search index spanning known presentations;
- the selected transition's events;
- a presentation history only when needed.

There is no application server between the browser and these files. Searches
stay in the browser and are not tied to an account or patient.

## Identity and chronology

Products are matched only by Código Nacional. Comparisons must join consecutive
months, must not conflict with existing snapshot data, and are ordered by
`YYYY-MM`. The pipeline does not guess that different identifiers describe the
same product, even when their names are similar.

See [Normalization and semantic diffs](normalization-and-diffs.md) for field
rules and [Monthly update](../operations/monthly-update.md) for the operator
workflow.
