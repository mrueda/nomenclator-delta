import gzip
import hashlib
import json
from pathlib import Path

import pytest

from nomenclator_delta.build import build_comparison
from nomenclator_delta import update as updater
from nomenclator_delta.validate import validate_dataset

FIXTURES = Path(__file__).parent / 'fixtures'


@pytest.mark.parametrize('heading,expected', [
    ('<h2>Nomenclátor de Facturación de SEPTIEMBRE-2026</h2>', '2026-09'),
    ('Nomencl&aacute;tor de Facturaci&oacute;n de NOVIEMBRE -2026', '2026-11'),
])
def test_publication_month(heading, expected):
    assert updater.release_month(heading) == expected


def test_unrecognized_month_rejected():
    with pytest.raises(ValueError):
        updater.release_month('Error: servicio no disponible')


def setup_source(tmp_path, monkeypatch, month):
    data = tmp_path / 'data'
    build_comparison(FIXTURES / '2026-07.csv', FIXTURES / '2026-08.csv', '2026-07', '2026-08', data, minimum_records=1)
    monkeypatch.setattr(updater, 'fetch_page', lambda: f'Nomenclátor de Facturación de {month} -2026')
    def collect(snapshot, root, url):
        raw = FIXTURES / '2026-09.csv'
        return dict(artifact=str(raw), snapshot=snapshot, sha256=hashlib.sha256(raw.read_bytes()).hexdigest(), file_size=raw.stat().st_size, mime_type='text/csv')
    monkeypatch.setattr(updater, 'collect_snapshot', collect)
    return data, tmp_path / 'archive'


def digest(data):
    return {str(p.relative_to(data)): p.read_bytes() for p in data.rglob('*') if p.is_file()}


def test_update_archives_exact_bytes_and_is_idempotent(tmp_path, monkeypatch):
    data, archive = setup_source(tmp_path, monkeypatch, 'SEPTIEMBRE')
    old = (data / 'snapshots/2026-08/products.json').read_bytes()
    assert updater.update(data, archive, minimum_records=1)['status'] == 'updated'
    assert validate_dataset(data) == []
    assert (data / 'snapshots/2026-08/products.json').read_bytes() == old
    assert gzip.decompress(next(archive.rglob('*.gz')).read_bytes()) == (FIXTURES / '2026-09.csv').read_bytes()
    assert not any('artifact' in json.loads(p.read_text()) for p in archive.rglob('*.json'))
    before = digest(data)
    monkeypatch.setattr(updater, 'collect_snapshot', lambda *a: pytest.fail('Must not download an existing month'))
    assert updater.update(data, archive)['status'] == 'unchanged'
    assert digest(data) == before


def test_gap_archives_without_modifying_history(tmp_path, monkeypatch):
    data, archive = setup_source(tmp_path, monkeypatch, 'OCTUBRE')
    before = digest(data)
    assert updater.update(data, archive)['status'] == 'gap'
    archived = digest(archive)
    assert updater.update(data, archive)['status'] == 'gap'
    assert digest(archive) == archived
    assert digest(data) == before


def test_month_rollover_aborts(tmp_path, monkeypatch):
    data, archive = setup_source(tmp_path, monkeypatch, 'SEPTIEMBRE')
    pages = iter(['Nomenclátor de Facturación de SEPTIEMBRE-2026', 'Nomenclátor de Facturación de OCTUBRE-2026'])
    monkeypatch.setattr(updater, 'fetch_page', lambda: next(pages))
    before = digest(data)
    with pytest.raises(ValueError, match='changed during download'):
        updater.update(data, archive)
    assert digest(data) == before
    assert not archive.exists()


def test_invalid_export_does_not_replace_dataset(tmp_path, monkeypatch):
    data, archive = setup_source(tmp_path, monkeypatch, 'SEPTIEMBRE')
    before = digest(data)
    with pytest.raises(ValueError, match='suspicious product count'):
        updater.update(data, archive)
    assert digest(data) == before
