---
sidebar_position: 1
title: Overview
description: What nomenclator-delta does, where its data comes from, and what it does not claim.
---

import Link from '@docusaurus/Link';

# What nomenclator-delta does

The *Nomenclátor de Facturación* is the Ministerio de Sanidad's database of
medicines and health products included in the *prestación farmacéutica*
(pharmaceutical benefit) of the Sistema Nacional de Salud (SNS) and dispensed
through community pharmacies (*oficinas de farmacia*). The Ministry publishes a
new file each month.

**nomenclator-delta** compares available releases to answer one question:
**what changed for this Código Nacional from one published month to the next?**

<div className="button-row">
  <Link className="button button--primary" to="pathname:///app/">Open the Spanish app</Link>
  <Link className="button button--secondary" to="/docs/usage/quickstart">Read the user guide</Link>
</div>

## What you can do

- Search by Código Nacional, official product name, active ingredient, or
  offering laboratory.
- See presentations that appear in one monthly file but not the other.
- Review changes to prices, status, dates, laboratory, active ingredients,
  contribution, homogeneous groups, and selected flags.
- Compare the earlier and later values and check the source details for each
  month.
- Use the static website without an account. It has no backend, analytics
  service, or patient data.

The browser app is in Spanish and preserves familiar Ministerio de Sanidad
terminology. The documentation and developer-facing interfaces are in English.

## Where the data comes from

The data authority is the [Ministerio de Sanidad's Nomenclátor de
facturación](https://www.sanidad.gob.es/profesionales/nomenclator.do). For each
retained source file, the project records the release month, retrieval time,
original filename, size, file type, parser version, and SHA-256 checksum. These
details make it possible to identify the exact file used in a comparison.

The Ministry's download link serves the current export; it is not a catalogue
of old monthly files. The maintainer therefore archives each source file before
processing it. The public site uses only reviewed, validated data committed to
this repository.

:::important Independent information service

nomenclator-delta reorganizes and compares public official data. It is not
affiliated with or endorsed by the Ministerio de Sanidad. The official
Nomenclátor and official publications remain authoritative.

:::

## Scope

The project reports differences found in the source files. It cannot say why a
value changed. It does not recommend dispensing, reimbursement, substitution,
prescribing, treatment, or clinical action. An addition or removal means only
that a Código Nacional is present in one compared file and absent from the
other.

Continue with [Using the app](usage/quickstart.md), or read the
[architecture](technical-details/architecture.md) if you maintain the project.
