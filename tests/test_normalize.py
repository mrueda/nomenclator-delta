from nomenclator_delta.normalize import (
    normalize_cn,
    normalize_date,
    normalize_decimal,
    normalize_flag,
    normalize_ingredients,
    normalize_text,
)


def test_normalization_rules_are_conservative_and_deterministic():
    assert normalize_text("  LABORATORIO   UNO ") == "LABORATORIO UNO"
    assert normalize_cn("123456") == "123456"
    assert normalize_date("01/08/2026") == "2026-08-01"
    assert normalize_decimal("10.00") == "10"
    assert normalize_decimal(".28") == "0.28"
    assert normalize_flag("SI") is True
    assert normalize_flag("NO") is False
    assert normalize_flag("PENDIENTE") == "PENDIENTE"
    assert normalize_ingredients(" BETA, ALFA, BETA ") == ["ALFA", "BETA"]


def test_invalid_cn_is_rejected():
    try:
        normalize_cn("12345")
    except ValueError as error:
        assert "Código Nacional" in str(error)
    else:
        raise AssertionError("invalid CN was accepted")
