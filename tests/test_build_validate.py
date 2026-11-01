import hashlib
import json
from pathlib import Path

import pytest

from nomenclator_delta.build import build_comparison
from nomenclator_delta.validate import validate_dataset


FIXTURES = Path(__file__).parent / "fixtures"


def test_explicit_gap_preserves_history_and_allows_next_month(tmp_path):
    output = tmp_path / "data"
    build_comparison(FIXTURES / "2026-07.csv", FIXTURES / "2026-08.csv",
                     "2026-08", "2026-09", output, minimum_records=1)
    previous = dataset_digest(output / "snapshots")
    build_comparison(None, FIXTURES / "2026-09.csv", "2026-09", "2026-11",
                     output, minimum_records=1, allow_gap=True)
    assert validate_dataset(output) == []
    assert not (output / "snapshots" / "2026-10").exists()
    assert all(dataset_digest(output / "snapshots")[path] == digest
               for path, digest in previous.items())
    build_comparison(None, FIXTURES / "2026-09.csv", "2026-11", "2026-12",
                     output, minimum_records=1)
    assert validate_dataset(output) == []
    assert json.loads((output / "metadata.json").read_text())["transitions"] == [
        "2026-08_to_2026-09", "2026-09_to_2026-11", "2026-11_to_2026-12"]


@pytest.mark.parametrize("end", ["2026-08", "2026-07", "2026-10", "2027-01", "invalid"])
def test_explicit_gap_rejects_non_forward_or_invalid_month(tmp_path, end):
    with pytest.raises(ValueError):
        build_comparison(FIXTURES / "2026-07.csv", FIXTURES / "2026-08.csv",
                         "2026-08", end, tmp_path / "data", minimum_records=1,
                         allow_gap=True)


