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

Use **Periodo comparado** to choose a comparison. The dropdown lists the newest
period first, selected by default and marked **Último disponible**. Below it,
the app shows the latest publication available in its dataset, the selected
period's counts, and any missing-month warning. The latest available publication
does not imply that a newer Ministry release has already been collected.

The app normally compares consecutive monthly releases. October 2026 is the
one-time exception: September is compared directly with November. A short
warning identifies the gap; **Más información** explains why these accumulated
differences cannot be assigned to either month individually.

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
selected period. The compared months also appear above the results. The app
initially shows up to 100 matches; **Mostrar más** reveals the next 100 until
all matches are visible. Changing the search, filter, view, or period resets
the list to the first 100. Selecting a presentation keeps the expanded list.

## Refine the results

The top navigation changes the result set:

- **Cambios** shows every presentation with one or more changes;
- **Altas** shows a Código Nacional that is absent from the earlier file and
  present in the later file;
- **Bajas** shows a Código Nacional that is present in the earlier file and
  absent from the later file.

Use **Tipo de cambio** to select one kind of change, such as *Cambio de precio*
or *Cambio de estado*.

## Download the filtered results

Select **Descargar CSV** to download all matching presentations, including those
beyond the first 100 shown on screen. The file follows the current search,
view, and change-type filter; the button is disabled when there are no matches.

The UTF-8, semicolon-separated file contains one row per presentation, with
Código Nacional, name and laboratory from the latest search index, the two
compared months, change labels, and any missing-month warning. It is a summary,
not a full export of before-and-after values. Names and laboratories may be newer
than a historical comparison; use the detail panel to inspect historical values.

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
contains. Automatic checks on the 1st, 5th, and 10th look for a new Ministry
release. A release appears only after collection and validation succeed.

Next: [Interpreting changes](reading-changes.md).
