from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from datetime import date
from pathlib import Path
from typing import Any

from nomenclator_delta.diff import diff_snapshots, product_state
from nomenclator_delta.parse import parse_csv
from nomenclator_delta.schema import PARSER_VERSION, SCHEMA_VERSION


LANDING_PAGE_URL = "https://www.sanidad.gob.es/profesionales/nomenclator.do"
DISCLAIMER_ES = (
    "nomenclator-delta es un proyecto independiente de código abierto que reorganiza y "
    "compara datos oficiales de acceso público. No está afiliado ni respaldado por el "
    "Ministerio de Sanidad. El Nomenclátor y las publicaciones oficiales siguen siendo "
    "la fuente autorizada."
)


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
    from_source: Path | None,
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
    require_consecutive_snapshots(from_snapshot, to_snapshot)
    existing_metadata = read_existing_metadata(output)

    if existing_metadata is None:
        if from_source is None:
            raise ValueError("from-source is required when creating a new dataset")
        before, before_warnings = parse_csv(from_source, from_snapshot)
        provenance = {
            from_snapshot: artifact_metadata(from_source, from_snapshot, from_metadata),
        }
        snapshots = [from_snapshot, to_snapshot]
        transitions: list[str] = []
    else:
        latest_snapshot = existing_metadata["latest_snapshot"]
        if from_snapshot != latest_snapshot:
            raise ValueError(
                f"append must start at latest snapshot {latest_snapshot}, got {from_snapshot}"
            )
        if to_snapshot in existing_metadata["snapshots"]:
            raise ValueError(f"snapshot {to_snapshot} already exists")
        transition = f"{from_snapshot}_to_{to_snapshot}"
        if transition in existing_metadata["transitions"]:
            raise ValueError(f"transition {transition} already exists")

        # The normalized latest snapshot is the canonical input for an append. The
        # older raw artifact need not remain available and is never parsed again.
        before = read_json(output / "snapshots" / from_snapshot / "products.json")
        previous_snapshot_metadata = read_json(
            output / "snapshots" / from_snapshot / "metadata.json"
        )
        before_warnings = previous_snapshot_metadata.get("warnings", [])
        if from_metadata is not None:
            verify_stored_source_metadata(
                previous_snapshot_metadata["source"], from_metadata, from_snapshot
            )
        provenance = load_provenance(output, existing_metadata["snapshots"])
        snapshots = [*existing_metadata["snapshots"], to_snapshot]
        transitions = list(existing_metadata["transitions"])

    after, after_warnings = parse_csv(to_source, to_snapshot)
    if len(before) < minimum_records or len(after) < minimum_records:
        raise ValueError(
            f"suspicious product count: {len(before)} -> {len(after)}; minimum is {minimum_records}"
        )
    count_change_ratio = abs(len(after) - len(before)) / max(len(before), 1)
    if count_change_ratio > maximum_count_change_ratio:
        raise ValueError(f"catastrophic product-count change: {count_change_ratio:.1%}")

    provenance[to_snapshot] = artifact_metadata(to_source, to_snapshot, to_metadata)
    events, summary = diff_snapshots(before, after, from_snapshot, to_snapshot)
    transition = f"{from_snapshot}_to_{to_snapshot}"
    transitions.append(transition)

    report = {
        "transition": transition,
        "source_records": {from_snapshot: len(before), to_snapshot: len(after)},
        "normalized_records": {from_snapshot: len(before), to_snapshot: len(after)},
        "warnings": before_warnings + after_warnings,
        "errors": [],
        **summary,
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    temporary_root = Path(
        tempfile.mkdtemp(prefix=f".{output.name}-build-", dir=output.parent)
    )
    staged_output = temporary_root / "dataset"
    try:
        if existing_metadata is None:
            staged_output.mkdir()
            write_snapshot(
                staged_output,
                from_snapshot,
                before,
                provenance[from_snapshot],
                before_warnings,
            )
        else:
            shutil.copytree(output, staged_output)

        write_snapshot(
            staged_output,
            to_snapshot,
            after,
            provenance[to_snapshot],
            after_warnings,
        )
        write_json(
            staged_output / "changes" / f"{transition}.json",
            {"schema_version": SCHEMA_VERSION, "summary": summary, "events": events},
        )
        write_indexes_and_histories(staged_output, snapshots, transitions)

        all_products = load_snapshot_products(staged_output, snapshots)
        metadata = dataset_metadata(snapshots, transitions, all_products)
        write_json(staged_output / "build-report.json", report)
        write_json(staged_output / "metadata.json", metadata)

        from nomenclator_delta.validate import validate_dataset

        validation_errors = validate_dataset(staged_output)
        if validation_errors:
            raise ValueError(
                "generated dataset is invalid: " + "; ".join(validation_errors)
            )
        install_staged_output(output, staged_output, temporary_root)
    finally:
        if temporary_root.exists():
            shutil.rmtree(temporary_root)

    return metadata


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def next_snapshot(snapshot: str) -> str:
    try:
        year_text, month_text = snapshot.split("-", 1)
        current = date(int(year_text), int(month_text), 1)
    except (TypeError, ValueError) as error:
        raise ValueError(f"invalid snapshot {snapshot!r}; expected YYYY-MM") from error
    if snapshot != current.strftime("%Y-%m"):
        raise ValueError(f"invalid snapshot {snapshot!r}; expected YYYY-MM")
    if current.month == 12:
        return f"{current.year + 1:04d}-01"
    return f"{current.year:04d}-{current.month + 1:02d}"


def require_consecutive_snapshots(from_snapshot: str, to_snapshot: str) -> None:
    expected = next_snapshot(from_snapshot)
    next_snapshot(to_snapshot)
    if to_snapshot != expected:
        raise ValueError(
            f"snapshots must be consecutive: expected {expected} after {from_snapshot}, "
            f"got {to_snapshot}"
        )


def read_existing_metadata(output: Path) -> dict[str, Any] | None:
    if not output.exists():
        return None
    if not output.is_dir():
        raise ValueError(f"output exists and is not a directory: {output}")
    if not any(output.iterdir()):
        return None
    if not (output / "metadata.json").exists():
        raise ValueError("refusing to replace non-empty output without metadata.json")

    from nomenclator_delta.validate import validate_dataset

    errors = validate_dataset(output)
    if errors:
        raise ValueError("existing output is invalid: " + "; ".join(errors))
    return read_json(output / "metadata.json")


def verify_stored_source_metadata(
    stored: dict[str, Any], supplied_path: Path, snapshot: str
) -> None:
    supplied = read_json(supplied_path)
    supplied.pop("artifact", None)
    for field in ("snapshot", "sha256", "file_size"):
        if supplied.get(field) != stored.get(field):
            raise ValueError(
                f"supplied metadata conflicts with stored source for {snapshot}: {field}"
            )


def load_provenance(output: Path, snapshots: list[str]) -> dict[str, dict[str, Any]]:
    return {
        snapshot: read_json(output / "snapshots" / snapshot / "metadata.json")["source"]
        for snapshot in snapshots
    }


def load_snapshot_products(
    output: Path, snapshots: list[str]
) -> dict[str, list[dict[str, Any]]]:
    return {
        snapshot: read_json(output / "snapshots" / snapshot / "products.json")
        for snapshot in snapshots
    }


def dataset_metadata(
    snapshots: list[str],
    transitions: list[str],
    products_by_snapshot: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    all_codes = {
        product["codigo_nacional"]
        for snapshot in snapshots
        for product in products_by_snapshot[snapshot]
    }
    latest_snapshot = snapshots[-1]
    return {
        "schema_version": SCHEMA_VERSION,
        "project": "nomenclator-delta",
        "authority": "Ministerio de Sanidad",
        "official_source_url": LANDING_PAGE_URL,
        "snapshots": snapshots,
        "latest_snapshot": latest_snapshot,
        "transitions": transitions,
        "product_count": len(all_codes),
        "current_product_count": len(products_by_snapshot[latest_snapshot]),
        "data_as_of": latest_snapshot,
        "disclaimer_es": DISCLAIMER_ES,
    }


def install_staged_output(output: Path, staged_output: Path, temporary_root: Path) -> None:
    previous_output = temporary_root / "previous"
    if output.exists():
        output.replace(previous_output)
    try:
        staged_output.replace(output)
    except Exception:
        if output.exists():
            output.replace(temporary_root / "failed-output")
        if previous_output.exists():
            previous_output.replace(output)
        raise


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
    snapshots: list[str],
    transitions: list[str],
) -> None:
    for directory in (output / "products", output / "indexes"):
        if directory.exists():
            shutil.rmtree(directory)

    products_by_snapshot = {
        snapshot: {
            product["codigo_nacional"]: product
            for product in read_json(output / "snapshots" / snapshot / "products.json")
        }
        for snapshot in snapshots
    }
    provenance = load_provenance(output, snapshots)
    events_by_cn: dict[str, list[dict[str, Any]]] = {}
    summaries: list[dict[str, Any]] = []
    for transition in transitions:
        payload = read_json(output / "changes" / f"{transition}.json")
        summaries.append(payload["summary"])
        for event in payload["events"]:
            events_by_cn.setdefault(event["cn"], []).append(event)

    index = []
    all_codes = set().union(*(set(products) for products in products_by_snapshot.values()))
    latest_products = products_by_snapshot[snapshots[-1]]
    for cn in sorted(all_codes):
        product = next(
            products_by_snapshot[snapshot][cn]
            for snapshot in reversed(snapshots)
            if cn in products_by_snapshot[snapshot]
        )
        index.append(
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
        if cn in events_by_cn:
            relevant_snapshot_names = {
                event[snapshot_field]
                for event in events_by_cn[cn]
                for snapshot_field in ("from_snapshot", "to_snapshot")
            }
            history_snapshots = [
                {
                    "snapshot": snapshot,
                    "state": product_state(products_by_snapshot[snapshot][cn]),
                }
                for snapshot in snapshots
                if snapshot in relevant_snapshot_names and cn in products_by_snapshot[snapshot]
            ]
            write_json(
                output / "products" / f"{cn}.json",
                {
                    "cn": cn,
                    "current": product_state(product),
                    "snapshots": history_snapshots,
                    "events": events_by_cn[cn],
                    "sources": {
                        snapshot: provenance[snapshot]
                        for snapshot in snapshots
                        if snapshot in relevant_snapshot_names
                    },
                },
            )

    write_json(output / "indexes" / "products.json", index, compact=True)
    write_json(output / "indexes" / "changes-by-month.json", summaries)
