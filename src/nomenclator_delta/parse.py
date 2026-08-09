from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from nomenclator_delta.normalize import normalize_record
from nomenclator_delta.schema import HEADER_ALIASES, SOURCE_HEADERS


class SourceSchemaError(ValueError):
    """Raised when the official export schema cannot be parsed safely."""


def parse_csv(path: Path, snapshot: str) -> tuple[list[dict[str, Any]], list[str]]:
    products: list[dict[str, Any]] = []
    warnings: list[str] = []
    seen: set[str] = set()
    unknown_flags: set[tuple[str, str]] = set()

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        raw_headers = reader.fieldnames or []
        canonical_headers = [HEADER_ALIASES.get(header, header) for header in raw_headers]
        missing = sorted(set(SOURCE_HEADERS) - set(canonical_headers))
        unknown = sorted(set(canonical_headers) - set(SOURCE_HEADERS))
        if missing:
            raise SourceSchemaError(f"missing expected source columns: {missing}")
        if unknown:
            warnings.append(f"unexpected source columns preserved: {unknown}")

        for source_row, raw_row in enumerate(reader, start=2):
            row = {
                HEADER_ALIASES.get(key, key): value
                for key, value in raw_row.items()
                if key is not None
            }
            try:
                product = normalize_record(row, snapshot, source_row)
            except (KeyError, ValueError) as exc:
                raise SourceSchemaError(f"row {source_row}: {exc}") from exc
            cn = product["codigo_nacional"]
            if cn in seen:
                raise SourceSchemaError(f"row {source_row}: duplicate Código Nacional {cn}")
            seen.add(cn)
            extras = {
                key: value
                for key, value in row.items()
                if key not in SOURCE_HEADERS and value not in (None, "")
            }
            if extras:
                product["extra_source_fields"] = extras
            for header in (
                "Diagnóstico hospitalario",
                "Tratamiento de larga duración",
                "Especial control médico",
                "Medicamento huérfano",
            ):
                flag = (row.get(header) or "").strip()
                if flag and flag.upper() not in {"SI", "NO"}:
                    unknown_flags.add((header, flag))
            products.append(product)

    products.sort(key=lambda product: product["codigo_nacional"])
    warnings.extend(
        f"unexpected flag value preserved in {header}: {value!r}"
        for header, value in sorted(unknown_flags)
    )
    return products, warnings
