<div align="center">
  <a href="https://mrueda.github.io/nomenclator-delta/">
    <img src="docs-site/static/img/nomenclator-delta-wordmark.svg" width="560" alt="nomenclator-delta">
  </a>
  <p><em>Presentation-level change history for Spain's Nomenclátor</em></p>
  <p>
    <a href="https://github.com/mrueda/nomenclator-delta/actions/workflows/build-and-test.yml"><img src="https://github.com/mrueda/nomenclator-delta/actions/workflows/build-and-test.yml/badge.svg" alt="Build and test"></a>
    <a href="https://github.com/mrueda/nomenclator-delta/actions/workflows/deploy.yml"><img src="https://github.com/mrueda/nomenclator-delta/actions/workflows/deploy.yml/badge.svg" alt="Documentation deployment"></a>
    <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-%E2%89%A53.10-126754" alt="Python 3.10 or newer"></a>
    <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-bc5d2d" alt="MIT License"></a>
  </p>
  <p>
    <a href="https://mrueda.github.io/nomenclator-delta/app/"><strong>Open the app</strong></a>
    ·
    <a href="https://mrueda.github.io/nomenclator-delta/"><strong>Read the documentation</strong></a>
  </p>
</div>

## About

`nomenclator-delta` compares consecutive releases of Spain's *Nomenclátor de
facturación*. It provides a static browser app for finding changes by Código
Nacional, medicine name, active ingredient, or laboratory. There is no backend,
account, tracking service, or patient data.

The pharmacy-facing app is entirely in Spanish and uses official Ministerio de
Sanidad terminology. Source code, data keys, tests, README, and documentation
are in English.

## Quick start

```bash
python3 -m pip install -e ".[test]"
pytest
python3 -m nomenclator_delta validate data
python3 -m nomenclator_delta dist
python3 -m http.server 8000 --directory dist
```

Open `http://localhost:8000`.

To run the complete documentation site with the app embedded at `/app/`:

```bash
cd docs-site
npm ci
npm start
```

## Documentation

The [documentation site](https://mrueda.github.io/nomenclator-delta/) explains
how to use the app and how the data is produced. Maintainers can start with the
[monthly update runbook](docs-site/docs/operations/monthly-update.md).

Detailed observations about the Ministry source files are kept in
[DATA_NOTES.md](DATA_NOTES.md).

## Repository map

```text
src/nomenclator_delta/  collection, normalization, diffing, and validation
data/                    committed deterministic snapshots and change history
site/                    Spanish static application
docs-site/               English documentation and Pages build
tests/                   unit and integration tests
```

## Source and scope

The data authority is the Ministerio de Sanidad's public [Nomenclátor de
facturación](https://www.sanidad.gob.es/profesionales/nomenclator.do).

This independent project is not affiliated with or endorsed by the Ministerio
de Sanidad. It reports differences between source files; it does not provide
dispensing, reimbursement, substitution, prescribing, treatment, or clinical
advice. The official Nomenclátor and related publications remain authoritative.

## License

[MIT](LICENSE) © 2026 Manuel Rueda.
