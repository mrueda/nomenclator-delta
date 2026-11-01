---
sidebar_position: 4
title: Troubleshooting
description: Resolve common search, freshness, and loading questions.
---

# Troubleshooting

## A known product does not appear

The default result list shows presentations with a change in the selected
period. It does not show every current product. Check that:

1. the Código Nacional has six digits;
2. the search has no extra restrictive terms;
3. **Tipo de cambio** is set as intended;
4. the selected **Cambios**, **Altas**, or **Bajas** view matches the question.

If the presentation exists but did not change between the two monthly files,
it is in the search index but does not appear in a change view.

## “No se pudieron cargar los datos” appears

The app could not fetch its static JSON. Reload the page first. If you are
running the repository locally, serve the built directory over HTTP; opening
`site/index.html` directly with a `file://` URL prevents normal browser fetches.

```bash
python3 -m nomenclator_delta dist
python3 -m http.server 8000 --directory dist
```

Then open `http://localhost:8000`.

## The official page shows a newer month

This can happen between an official release and the next maintained data
update. Check the app's **Comparación disponible** line for the months it
contains. Automatic collection runs on the 1st, 5th, and 10th. If a release is
still missing, check Actions for download errors, validation failures, or a
missing intervening month that needs recovery.

## A value differs from another system

Open the result's **Procedencia** section and note both months and SHA-256
prefixes. Compare the same field and Código Nacional in the corresponding
official release. A difference may be due to release timing, a different
official field, or newer source data rather than a parsing error.

When opening a
[GitHub issue](https://github.com/mrueda/nomenclator-delta/issues), include the
Código Nacional, compared months, field label, before and after values, and
source checksum. This gives the maintainer enough information to reproduce the
result.
