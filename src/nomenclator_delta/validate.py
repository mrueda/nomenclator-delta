from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from nomenclator_delta.diff import product_state
from nomenclator_delta.schema import CHANGE_LABELS_ES, SCHEMA_VERSION


SNAPSHOT_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
TRANSITION_RE = re.compile(
    r"^(\d{4}-(?:0[1-9]|1[0-2]))_to_(\d{4}-(?:0[1-9]|1[0-2]))$"
)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def month_number(snapshot: str) -> int:
    year, month = snapshot.split("-")
    return int(year) * 12 + int(month) - 1


def validate_dataset(root: Path) -> list[str]:
    errors: list[str] = []
    metadata_path = root / "metadata.json"
    if not metadata_path.exists():
        return ["missing metadata.json"]
    metadata = read_json(metadata_path)
    if metadata.get("schema_version") != SCHEMA_VERSION:
        errors.append("metadata contains unsupported schema version")

    snapshots_value = metadata.get("snapshots", [])
    snapshots = snapshots_value if isinstance(snapshots_value, list) else []
    valid_snapshots = bool(snapshots) and all(
        isinstance(item, str) and SNAPSHOT_RE.fullmatch(item) for item in snapshots
    )
    if not valid_snapshots:
        errors.append("metadata contains invalid snapshots")
    elif len(snapshots) != len(set(snapshots)):
        errors.append("metadata contains duplicate snapshots")
    else:
        if snapshots != sorted(snapshots):
            errors.append("metadata snapshots are not chronological")
        if any(
            month_number(after) != month_number(before) + 1
            for before, after in zip(snapshots, snapshots[1:])
        ):
            errors.append("metadata snapshots are not consecutive months")
        if metadata.get("latest_snapshot") != snapshots[-1]:
            errors.append("metadata latest snapshot is inconsistent")
        if metadata.get("data_as_of") != snapshots[-1]:
            errors.append("metadata data_as_of is inconsistent")

    transitions_value = metadata.get("transitions", [])
    transitions = transitions_value if isinstance(transitions_value, list) else []
    expected_transitions = (
        [f"{before}_to_{after}" for before, after in zip(snapshots, snapshots[1:])]
        if valid_snapshots
        else []
    )
    if transitions != expected_transitions:
        errors.append("metadata transitions do not match snapshot chronology")

    products_by_snapshot: dict[str, dict[str, dict[str, Any]]] = {}
    provenance: dict[str, dict[str, Any]] = {}
    for snapshot in snapshots if valid_snapshots else []:
        snapshot_root = root / "snapshots" / snapshot
        product_path = snapshot_root / "products.json"
        snapshot_metadata_path = snapshot_root / "metadata.json"
        if not product_path.exists() or not snapshot_metadata_path.exists():
            errors.append(f"{snapshot}: missing snapshot products or metadata")
            continue
        products = read_json(product_path)
        snapshot_metadata = read_json(snapshot_metadata_path)
        if not isinstance(products, list):
            errors.append(f"{snapshot}: snapshot products are not a list")
            continue
        ids = [product.get("codigo_nacional") for product in products]
        if len(ids) != len(set(ids)):
            errors.append(f"{snapshot}: duplicate Código Nacional")
        if ids != sorted(ids):
            errors.append(f"{snapshot}: products are not sorted by Código Nacional")
        if snapshot_metadata.get("schema_version") != SCHEMA_VERSION:
            errors.append(f"{snapshot}: unsupported snapshot schema version")
        if snapshot_metadata.get("snapshot") != snapshot:
            errors.append(f"{snapshot}: snapshot metadata references wrong month")
        if snapshot_metadata.get("product_count") != len(products):
            errors.append(f"{snapshot}: metadata count does not match products")
        source = snapshot_metadata.get("source")
        if not isinstance(source, dict) or source.get("snapshot") != snapshot:
            errors.append(f"{snapshot}: invalid source provenance")
        else:
            provenance[snapshot] = source
        for product in products:
            if product.get("source_snapshot") != snapshot:
                errors.append(f"{snapshot}: product references wrong snapshot")
            if not re.fullmatch(r"\d{6}", str(product.get("codigo_nacional", ""))):
                errors.append(f"{snapshot}: invalid Código Nacional")
        products_by_snapshot[snapshot] = {
            product["codigo_nacional"]: product
            for product in products
            if "codigo_nacional" in product
        }

    all_codes = set().union(*(set(products) for products in products_by_snapshot.values()))
    latest_products = products_by_snapshot.get(snapshots[-1], {}) if valid_snapshots else {}

    event_ids: set[str] = set()
    events_by_cn: dict[str, list[dict[str, Any]]] = {}
    summaries: list[dict[str, Any]] = []
    for position, transition in enumerate(transitions):
        if not isinstance(transition, str):
            errors.append("metadata contains invalid transition")
            continue
        match = TRANSITION_RE.fullmatch(transition)
        if not match:
            errors.append(f"{transition}: invalid transition name")
            continue
        transition_from, transition_to = match.groups()
        change_path = root / "changes" / f"{transition}.json"
        if not change_path.exists():
            errors.append(f"{transition}: missing change file")
            continue
        payload = read_json(change_path)
        if payload.get("schema_version") != SCHEMA_VERSION:
            errors.append(f"{transition}: unsupported change schema version")
        summary = payload.get("summary", {})
        if not isinstance(summary, dict):
            errors.append(f"{transition}: summary is not an object")
            summary = {}
        events = payload.get("events", [])
        if not isinstance(events, list):
            errors.append(f"{transition}: events are not a list")
            continue
        summaries.append(summary)
        from_snapshot = summary.get("from_snapshot")
        to_snapshot = summary.get("to_snapshot")
        if from_snapshot != transition_from or to_snapshot != transition_to:
            errors.append(f"{transition}: summary does not match transition name")
        if position < len(expected_transitions) and transition != expected_transitions[position]:
            errors.append(f"{transition}: transition is out of chronological order")
        if from_snapshot not in products_by_snapshot or to_snapshot not in products_by_snapshot:
            errors.append(f"{transition}: references unknown snapshot")
            before_products: dict[str, dict[str, Any]] = {}
            after_products: dict[str, dict[str, Any]] = {}
        else:
            before_products = products_by_snapshot[from_snapshot]
            after_products = products_by_snapshot[to_snapshot]
            if summary.get("from_product_count") != len(before_products):
                errors.append(f"{transition}: from-product count does not match snapshot")
            if summary.get("to_product_count") != len(after_products):
                errors.append(f"{transition}: to-product count does not match snapshot")
        if summary.get("change_events") != len(events):
            errors.append(f"{transition}: event count does not match summary")
        actual_counts: dict[str, int] = {}
        changed_existing: set[str] = set()
        valid_events = []
        for event in events:
            if not isinstance(event, dict):
                errors.append(f"{transition}: event is not an object")
                continue
            valid_events.append(event)
            change_type = event.get("change_type")
            if not isinstance(change_type, str):
                errors.append(f"{transition}: event has invalid change type")
                continue
            if change_type not in CHANGE_LABELS_ES:
                errors.append(f"{transition}: event has unknown change type {change_type}")
            actual_counts[change_type] = actual_counts.get(change_type, 0) + 1
            if change_type not in {"PRODUCT_ADDED", "PRODUCT_REMOVED"}:
                cn = event.get("cn")
                if isinstance(cn, str):
                    changed_existing.add(cn)
        if summary.get("counts_by_type") != dict(sorted(actual_counts.items())):
            errors.append(f"{transition}: change-type counts do not match events")
        if summary.get("added") != actual_counts.get("PRODUCT_ADDED", 0):
            errors.append(f"{transition}: added count does not match events")
        if summary.get("removed") != actual_counts.get("PRODUCT_REMOVED", 0):
            errors.append(f"{transition}: removed count does not match events")
        if summary.get("changed_products") != len(changed_existing):
            errors.append(f"{transition}: changed-product count does not match events")

        for event in valid_events:
            event_id = event.get("id")
            if not isinstance(event_id, str):
                errors.append(f"{transition}: event has invalid id")
            elif event_id in event_ids:
                errors.append(f"{transition}: duplicate event id {event_id}")
            else:
                event_ids.add(event_id)
            if event.get("before") == event.get("after"):
                errors.append(f"{transition}: event has equal before and after values")
            if (
                event.get("from_snapshot") != from_snapshot
                or event.get("to_snapshot") != to_snapshot
            ):
                errors.append(f"{transition}: event references wrong snapshots")
            cn = event.get("cn")
            if not isinstance(cn, str):
                errors.append(f"{transition}: event has invalid Código Nacional")
                continue
            in_before = cn in before_products
            in_after = cn in after_products
            change_type = event.get("change_type")
            if change_type == "PRODUCT_ADDED" and (in_before or not in_after):
                errors.append(f"{transition}: invalid added-product event for {cn}")
            elif change_type == "PRODUCT_REMOVED" and (not in_before or in_after):
                errors.append(f"{transition}: invalid removed-product event for {cn}")
            elif change_type not in {"PRODUCT_ADDED", "PRODUCT_REMOVED"} and not (
                in_before and in_after
            ):
                errors.append(f"{transition}: changed product {cn} is absent from a snapshot")
            events_by_cn.setdefault(cn, []).append(event)

    changes_index_path = root / "indexes" / "changes-by-month.json"
    if not changes_index_path.exists():
        errors.append("missing changes-by-month index")
    elif read_json(changes_index_path) != summaries:
        errors.append("changes-by-month index does not match transitions")

    index_path = root / "indexes" / "products.json"
    if not index_path.exists():
        errors.append("missing product index")
    else:
        index = read_json(index_path)
        expected_index = []
        for cn in sorted(all_codes):
            product = next(
                products_by_snapshot[snapshot][cn]
                for snapshot in reversed(snapshots)
                if snapshot in products_by_snapshot and cn in products_by_snapshot[snapshot]
            )
            expected_index.append(
                {
                    "cn": cn,
                    "medicine_name": product["medicine_name"],
                    "laboratory": product["laboratory"]["name"],
                    "active_ingredients": product["active_ingredients"],
                    "status": product["status"],
                    "prices": product["prices"],
                    "present_in_latest": cn in latest_products,
                    "has_changes": cn in events_by_cn,
                }
            )
        if index != expected_index:
            errors.append("product index does not match snapshot products and events")

    if metadata.get("product_count") != len(all_codes):
        errors.append("metadata product count does not match snapshots")
    if metadata.get("current_product_count") != len(latest_products):
        errors.append("metadata current product count does not match latest snapshot")

    products_root = root / "products"
    actual_history_codes = (
        {path.stem for path in products_root.glob("*.json")} if products_root.exists() else set()
    )
    if actual_history_codes != set(events_by_cn):
        errors.append("product histories do not match products with change events")
    for cn, expected_events in events_by_cn.items():
        history_path = products_root / f"{cn}.json"
        if not history_path.exists():
            errors.append(f"missing history for {cn}")
            continue
        history = read_json(history_path)
        if history.get("cn") != cn:
            errors.append(f"{history_path.name}: history references wrong product")
        expected_event_ids = [event.get("id") for event in expected_events]
        history_event_ids = [event.get("id") for event in history.get("events", [])]
        if history_event_ids != expected_event_ids:
            errors.append(f"{history_path.name}: history events do not match transitions")

        relevant_snapshots = {
            event.get(field)
            for event in expected_events
            for field in ("from_snapshot", "to_snapshot")
            if isinstance(event.get(field), str)
        }
        expected_history_snapshots = [
            {
                "snapshot": snapshot,
                "state": product_state(products_by_snapshot[snapshot][cn]),
            }
            for snapshot in snapshots
            if snapshot in relevant_snapshots
            and snapshot in products_by_snapshot
            and cn in products_by_snapshot[snapshot]
        ]
        if history.get("snapshots") != expected_history_snapshots:
            errors.append(f"{history_path.name}: snapshots do not match change history")
        history_snapshots = [
            item.get("snapshot") for item in history.get("snapshots", [])
        ]
        if history_snapshots != sorted(history_snapshots):
            errors.append(f"{history_path.name}: snapshots are not chronological")
        expected_sources = {
            snapshot: provenance[snapshot]
            for snapshot in snapshots
            if snapshot in relevant_snapshots and snapshot in provenance
        }
        if history.get("sources") != expected_sources:
            errors.append(f"{history_path.name}: sources do not match change history")
        latest_product = next(
            products_by_snapshot[snapshot][cn]
            for snapshot in reversed(snapshots)
            if snapshot in products_by_snapshot and cn in products_by_snapshot[snapshot]
        )
        if history.get("current") != product_state(latest_product):
            errors.append(f"{history_path.name}: current state does not match latest product")

    return sorted(set(errors))
