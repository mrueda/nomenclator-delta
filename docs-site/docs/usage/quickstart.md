---
sidebar_position: 1
title: Using the app
description: Search and inspect presentation-level changes in the Spanish browser app.
---

# Using the app

The app is in Spanish. Open it at
[mrueda.github.io/nomenclator-delta/app/](https://mrueda.github.io/nomenclator-delta/app/).
At the top of the page, you can see which two months are being compared and how
many presentations are in the later file.

Use the compact period pills—such as **Jun → Jul 2026 (308)**—to change the
comparison. The number in parentheses is the total number of changes found for
that period, including additions and removals. The latest period is selected by
default.

To get back to the starting screen, select **Restablecer**. This returns to the
latest comparison and clears the search, filters, **Cambios/Altas/Bajas** view,
selected presentation, and shared link.

## Search for a presentation

Use the field labelled **Código Nacional, medicamento, principio activo o
laboratorio**. Capital letters and accents do not affect the search. If you
enter several words, every word must occur somewhere in the presentation's
indexed information.

Useful searches include:

- a six-digit Código Nacional, such as `700579`;
- any distinctive part of the official product name;
- one or more active ingredients;
- the offering laboratory name.

The default **Cambios** view shows only presentations with a change in the
selected period. If a search returns more than 100 matches, the app asks you to
make it more specific.

## Refine the results

The top navigation changes the result set:

- **Cambios** shows every presentation with one or more changes;
- **Altas** shows a Código Nacional that is absent from the earlier file and
  present in the later file;
- **Bajas** shows a Código Nacional that is present in the earlier file and
  absent from the later file.

Use **Tipo de cambio** to select one kind of change, such as *Cambio de precio*
or *Cambio de estado*. Use **Situación en el índice más reciente** to distinguish
records that are present from records that are absent in the latest index.

## Inspect the timeline

Select a result to open its details. The panel shows:

1. the Código Nacional and whether it occurs in the later file;
2. the latest available product state;
3. one before-and-after card for every changed field;
4. the period in which each change occurred;
5. source details for both monthly files.

Prices are displayed in euros with Spanish decimal formatting. Blank official
values appear as **Sin dato**. A link with `#cn=NNNNNN` opens the same changed
presentation directly and can be shared.

## Check the source

The **Procedencia** section lists when each file was retrieved and part of its
SHA-256 checksum. Use its Ministerio de Sanidad link to check the current
official information before making an operational decision. The Ministry may
have published a newer release since this site was updated.

The **Comparación disponible** line tells you exactly which months this site
contains. The site is republished after every push to `main` and by a monthly
scheduled run. Neither process fetches a new Ministry release automatically.

Next: [Interpreting changes](reading-changes.md).
