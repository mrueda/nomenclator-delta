from pathlib import Path

from nomenclator_delta.build import build_comparison
from nomenclator_delta.validate import validate_dataset


FIXTURES = Path(__file__).parent / "fixtures"


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
