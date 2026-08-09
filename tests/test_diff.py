import json
from pathlib import Path

from nomenclator_delta.diff import diff_snapshots
from nomenclator_delta.parse import parse_csv


FIXTURES = Path(__file__).parent / "fixtures"


def test_semantic_diff_suppresses_ingredient_order_noise():
    before, _ = parse_csv(FIXTURES / "2026-07.csv", "2026-07")
    after, _ = parse_csv(FIXTURES / "2026-08.csv", "2026-08")
    events, summary = diff_snapshots(before, after, "2026-07", "2026-08")

    assert summary == {
        "from_snapshot": "2026-07",
        "to_snapshot": "2026-08",
        "from_product_count": 3,
        "to_product_count": 3,
        "added": 1,
        "removed": 1,
        "changed_products": 1,
        "change_events": 3,
        "counts_by_type": {
            "PRICE_CHANGED": 1,
            "PRODUCT_ADDED": 1,
            "PRODUCT_REMOVED": 1,
        },
    }
    assert not [event for event in events if event["cn"] == "345678"]
    price = next(event for event in events if event["change_type"] == "PRICE_CHANGED")
    assert price["before"] == "10"
    assert price["after"] == "9.5"


def test_complete_diff_matches_human_readable_golden_fixture():
    before, _ = parse_csv(FIXTURES / "2026-07.csv", "2026-07")
    after, _ = parse_csv(FIXTURES / "2026-08.csv", "2026-08")
    events, summary = diff_snapshots(before, after, "2026-07", "2026-08")
    expected = json.loads(
        (FIXTURES / "expected-2026-07_to_2026-08.json").read_text(encoding="utf-8")
    )
    assert {"events": events, "summary": summary} == expected
