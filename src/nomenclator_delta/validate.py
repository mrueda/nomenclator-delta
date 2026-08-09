from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


SNAPSHOT_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_dataset(root: Path) -> list[str]:
    errors: list[str] = []
    metadata_path = root / "metadata.json"
    if not metadata_path.exists():
        return ["missing metadata.json"]
    metadata = read_json(metadata_path)
    snapshots = metadata.get("snapshots", [])
    if not snapshots or any(not SNAPSHOT_RE.fullmatch(item) for item in snapshots):
        errors.append("metadata contains invalid snapshots")

    products_by_snapshot: dict[str, dict[str, dict[str, Any]]] = {}
    for snapshot in snapshots:
        snapshot_root = root / "snapshots" / snapshot
        product_path = snapshot_root / "products.json"
        snapshot_metadata_path = snapshot_root / "metadata.json"
        if not product_path.exists() or not snapshot_metadata_path.exists():
            errors.append(f"{snapshot}: missing snapshot products or metadata")
            continue
        products = read_json(product_path)
        snapshot_metadata = read_json(snapshot_metadata_path)
        ids = [product.get("codigo_nacional") for product in products]
        if len(ids) != len(set(ids)):
            errors.append(f"{snapshot}: duplicate Código Nacional")
        if snapshot_metadata.get("product_count") != len(products):
            errors.append(f"{snapshot}: metadata count does not match products")
        for product in products:
            if product.get("source_snapshot") != snapshot:
                errors.append(f"{snapshot}: product references wrong snapshot")
            if not re.fullmatch(r"\d{6}", str(product.get("codigo_nacional", ""))):
                errors.append(f"{snapshot}: invalid Código Nacional")
        products_by_snapshot[snapshot] = {product["codigo_nacional"]: product for product in products}

    index_path = root / "indexes" / "products.json"
    if not index_path.exists():
        errors.append("missing product index")
    else:
        index = read_json(index_path)
        expected = set().union(*(set(products) for products in products_by_snapshot.values()))
        if {item.get("cn") for item in index} != expected:
            errors.append("product index does not match snapshot products")

    for transition in metadata.get("transitions", []):
        change_path = root / "changes" / f"{transition}.json"
        if not change_path.exists():
            errors.append(f"{transition}: missing change file")
            continue
        payload = read_json(change_path)
        summary = payload.get("summary", {})
        events = payload.get("events", [])
        from_snapshot = summary.get("from_snapshot")
        to_snapshot = summary.get("to_snapshot")
        if from_snapshot not in snapshots or to_snapshot not in snapshots:
            errors.append(f"{transition}: references unknown snapshot")
        if summary.get("change_events") != len(events):
            errors.append(f"{transition}: event count does not match summary")
        actual_counts: dict[str, int] = {}
        for event in events:
            change_type = event.get("change_type")
            actual_counts[change_type] = actual_counts.get(change_type, 0) + 1
        if summary.get("counts_by_type") != dict(sorted(actual_counts.items())):
            errors.append(f"{transition}: change-type counts do not match events")
        event_ids: set[str] = set()
        history_paths: set[Path] = set()
        for event in events:
            if event.get("id") in event_ids:
                errors.append(f"{transition}: duplicate event id {event.get('id')}")
            event_ids.add(event.get("id"))
            if event.get("before") == event.get("after"):
                errors.append(f"{transition}: event has equal before and after values")
            if event.get("from_snapshot") != from_snapshot or event.get("to_snapshot") != to_snapshot:
                errors.append(f"{transition}: event references wrong snapshots")
            history = root / "products" / f"{event.get('cn')}.json"
            if not history.exists():
                errors.append(f"{transition}: missing history for {event.get('cn')}")
            else:
                history_paths.add(history)
        for history_path in history_paths:
            history = read_json(history_path)
            history_snapshots = [item.get("snapshot") for item in history.get("snapshots", [])]
            if history_snapshots != sorted(history_snapshots):
                errors.append(f"{history_path.name}: snapshots are not chronological")
            history_event_ids = {event.get("id") for event in history.get("events", [])}
            expected_event_ids = {
                event.get("id") for event in events if event.get("cn") == history.get("cn")
            }
            if history_event_ids != expected_event_ids:
                errors.append(f"{history_path.name}: history events do not match transition")

    return sorted(set(errors))
