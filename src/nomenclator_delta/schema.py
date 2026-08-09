from __future__ import annotations

from dataclasses import dataclass


SCHEMA_VERSION = 1
PARSER_VERSION = "1"

SOURCE_HEADERS = (
    "Código Nacional",
    "Nombre del producto farmacéutico",
    "Tipo de fármaco",
    "Nombre genérico efecto y accesorio",
    "Código del laboratorio ofertante",
    "Nombre del laboratorio ofertante",
    "Estado",
    "Fecha de alta en el nomenclátor",
    "Fecha de baja en el nomenclátor",
    "Aportación del beneficiario",
    "Principio activo o asociación de principios activos",
    "Precio venta al público con IVA",
    "Precio de referencia",
    "Menor precio de la agrupación homogénea del producto sanitario",
    "Código de la agrupación homogénea del producto sanitario",
    "Nombre de la agrupación homogénea del producto sanitario",
    "Diagnóstico hospitalario",
    "Tratamiento de larga duración",
    "Especial control médico",
    "Medicamento huérfano",
)

# Known labels from the legacy XLS export. Keeping them here makes a future XLS
# adapter possible without weakening CSV header validation.
HEADER_ALIASES = {
    "Precio de venta al público con IVA": "Precio venta al público con IVA",
    "Menor precio de la agrupación homogéna del producto sanitario":
        "Menor precio de la agrupación homogénea del producto sanitario",
    "Código de la agrupación homegénea del productor sanitario":
        "Código de la agrupación homogénea del producto sanitario",
}


@dataclass(frozen=True)
class DiffField:
    path: str
    change_type: str
    label_es: str


DIFF_FIELDS = (
    DiffField("medicine_name", "NAME_CHANGED", "Nombre del producto farmacéutico"),
    DiffField("drug_type", "PRODUCT_TYPE_CHANGED", "Tipo de fármaco"),
    DiffField("generic_product_name", "GENERIC_NAME_CHANGED", "Nombre genérico"),
    DiffField("laboratory", "LABORATORY_CHANGED", "Laboratorio ofertante"),
    DiffField("status", "STATUS_CHANGED", "Estado"),
    DiffField("listed_from", "LISTING_DATE_CHANGED", "Fecha de alta en el nomenclátor"),
    DiffField("listed_until", "REMOVAL_DATE_CHANGED", "Fecha de baja en el nomenclátor"),
    DiffField("contribution", "CONTRIBUTION_CHANGED", "Aportación del beneficiario"),
    DiffField("active_ingredients", "ACTIVE_INGREDIENT_CHANGED", "Principio activo"),
    DiffField("prices.retail_with_vat", "PRICE_CHANGED", "Precio de venta al público con IVA"),
    DiffField("prices.reference", "PRICE_CHANGED", "Precio de referencia"),
    DiffField(
        "prices.homogeneous_group_minimum",
        "PRICE_CHANGED",
        "Menor precio de la agrupación homogénea",
    ),
    DiffField("homogeneous_group", "HOMOGENEOUS_GROUP_CHANGED", "Agrupación homogénea"),
    DiffField("flags.hospital_diagnosis", "HOSPITAL_DIAGNOSIS_CHANGED", "Diagnóstico hospitalario"),
    DiffField("flags.long_term_treatment", "LONG_TERM_TREATMENT_CHANGED", "Tratamiento de larga duración"),
    DiffField("flags.special_medical_control", "SPECIAL_CONTROL_CHANGED", "Especial control médico"),
    DiffField("flags.orphan_medicine", "ORPHAN_STATUS_CHANGED", "Medicamento huérfano"),
)

CHANGE_LABELS_ES = {
    "PRODUCT_ADDED": "Alta en la comparación",
    "PRODUCT_REMOVED": "Baja en la comparación",
    "NAME_CHANGED": "Cambio de nombre",
    "PRODUCT_TYPE_CHANGED": "Cambio de tipo de fármaco",
    "GENERIC_NAME_CHANGED": "Cambio de nombre genérico",
    "LABORATORY_CHANGED": "Cambio de laboratorio",
    "STATUS_CHANGED": "Cambio de estado",
    "LISTING_DATE_CHANGED": "Cambio de fecha de alta",
    "REMOVAL_DATE_CHANGED": "Cambio de fecha de baja",
    "CONTRIBUTION_CHANGED": "Cambio de aportación",
    "ACTIVE_INGREDIENT_CHANGED": "Cambio de principio activo",
    "PRICE_CHANGED": "Cambio de precio",
    "HOMOGENEOUS_GROUP_CHANGED": "Cambio de agrupación homogénea",
    "HOSPITAL_DIAGNOSIS_CHANGED": "Cambio de diagnóstico hospitalario",
    "LONG_TERM_TREATMENT_CHANGED": "Cambio de tratamiento de larga duración",
    "SPECIAL_CONTROL_CHANGED": "Cambio de control médico especial",
    "ORPHAN_STATUS_CHANGED": "Cambio de condición de medicamento huérfano",
}
