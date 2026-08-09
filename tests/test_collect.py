import hashlib
from pathlib import Path

from requests.structures import CaseInsensitiveDict

from nomenclator_delta.collect import collect_snapshot


class FakeResponse:
    def __init__(self, payload: bytes, filename: str):
        self.payload = payload
        self.headers = CaseInsensitiveDict(
            {
                "Content-Type": "text/csv; charset=UTF-8",
                "Content-Disposition": f'attachment; filename="{filename}"',
            }
        )

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def raise_for_status(self):
        return None

    def iter_content(self, chunk_size):
        yield self.payload


def test_collector_content_addresses_republished_source(monkeypatch, tmp_path):
    payloads = [b"first official export\n", b"corrected official export\n"]

    def fake_get(*args, **kwargs):
        payload = payloads.pop(0)
        return FakeResponse(payload, "Nomenclator.csv")

    monkeypatch.setattr("nomenclator_delta.collect.requests.get", fake_get)
    first = collect_snapshot("2026-08", tmp_path, "https://example.test/official.csv")
    second = collect_snapshot("2026-08", tmp_path, "https://example.test/official.csv")

    assert first["sha256"] != second["sha256"]
    artifacts = sorted((tmp_path / "artifacts" / "2026-08").glob("*.csv"))
    assert len(artifacts) == 2
    assert {path.stem for path in artifacts} == {first["sha256"], second["sha256"]}
    assert first["sha256"] == hashlib.sha256(b"first official export\n").hexdigest()
