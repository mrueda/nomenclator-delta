---
sidebar_position: 2
title: Source format
description: Official export assumptions, mutable URLs, and parser boundaries.
---

# Source format

The canonical source is the full CSV export linked from the Ministerio de
Sanidad's [Nomenclátor de
facturación](https://www.sanidad.gob.es/profesionales/nomenclator.do).

## CSV format

The inspected export is UTF-8, uses commas as separators, and contains 20
official columns. In the files examined so far:

- Código Nacional arrives as text and is unique per inspected snapshot;
- dates use `DD/MM/YYYY`;
- decimal prices use a dot separator;
- boolean-like fields use `SI` and `NO`;
- blank cells are common and meaningful;
- medicine-only fields may be blank for financed health-product rows.

The parser requires all known columns, and the build stops if any are missing.
Populated unknown columns are kept in `extra_source_fields` and produce a
warning. This prevents a Ministry format change from passing unnoticed.

The exact ordered header set and the source facts observed during initial
analysis are maintained in
[`DATA_NOTES.md`](https://github.com/mrueda/nomenclator-delta/blob/main/DATA_NOTES.md).
The executable contract lives in `src/nomenclator_delta/schema.py`.

## Why old monthly files are hard to find

The Ministry page links to the current export. When a new month is published,
the same download address returns the new file; it does not continue to serve
the previous one. There is no clear public catalogue of old CSV downloads on
that page. This is why finding June after July was published was not as simple
as changing a month in the URL.

The collector therefore stores each response immediately under:

```text
sources/artifacts/<YYYY-MM>/<sha256>.<extension>
```

The accompanying metadata records the authority, requested URL, UTC retrieval
time, nominal month, original filename, file type, SHA-256 checksum, byte size,
and parser version. Downloading identical bytes again reuses the same path; a
different file gets a different checksum and path.

Raw source files are not committed by default. Keep them in reliable storage
controlled by the maintainer so that a generated release can be reproduced.

## How the June 2026 comparison was built

No preserved copy of the June CSV response was found. This is a consequence of
the current-file download described above, not evidence that a June release did
not exist. Internet Archive preserved two useful items: the Ministry page that
identified the June release and the complete official June XLS file.

The parser input for June was produced from that XLS in a fixed, repeatable way:
cell-edge whitespace was trimmed, three known older header names were mapped to
their current names, and the rows were written using the Ministry's CSV format.

The conversion was checked against August: converting the official August XLS
reproduced the official August CSV byte for byte. Even with that check, the June
source record is explicit about what was recovered. It sets
`exact_original_csv_bytes_preserved: false`, records the original XLS filename
and SHA-256 checksum, and lists Internet Archive only as the transport. The
project does not claim to have preserved the original June CSV bytes.

## Historical transport

When a file is recovered through a web archive, the archive is the transport,
not the data authority. The Ministerio de Sanidad remains the authority.
Archive-specific identifiers are stored in snapshot metadata and included in
generated histories.

## Parser policy

The parser rejects invalid identifiers, missing required headers, malformed
dates, and duplicate CNs. It does not guess the meaning of unfamiliar values:
an unexpected flag value is preserved and reported.
