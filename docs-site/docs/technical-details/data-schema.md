---
sidebar_position: 4
title: Data schema
description: Static JSON contracts for snapshots, transitions, indexes, and product histories.
---

# Data schema

The browser app reads generated JSON files. Their keys are in English and the
current format is marked `schema_version: 1`. Records and keys are written in a
stable order, so the same input produces the same files.

## Normalized product

```json
{
  "codigo_nacional": "700579",
  "medicine_name": "SINEMET PLUS 25 mg/100 mg COMPRIMIDOS , 100 comprimidos",
  "drug_type": "Medicamento Etica",
  "generic_product_name": null,
  "laboratory": {"code": "884", "name": "ORGANON SALUD, S.L."},
  "status": "ALTA",
  "listed_from": "2016-07-01",
  "listed_until": null,
  "contribution": "ESPECIAL",
  "active_ingredients": ["CARBIDOPA MONOHIDRATO", "LEVODOPA"],
  "prices": {
    "retail_with_vat": "10.12",
    "reference": "10.12",
    "homogeneous_group_minimum": "11.26"
  },
  "homogeneous_group": {
    "code": "3283",
    "name": "LEVODOPA/CARBIDOPA 100MG/25MG 100 COMPRIMIDOS"
  },
  "flags": {
    "hospital_diagnosis": false,
    "long_term_treatment": true,
    "special_medical_control": false,
    "orphan_medicine": false
  },
  "source_snapshot": "2026-08",
  "source_row": 11299
}
```

`source_row` is the one-based CSV record position including the header offset.
This example is taken from the bundled August 2026 normalized snapshot.

## Change event

```json
{
  "id": "2026-07_to_2026-08:700579:PRICE_CHANGED:0",
  "cn": "700579",
  "from_snapshot": "2026-07",
  "to_snapshot": "2026-08",
  "change_type": "PRICE_CHANGED",
  "change_label_es": "Cambio de precio",
  "field": "prices.retail_with_vat",
  "field_label_es": "Precio de venta al público con IVA",
  "before": "11.26",
  "after": "10.12",
  "source": {
    "authority": "Ministerio de Sanidad",
    "official_source_url": "https://www.sanidad.gob.es/profesionales/nomenclator.do",
    "from_snapshot": "2026-07",
    "to_snapshot": "2026-08"
  }
}
```

## Generated layout

```text
data/
  metadata.json
  build-report.json
  snapshots/<YYYY-MM>/{metadata.json,products.json}
  changes/<from>_to_<to>.json
  products/<CN>.json
  indexes/products.json
  indexes/changes-by-month.json
```

`metadata.json` is the first file the application reads. It lists the available
months and comparisons, identifies the latest month, and includes counts,
source authority, and the Spanish disclaimer.

The product index contains every known CN and enough information for browser
search. It also records whether each CN is present in each month. A product
history contains its monthly states, all changes for that CN, and the source
details for the months involved.

`changes-by-month.json` contains transition summaries. Each transition file
contains its summary plus the complete event list for that pair.

## Presentation histories

A link ending in `#cn=<CN>` opens a changed presentation directly. Each new
monthly comparison adds to its history. An unchanged search result uses the
compact index record and is labelled as having no change in the selected
period.
