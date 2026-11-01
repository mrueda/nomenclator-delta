---
sidebar_position: 1
title: CLI reference
description: Command-line interface for collection, comparison, validation, and static packaging.
---

# CLI reference

Install the package from the repository root:

```bash
python3 -m pip install -e .
```

The `nomenclator-delta` console script and `python3 -m nomenclator_delta` expose
the same commands.

## `collect`

Download and content-address the current official export.

```bash
nomenclator-delta collect \
  --snapshot 2026-09 \
  --source-root sources
```

| Option | Required | Default | Meaning |
| --- | --- | --- | --- |
| `--snapshot YYYY-MM` | yes | — | Operator-verified nominal release month. |
| `--source-root PATH` | no | `sources` | Root for artifacts and metadata sidecars. |
| `--url URL` | no | official full CSV endpoint | Override the collection endpoint. |

The command prints the source metadata as JSON. It writes the downloaded file
below `artifacts/<snapshot>/` and the accompanying metadata below
`metadata/<snapshot>/`. Both filenames contain the response's SHA-256 checksum.

Collection does not build or publish data. Before continuing, verify the
filename, content type, checksum, size, and release month.

## `build`

Compare one new source file with the latest validated snapshot and append the
result.

```bash
nomenclator-delta build \
  --from 2026-08 \
  --to 2026-09 \
  --to-source sources/artifacts/2026-09/<sha256>.csv \
  --to-metadata sources/metadata/2026-09/<sha256>.json \
  --output data
```

| Option | Required | Default | Meaning |
| --- | --- | --- | --- |
| `--from YYYY-MM` | yes | — | Earlier snapshot. |
| `--to YYYY-MM` | yes | — | Later snapshot. |
| `--from-source PATH` | first build only | — | Earlier official artifact; omitted when appending. |
| `--to-source PATH` | yes | — | Later official artifact. |
| `--from-metadata PATH` | no | generated from artifact | Earlier provenance sidecar. |
| `--to-metadata PATH` | no | generated from artifact | Later provenance sidecar. |
| `--output PATH` | no | `data` | Generated static data root. |
| `--minimum-records N` | no | `15000` | Sanity threshold per source snapshot. |
| `--allow-gap` | no | off | One-time September → November 2026 exception only. All other gaps are rejected. |

In an empty output directory, `build` creates the first comparison and needs
both raw source files. In an existing dataset, the new month must follow the
latest month. Omit `--from-source`: the latest validated normalized snapshot is
used as the earlier input. Existing snapshots, changes, and histories are kept,
and only the new raw file is parsed.

## `validate`

Check a generated dataset without reading raw source artifacts.

```bash
nomenclator-delta validate data
```

The path defaults to `data`. Every validation error is written to standard
error and the process exits non-zero. Success prints `Validated <path>`.

## `dist`

Create a deployable application directory.

```bash
nomenclator-delta dist \
  --site site \
  --data data \
  --output dist
```

| Option | Default | Meaning |
| --- | --- | --- |
| `--site PATH` | `site` | Static application source. |
| `--data PATH` | `data` | Validated generated JSON. |
| `--output PATH` | `dist` | Destination to replace with the packaged app. |

The command copies the app and data. It does not parse or validate them. For
safety, the output path cannot be `/` or the current working directory.
