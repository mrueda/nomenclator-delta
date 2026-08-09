from pathlib import Path

import pytest

from nomenclator_delta.parse import SourceSchemaError, parse_csv


FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_csv_uses_cn_identity_and_normalizes_values():
    products, warnings = parse_csv(FIXTURES / "2026-07.csv", "2026-07")
    assert warnings == []
    assert [product["codigo_nacional"] for product in products] == ["123456", "234567", "345678"]
    product = products[0]
    assert product["listed_from"] == "2026-07-01"
    assert product["prices"]["retail_with_vat"] == "10"
    assert product["active_ingredients"] == ["ALFA", "BETA"]
    assert product["flags"]["long_term_treatment"] is True


def test_missing_critical_header_fails(tmp_path):
    path = tmp_path / "broken.csv"
    path.write_text("Código Nacional,Nombre del producto farmacéutico\n123456,TEST\n", encoding="utf-8")
    with pytest.raises(SourceSchemaError, match="missing expected source columns"):
        parse_csv(path, "2026-07")
