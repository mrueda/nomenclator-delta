---
sidebar_position: 3
title: Normalization and semantic diffs
description: Deterministic normalization rules and the event taxonomy.
---

# Normalization and semantic diffs

Before comparing files, the pipeline standardizes formatting that should not
count as a real change. This step is called normalization. It keeps the official
meaning and ensures that the same source file and parser version produce the
same JSON.

## Normalization rules

- Strip leading and trailing whitespace and collapse repeated whitespace.
- Convert empty strings to JSON `null`.
- Require a six-digit numeric Código Nacional; never invent an identifier.
- Convert dates to ISO `YYYY-MM-DD`.
- Parse prices with `Decimal`, then store exact canonical decimal strings.
- Convert known `SI`/`NO` flags to booleans and preserve unknown non-empty
  values with a warning.
- Split active ingredients on commas, trim and deduplicate them, then sort them
  for comparison.
- Preserve capitalization, including case-only changes.

Names remain the official `Nombre del producto farmacéutico`. The source does
not provide strength, form, package size, or presentation as separate columns,
so the pipeline does not try to extract them from the name.

## Why active-ingredient order is ignored

The source does not say that ingredient order is meaningful. Reporting a
reordered list would create many changes where the ingredients themselves are
unchanged. Lists with the same ingredients therefore compare as equal, while
an actual addition, removal, or text change remains visible.

## Event taxonomy

Each difference becomes a separate change event. It has a stable developer
type and a Spanish label for the app. Current types are:

| Category | Event types |
| --- | --- |
| Presence | `PRODUCT_ADDED`, `PRODUCT_REMOVED` |
| Identity text | `NAME_CHANGED`, `PRODUCT_TYPE_CHANGED`, `GENERIC_NAME_CHANGED` |
| Commercial/source state | `LABORATORY_CHANGED`, `STATUS_CHANGED`, `CONTRIBUTION_CHANGED` |
| Dates | `LISTING_DATE_CHANGED`, `REMOVAL_DATE_CHANGED` |
| Composition | `ACTIVE_INGREDIENT_CHANGED` |
| Price | `PRICE_CHANGED` for each distinct official price field |
| Grouping | `HOMOGENEOUS_GROUP_CHANGED` |
| Flags | hospital diagnosis, long-term treatment, special control, and orphan-status changes |

An event records the CN, the two months, the field, its exact before and after
values, the developer type, Spanish app labels, and a source reference. If
several fields change for one CN, each is recorded separately.

## What the comparison does not do

The pipeline does not use approximate name matching, interpret free text, assign
clinical categories, or infer why something changed. A removed CN and an added
CN remain two separate presence changes even if their names look similar.
