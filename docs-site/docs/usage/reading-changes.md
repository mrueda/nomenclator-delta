---
sidebar_position: 2
title: Interpreting changes
description: The precise meaning of additions, removals, and changed field values.
---

# Interpreting changes

nomenclator-delta matches records by their six-digit Código Nacional. Each item
on screen is a difference between two monthly source files. It does not explain
the reason for that difference.

## Presence and official status are different concepts

| App term | Exact meaning |
| --- | --- |
| **Alta en la comparación** | The Código Nacional is absent from the earlier export and present in the later export. |
| **Baja en la comparación** | The Código Nacional is present in the earlier export and absent from the later export. |
| **Cambio de estado** | The official `Estado` value changed while the Código Nacional remained present in both exports. |
| **Presentes/Ausentes en el índice más reciente** | Whether the Código Nacional occurs in the latest index. |

In this app, *alta* and *baja* describe whether a Código Nacional occurs in each
file. They do not state the reason for a change and should not be read as a
product recall, legal interpretation, or dispensing guidance.

## Before and after

Each change keeps the values from both months after basic formatting has been
standardized. The left value is from the earlier file; the highlighted right
value is from the later file. **No figuraba** and **No figura** are used only
when a whole presentation is added or removed. **Sin dato** means that the
official cell was blank.

A presentation can have several changes in the same month. For example, its
price and official status may both change. The app lists them separately.

## Price fields

The source contains distinct price concepts. The app retains their official
meaning and labels rather than merging them:

- **Precio de venta al público con IVA**;
- **Precio de referencia**;
- **Menor precio de la agrupación homogénea**.

Values are compared exactly and displayed with a euro symbol. A price change
means only that the values in the two exports differ.

## Active ingredients and other structured fields

The order of active ingredients is ignored because the source does not say that
order has a meaning. Before comparison, the pipeline removes extra spacing and
duplicates and sorts the ingredients. An actual addition, removal, or spelling
change still produces **Cambio de principio activo**.

Laboratory and homogeneous-group code/name pairs are compared as a unit.
Fields that normally contain yes/no values keep their official values. If an
unexpected value appears, the build reports a warning instead of guessing what
it means.

## What to do with a result

Use the presentation history to find and read a source change. Then verify the
current record and any relevant publication at
the [official Nomenclátor](https://www.sanidad.gob.es/profesionales/nomenclator.do).
