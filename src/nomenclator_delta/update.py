"""Collect one new official release without relabelling or rewriting history."""
from __future__ import annotations

import argparse
import gzip
import html
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import requests

from nomenclator_delta.build import LANDING_PAGE_URL, build_comparison, write_json
from nomenclator_delta.cli import DEFAULT_CSV_URL
from nomenclator_delta.collect import collect_snapshot
from nomenclator_delta.validate import validate_dataset

MONTHS = "ENERO FEBRERO MARZO ABRIL MAYO JUNIO JULIO AGOSTO SEPTIEMBRE OCTUBRE NOVIEMBRE DICIEMBRE".split()


def release_month(page: str) -> str:
    text = html.unescape(re.sub(r"<[^>]+>", " ", page)).upper()
    matches = re.findall(r"NOMENCL[ÁA]TOR\s+DE\s+FACTURACI[ÓO]N\s+DE\s+([A-Z]+)\s*-?\s*(20\d{2})", text)
    months = {f"{year}-{MONTHS.index(month) + 1:02d}" for month, year in matches if month in MONTHS}
    if len(months) != 1:
        raise ValueError("Cannot identify one official publication month")
    return months.pop()


def fetch_page() -> str:
    response = requests.get(LANDING_PAGE_URL, timeout=60)
    response.raise_for_status()
    response.encoding = "utf-8"
    return response.text


def update(data: Path, archive: Path, *, minimum_records: int = 15_000) -> dict:
    errors = validate_dataset(data)
    if errors:
        raise ValueError("Invalid existing dataset: " + "; ".join(errors))
    latest = json.loads((data / "metadata.json").read_text())["latest_snapshot"]
    page = fetch_page()
    published = release_month(page)
    if published > datetime.now(timezone.utc).strftime("%Y-%m"):
        raise ValueError(f"Unexpected future publication: {published}")
    if published <= latest:
        return {"status": "unchanged", "message": f"No new month: published {published}, stored {latest}"}
    with tempfile.TemporaryDirectory(prefix="nomenclator-update-") as temporary:
        source = collect_snapshot(published, Path(temporary), DEFAULT_CSV_URL)
        # Check again after downloading: the mutable endpoint may roll over mid-run.
        if release_month(fetch_page()) != published:
            raise ValueError("Publication month changed during download; retry later")
        if source["mime_type"] not in {"text/csv", "application/csv"}:
            raise ValueError(f"Unexpected export type: {source['mime_type']}")
        raw = Path(source.pop("artifact"))
        target = archive / published / source["sha256"]
        compressed = target.with_suffix(".csv.gz")
        metadata = target.with_suffix(".json")
        compressed.parent.mkdir(parents=True, exist_ok=True)
        if not compressed.exists():
            compressed.write_bytes(gzip.compress(raw.read_bytes(), mtime=0))
        if not metadata.exists():
            write_json(metadata, source)
            target.with_suffix(".html").write_text(page, encoding="utf-8")
        year, month = map(int, latest.split("-"))
        expected = f"{year + (month == 12):04d}-{month % 12 + 1:02d}"
        if published != expected:
            return {"status": "gap", "message": f"Archived {published}, but missing {expected}. Recover intervening months before appending; published data is unchanged."}
        build_comparison(None, raw, latest, published, data, to_metadata=metadata, minimum_records=minimum_records)
        return {"status": "updated", "message": f"Added {latest} to {published}"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--archive", type=Path, default=Path("sources/archive"))
    args = parser.parse_args()
    result = update(args.data, args.archive)
    print(result["message"])
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as output:
            output.write(f"status={result['status']}\n")
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as summary:
            summary.write(result["message"] + "\n")
    # In Actions the workflow first commits the archived source, then fails on a gap.
    if result["status"] == "gap" and not os.environ.get("GITHUB_OUTPUT"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
