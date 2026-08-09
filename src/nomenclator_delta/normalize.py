from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any


CN_RE = re.compile(r"^\d{6}$")


def normalize_text(value: Any) -> str | None:
    if value is None:
        return None
    text = " ".join(str(value).strip().split())
    return text or None


def normalize_cn(value: Any) -> str:
    cn = normalize_text(value) or ""
    if not CN_RE.fullmatch(cn):
        raise ValueError(f"invalid Código Nacional: {value!r}")
    return cn


def normalize_date(value: Any) -> str | None:
    text = normalize_text(value)
    if text is None:
        return None
    try:
        return datetime.strptime(text, "%d/%m/%Y").date().isoformat()
    except ValueError as exc:
        raise ValueError(f"invalid Nomenclátor date: {text!r}") from exc


def normalize_decimal(value: Any) -> str | None:
    text = normalize_text(value)
    if text is None:
        return None
    try:
        decimal = Decimal(text.replace(",", "."))
    except InvalidOperation as exc:
        raise ValueError(f"invalid price: {text!r}") from exc
    normalized = format(decimal, "f").rstrip("0").rstrip(".")
    return normalized or "0"


def normalize_flag(value: Any) -> bool | str | None:
    text = normalize_text(value)
    if text is None:
        return None
    upper = text.upper()
    if upper == "SI":
        return True
    if upper == "NO":
        return False
    return text


def normalize_ingredients(value: Any) -> list[str]:
    text = normalize_text(value)
    if text is None:
        return []
    return sorted({part.strip() for part in text.split(",") if part.strip()})


def normalize_record(row: dict[str, str], snapshot: str, source_row: int) -> dict[str, Any]:
    return {
        "codigo_nacional": normalize_cn(row["Código Nacional"]),
        "medicine_name": normalize_text(row["Nombre del producto farmacéutico"]),
        "drug_type": normalize_text(row["Tipo de fármaco"]),
        "generic_product_name": normalize_text(row["Nombre genérico efecto y accesorio"]),
        "laboratory": {
            "code": normalize_text(row["Código del laboratorio ofertante"]),
            "name": normalize_text(row["Nombre del laboratorio ofertante"]),
        },
        "status": normalize_text(row["Estado"]),
        "listed_from": normalize_date(row["Fecha de alta en el nomenclátor"]),
        "listed_until": normalize_date(row["Fecha de baja en el nomenclátor"]),
        "contribution": normalize_text(row["Aportación del beneficiario"]),
        "active_ingredients": normalize_ingredients(
            row["Principio activo o asociación de principios activos"]
        ),
        "prices": {
            "retail_with_vat": normalize_decimal(row["Precio venta al público con IVA"]),
            "reference": normalize_decimal(row["Precio de referencia"]),
            "homogeneous_group_minimum": normalize_decimal(
                row["Menor precio de la agrupación homogénea del producto sanitario"]
            ),
        },
        "homogeneous_group": {
            "code": normalize_text(row["Código de la agrupación homogénea del producto sanitario"]),
            "name": normalize_text(row["Nombre de la agrupación homogénea del producto sanitario"]),
        },
        "flags": {
            "hospital_diagnosis": normalize_flag(row["Diagnóstico hospitalario"]),
            "long_term_treatment": normalize_flag(row["Tratamiento de larga duración"]),
            "special_medical_control": normalize_flag(row["Especial control médico"]),
            "orphan_medicine": normalize_flag(row["Medicamento huérfano"]),
        },
        "source_snapshot": snapshot,
        "source_row": source_row,
    }
