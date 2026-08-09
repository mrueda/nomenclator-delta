from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

from nomenclator_delta.diff import diff_snapshots, product_state
from nomenclator_delta.parse import parse_csv
from nomenclator_delta.schema import PARSER_VERSION, SCHEMA_VERSION


LANDING_PAGE_URL = "https://www.sanidad.gob.es/profesionales/nomenclator.do"


def write_json(path: Path, payload: Any, *, compact: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    options: dict[str, Any] = {"ensure_ascii": False, "sort_keys": True}
    if compact:
        options["separators"] = (",", ":")
    else:
        options["indent"] = 2
    path.write_text(json.dumps(payload, **options) + "\n", encoding="utf-8")


def artifact_metadata(path: Path, snapshot: str, supplied: Path | None = None) -> dict[str, Any]:
    content = path.read_bytes()
    metadata: dict[str, Any] = {
        "authority": "Ministerio de Sanidad",
        "source_url": LANDING_PAGE_URL,
        "retrieved_at": None,
        "snapshot": snapshot,
        "original_filename": path.name,
        "mime_type": "text/csv",
        "sha256": hashlib.sha256(content).hexdigest(),
        "file_size": len(content),
        "parser_version": PARSER_VERSION,
    }
    if supplied:
        metadata.update(json.loads(supplied.read_text(encoding="utf-8")))
    if metadata.get("snapshot") != snapshot:
        raise ValueError(f"metadata snapshot does not match {snapshot}")
    actual_hash = hashlib.sha256(content).hexdigest()
    if metadata.get("sha256") != actual_hash:
        raise ValueError(f"artifact hash does not match metadata for {snapshot}")
    if metadata.get("file_size") != len(content):
        raise ValueError(f"artifact size does not match metadata for {snapshot}")
    metadata.pop("artifact", None)
    return metadata


def build_comparison(
    from_source: Path,
    to_source: Path,
    from_snapshot: str,
    to_snapshot: str,
    output: Path,
    *,
    from_metadata: Path | None = None,
    to_metadata: Path | None = None,
    minimum_records: int = 15_000,
    maximum_count_change_ratio: float = 0.2,
) -> dict[str, Any]:
    before, before_warnings = parse_csv(from_source, from_snapshot)
    after, after_warnings = parse_csv(to_source, to_snapshot)
    if len(before) < minimum_records or len(after) < minimum_records:
        raise ValueError(
            f"suspicious product count: {len(before)} -> {len(after)}; minimum is {minimum_records}"
        )
    count_change_ratio = abs(len(after) - len(before)) / max(len(before), 1)
    if count_change_ratio > maximum_count_change_ratio:
        raise ValueError(f"catastrophic product-count change: {count_change_ratio:.1%}")

    provenance = {
        from_snapshot: artifact_metadata(from_source, from_snapshot, from_metadata),
        to_snapshot: artifact_metadata(to_source, to_snapshot, to_metadata),
    }
    events, summary = diff_snapshots(before, after, from_snapshot, to_snapshot)
    transition = f"{from_snapshot}_to_{to_snapshot}"
    reset_generated_paths(output)

    write_snapshot(output, from_snapshot, before, provenance[from_snapshot], before_warnings)
    write_snapshot(output, to_snapshot, after, provenance[to_snapshot], after_warnings)
    write_json(
        output / "changes" / f"{transition}.json",
        {"schema_version": SCHEMA_VERSION, "summary": summary, "events": events},
    )
    write_indexes_and_histories(output, before, after, events, summary, provenance)

    report = {
        "transition": transition,
        "source_records": {from_snapshot: len(before), to_snapshot: len(after)},
        "normalized_records": {from_snapshot: len(before), to_snapshot: len(after)},
        "warnings": before_warnings + after_warnings,
        "errors": [],
        **summary,
    }
    write_json(output / "build-report.json", report)
    metadata = {
        "schema_version": SCHEMA_VERSION,
        "project": "nomenclator-delta",
        "authority": "Ministerio de Sanidad",
        "official_source_url": LANDING_PAGE_URL,
        "snapshots": [from_snapshot, to_snapshot],
        "latest_snapshot": to_snapshot,
        "transitions": [transition],
        "product_count": len({p["codigo_nacional"] for p in before + after}),
        "current_product_count": len(after),
        "data_as_of": to_snapshot,
        "disclaimer_es": (
            "nomenclator-delta es un proyecto independiente de código abierto que reorganiza y "
            "compara datos oficiales de acceso público. No está afiliado ni respaldado por el "
            "Ministerio de Sanidad. El Nomenclátor y las publicaciones oficiales siguen siendo "
            "la fuente autorizada."
        ),
    }
    write_json(output / "metadata.json", metadata)
    return metadata


def reset_generated_paths(output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    for name in ("snapshots", "changes", "products", "indexes"):
        path = output / name
        if path.exists():
            shutil.rmtree(path)
    for name in ("metadata.json", "build-report.json"):
        path = output / name
        if path.exists():
            path.unlink()


def write_snapshot(
    output: Path,
    snapshot: str,
    products: list[dict[str, Any]],
    provenance: dict[str, Any],
    warnings: list[str],
) -> None:
    base = output / "snapshots" / snapshot
    write_json(base / "products.json", products, compact=True)
    write_json(
        base / "metadata.json",
        {
            "schema_version": SCHEMA_VERSION,
            "snapshot": snapshot,
            "product_count": len(products),
            "warnings": warnings,
            "source": provenance,
        },
    )


def write_indexes_and_histories(
    output: Path,
    before: list[dict[str, Any]],
    after: list[dict[str, Any]],
    events: list[dict[str, Any]],
    summary: dict[str, Any],
    provenance: dict[str, dict[str, Any]],
) -> None:
    before_by_cn = {product["codigo_nacional"]: product for product in before}
    after_by_cn = {product["codigo_nacional"]: product for product in after}
    events_by_cn: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        events_by_cn.setdefault(event["cn"], []).append(event)

    index = []
    for cn in sorted(set(before_by_cn) | set(after_by_cn)):
        product = after_by_cn.get(cn) or before_by_cn[cn]
        index.append(
            {
                "cn": cn,
                "medicine_name": product["medicine_name"],
                "laboratory": product["laboratory"]["name"],
                "active_ingredients": product["active_ingredients"],
                "status": product["status"],
                "prices": product["prices"],
                "present_in_latest": cn in after_by_cn,
                "has_changes": cn in events_by_cn,
            }
        )
        if cn in events_by_cn:
            snapshots = []
            if cn in before_by_cn:
                snapshots.append(
                    {"snapshot": summary["from_snapshot"], "state": product_state(before_by_cn[cn])}
                )
            if cn in after_by_cn:
                snapshots.append(
                    {"snapshot": summary["to_snapshot"], "state": product_state(after_by_cn[cn])}
                )
            write_json(
                output / "products" / f"{cn}.json",
                {
                    "cn": cn,
                    "current": product_state(product),
                    "snapshots": snapshots,
                    "events": events_by_cn[cn],
                    "sources": provenance,
                },
            )

    write_json(output / "indexes" / "products.json", index, compact=True)
    write_json(output / "indexes" / "changes-by-month.json", [summary])
