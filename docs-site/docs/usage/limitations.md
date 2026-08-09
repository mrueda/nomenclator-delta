---
sidebar_position: 3
title: Limitations and safety
description: Known limits, independence, and appropriate use of the comparison.
---

# Limitations and safety

The app shows what differs between source files. It does not interpret the
clinical or regulatory meaning of a change.

## Known limits

- The official public download exposes the current export. It does not provide
  a clear catalogue of older monthly files.
- The nominal month is supplied by the operator and checked during collection;
  it is not encoded in the mutable download URL.
- Records are matched only by Código Nacional. The pipeline does not guess that
  two different identifiers belong to the same presentation.
- The official product name is preserved as one field. The source does not
  provide a separate structured presentation field, so the project does not
  invent one by parsing the name.
- A change in capitalization alone is reported as a change.
- Only the comparisons listed in the app are available. The Ministry may have
  published a new release that the maintainer has not processed yet.

## Appropriate use

nomenclator-delta can help a pharmacy professional find differences between two
published files and check their source. It cannot determine the reason for a
change or its legal, reimbursement, stock, substitution, safety, or treatment
consequences.

:::warning Verify current official information

Do not use the app as the sole basis for dispensing, reimbursement,
substitution, prescribing, treatment, or clinical decisions. Consult the
current official Nomenclátor and the relevant official publications.

:::

The project does not process patient information, provide accounts, or send
searches to an application backend.