def dataset_digest(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_complete_comparison_build_and_validation(tmp_path):
    output = tmp_path / "data"
    metadata = build_comparison(
        FIXTURES / "2026-07.csv",
        FIXTURES / "2026-08.csv",
        "2026-07",
        "2026-08",
        output,
        minimum_records=1,
    )
    assert metadata["current_product_count"] == 3
    assert (output / "products" / "123456.json").exists()
    assert not (output / "products" / "345678.json").exists()
    assert validate_dataset(output) == []


def test_sanity_threshold_rejects_implausibly_small_source(tmp_path):
    try:
        build_comparison(
            FIXTURES / "2026-07.csv",
            FIXTURES / "2026-08.csv",
            "2026-07",
            "2026-08",
            tmp_path / "data",
        )
    except ValueError as error:
        assert "suspicious product count" in str(error)
    else:
        raise AssertionError("small source passed the production threshold")


def test_append_uses_normalized_latest_snapshot_and_preserves_history(tmp_path):
    output = tmp_path / "data"
    build_comparison(
        FIXTURES / "2026-07.csv",
        FIXTURES / "2026-08.csv",
        "2026-07",
        "2026-08",
        output,
        minimum_records=1,
    )
    original_snapshot = (output / "snapshots" / "2026-08" / "products.json").read_bytes()
    original_changes = (output / "changes" / "2026-07_to_2026-08.json").read_bytes()

    metadata = build_comparison(
        None,
        FIXTURES / "2026-09.csv",
        "2026-08",
        "2026-09",
        output,
        minimum_records=1,
    )

    assert metadata["snapshots"] == ["2026-07", "2026-08", "2026-09"]
    assert metadata["transitions"] == [
        "2026-07_to_2026-08",
        "2026-08_to_2026-09",
    ]
    assert metadata["latest_snapshot"] == "2026-09"
    assert metadata["product_count"] == 5
    assert metadata["current_product_count"] == 3
    assert (output / "snapshots" / "2026-08" / "products.json").read_bytes() == original_snapshot
    assert (output / "changes" / "2026-07_to_2026-08.json").read_bytes() == original_changes

    history = json.loads((output / "products" / "123456.json").read_text(encoding="utf-8"))
    assert [item["snapshot"] for item in history["snapshots"]] == [
        "2026-07",
        "2026-08",
        "2026-09",
    ]
    assert [event["to_snapshot"] for event in history["events"]] == ["2026-08", "2026-09"]
    assert list(history["sources"]) == ["2026-07", "2026-08", "2026-09"]

    changes_index = json.loads(
        (output / "indexes" / "changes-by-month.json").read_text(encoding="utf-8")
    )
    assert [summary["to_snapshot"] for summary in changes_index] == ["2026-08", "2026-09"]
    assert validate_dataset(output) == []


def test_append_is_deterministic(tmp_path):
    outputs = [tmp_path / "first", tmp_path / "second"]
    for output in outputs:
        build_comparison(
            FIXTURES / "2026-07.csv",
            FIXTURES / "2026-08.csv",
            "2026-07",
            "2026-08",
            output,
            minimum_records=1,
        )
        build_comparison(
            None,
            FIXTURES / "2026-09.csv",
            "2026-08",
            "2026-09",
            output,
            minimum_records=1,
        )

    assert dataset_digest(outputs[0]) == dataset_digest(outputs[1])


def test_rejected_append_does_not_modify_existing_output(tmp_path):
    output = tmp_path / "data"
    build_comparison(
        FIXTURES / "2026-07.csv",
        FIXTURES / "2026-08.csv",
        "2026-07",
        "2026-08",
        output,
        minimum_records=1,
    )
    original = dataset_digest(output)

    with pytest.raises(ValueError, match="snapshots must be consecutive"):
        build_comparison(
            None,
            FIXTURES / "2026-09.csv",
            "2026-08",
            "2026-10",
            output,
            minimum_records=1,
        )
    assert dataset_digest(output) == original

    with pytest.raises(ValueError, match="append must start at latest snapshot"):
        build_comparison(
            FIXTURES / "2026-07.csv",
            FIXTURES / "2026-08.csv",
            "2026-07",
            "2026-08",
            output,
            minimum_records=1,
        )
    assert dataset_digest(output) == original

    stored_source = json.loads(
        (output / "snapshots" / "2026-08" / "metadata.json").read_text(encoding="utf-8")
    )["source"]
    stored_source["sha256"] = "0" * 64
    conflicting_metadata = tmp_path / "conflicting-metadata.json"
    conflicting_metadata.write_text(json.dumps(stored_source), encoding="utf-8")
    with pytest.raises(ValueError, match="conflicts with stored source"):
        build_comparison(
            None,
            FIXTURES / "2026-09.csv",
            "2026-08",
            "2026-09",
            output,
            from_metadata=conflicting_metadata,
            minimum_records=1,
        )
    assert dataset_digest(output) == original


def test_validation_rejects_nonchronological_multi_transition_metadata(tmp_path):
    output = tmp_path / "data"
    build_comparison(
        FIXTURES / "2026-07.csv",
        FIXTURES / "2026-08.csv",
        "2026-07",
        "2026-08",
        output,
        minimum_records=1,
    )
    build_comparison(
        None,
        FIXTURES / "2026-09.csv",
        "2026-08",
        "2026-09",
        output,
        minimum_records=1,
    )
    metadata_path = output / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["transitions"].reverse()
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    assert "metadata transitions do not match snapshot chronology" in validate_dataset(output)


def test_validation_rejects_cross_transition_event_reference(tmp_path):
    output = tmp_path / "data"
    build_comparison(
        FIXTURES / "2026-07.csv",
        FIXTURES / "2026-08.csv",
        "2026-07",
        "2026-08",
        output,
        minimum_records=1,
    )
    build_comparison(
        None,
        FIXTURES / "2026-09.csv",
        "2026-08",
        "2026-09",
        output,
        minimum_records=1,
    )
    changes_path = output / "changes" / "2026-08_to_2026-09.json"
    changes = json.loads(changes_path.read_text(encoding="utf-8"))
    changes["events"][0]["from_snapshot"] = "2026-07"
    changes_path.write_text(json.dumps(changes), encoding="utf-8")

    assert "2026-08_to_2026-09: event references wrong snapshots" in validate_dataset(output)
