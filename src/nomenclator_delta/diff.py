from __future__ import annotations

from collections import Counter
from typing import Any

from nomenclator_delta.schema import CHANGE_LABELS_ES, DIFF_FIELDS


def value_at(product: dict[str, Any], path: str) -> Any:
    value: Any = product
    for key in path.split("."):
        value = value[key]
    return value


def product_state(product: dict[str, Any]) -> dict[str, Any]:
    return {
        "medicine_name": product["medicine_name"],
        "laboratory": product["laboratory"],
        "status": product["status"],
        "contribution": product["contribution"],
        "active_ingredients": product["active_ingredients"],
        "prices": product["prices"],
    }


def diff_snapshots(
    from_products: list[dict[str, Any]],
    to_products: list[dict[str, Any]],
    from_snapshot: str,
    to_snapshot: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    before = {product["codigo_nacional"]: product for product in from_products}
    after = {product["codigo_nacional"]: product for product in to_products}
    events: list[dict[str, Any]] = []
    transition = f"{from_snapshot}_to_{to_snapshot}"

    def add_event(
        cn: str,
        change_type: str,
        field: str | None,
        field_label_es: str,
        old: Any,
        new: Any,
    ) -> None:
        sequence = sum(1 for event in events if event["cn"] == cn)
        events.append(
            {
                "id": f"{transition}:{cn}:{change_type}:{sequence}",
                "cn": cn,
                "from_snapshot": from_snapshot,
                "to_snapshot": to_snapshot,
                "change_type": change_type,
                "change_label_es": CHANGE_LABELS_ES[change_type],
                "field": field,
                "field_label_es": field_label_es,
                "before": old,
                "after": new,
                "source": {
                    "authority": "Ministerio de Sanidad",
                    "official_source_url": "https://www.sanidad.gob.es/profesionales/nomenclator.do",
                    "from_snapshot": from_snapshot,
                    "to_snapshot": to_snapshot,
                },
            }
        )

    for cn in sorted(set(after) - set(before)):
        add_event(cn, "PRODUCT_ADDED", None, "Presentación", None, product_state(after[cn]))
    for cn in sorted(set(before) - set(after)):
        add_event(cn, "PRODUCT_REMOVED", None, "Presentación", product_state(before[cn]), None)
    for cn in sorted(set(before) & set(after)):
        for diff_field in DIFF_FIELDS:
            old = value_at(before[cn], diff_field.path)
            new = value_at(after[cn], diff_field.path)
            if old != new:
                add_event(
                    cn,
                    diff_field.change_type,
                    diff_field.path,
                    diff_field.label_es,
                    old,
                    new,
                )

    events.sort(key=lambda event: (event["cn"], event["change_type"], event["field"] or ""))
    type_counts = Counter(event["change_type"] for event in events)
    changed_existing = {
        event["cn"]
        for event in events
        if event["change_type"] not in {"PRODUCT_ADDED", "PRODUCT_REMOVED"}
    }
    summary = {
        "from_snapshot": from_snapshot,
        "to_snapshot": to_snapshot,
        "from_product_count": len(before),
        "to_product_count": len(after),
        "added": type_counts["PRODUCT_ADDED"],
        "removed": type_counts["PRODUCT_REMOVED"],
        "changed_products": len(changed_existing),
        "change_events": len(events),
        "counts_by_type": dict(sorted(type_counts.items())),
    }
    return events, summary
