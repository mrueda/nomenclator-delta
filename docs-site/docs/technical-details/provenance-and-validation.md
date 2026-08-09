---
sidebar_position: 5
title: Provenance and validation
description: Evidence records, integrity checks, and publishing gates.
---

# Provenance and validation

Here, *provenance* means the information needed to identify the source of a
generated record. It is stored with the data, not added later as a note. Every
monthly snapshot identifies the exact input file and parser version used to
build it.

## Snapshot evidence

Snapshot metadata includes:

<div className="schemaGrid">
  <div className="schemaPill"><strong>Authority</strong>Ministerio de Sanidad</div>
  <div className="schemaPill"><strong>Identity</strong>Nominal month and original filename</div>
  <div className="schemaPill"><strong>Integrity</strong>SHA-256 and byte size</div>
  <div className="schemaPill"><strong>Retrieval</strong>Source URL and UTC timestamp</div>
  <div className="schemaPill"><strong>Processing</strong>Parser and schema versions</div>
  <div className="schemaPill"><strong>Transport</strong>Archive details when applicable</div>
</div>

When source metadata is supplied to a build, its month, checksum, and byte size
must match the actual file. The local `artifact` path is left out of public JSON
because it is meaningful only on the maintainer's computer.

## Build guardrails

Before diffing, the builder rejects:

- missing critical source columns;
- invalid or duplicate Código Nacional values;
- malformed dates or decimal prices;
- snapshots below the configured minimum record count;
- a product-count change above the catastrophic-change threshold;
- supplied metadata that does not match the input bytes;
- a non-consecutive or conflicting append to an existing dataset.

Unknown source columns and unexpected flag values produce warnings. This makes
a source-format change visible instead of silently ignoring it.

## Dataset validation

`nomenclator-delta validate` checks the complete generated dataset without
opening the raw source files. It verifies, among other things:

- valid, ordered snapshot and transition identifiers;
- snapshot metadata counts and CN uniqueness;
- product-index membership across snapshots;
- transition summary/event count agreement;
- event-type counts, unique IDs, and unequal before/after values;
- event references to the correct transition endpoints;
- existence and chronology of presentation histories;
- agreement between transition events and each product history.

Any validation error makes the command fail. CI runs the same check before
packaging the app and before deploying to Pages.

## Review boundary

Passing validation means that the generated files agree with one another. It
does not prove that a result is clinically or legally correct. For every monthly
update, a maintainer still reviews the source details, warnings, summary counts,
and a sample of changes against the official release.
