from difflib import SequenceMatcher

from .models import DataImport, DataImportColumn
from .utils import (
    normalize_column_name,
    normalize_field_name,
)


# ============================================================
# Field aliases
# ============================================================

FIELD_ALIASES = {
    "employee": {
        "employee_number": [
            "employee number",
            "employee #",
            "employee no",
            "employee num",
            "employee id",
            "emp number",
            "emp #",
            "emp no",
            "emp id",
            "emp num",
            "employee",
        ],
        "first_name": [
            "first",
            "first name",
            "firstname",
            "given name",
            "given",
        ],
        "last_name": [
            "last",
            "last name",
            "lastname",
            "surname",
            "family name",
        ],
        "phone_number": [
            "phone",
            "phone number",
            "mobile",
            "mobile number",
            "cell",
            "cell phone",
            "cell number",
            "telephone",
            "telephone number",
        ],
        "email": [
            "email",
            "email address",
            "e mail",
            "e-mail",
        ],
        "position": [
            "position",
            "job",
            "job title",
            "title",
            "occupation",
            "role",
        ],
        "department": [
            "department",
            "dept",
            "division",
        ],
        "group": [
            "group",
            "team",
            "crew",
        ],
        "callsign": [
            "callsign",
            "call sign",
            "radio callsign",
            "radio call sign",
        ],
        "date_hired": [
            "date hired",
            "hire date",
            "date hired",
            "hired date",
            "start date",
            "employment date",
        ],
    },

    "equipment": {
        "name": [
            "name",
            "equipment name",
            "equipment",
            "description",
        ],
        "serial_number": [
            "serial number",
            "serial #",
            "serial no",
            "serial",
            "sn",
        ],
        "model": [
            "model",
            "model number",
            "model #",
        ],
        "manufacturer": [
            "manufacturer",
            "make",
            "brand",
        ],
    },

    "location": {
        "name": [
            "name",
            "location",
            "location name",
            "location description",
        ],
        "address": [
            "address",
            "street",
            "street address",
            "address 1",
            "address line 1",
        ],
        "city": [
            "city",
            "town",
        ],
        "state": [
            "state",
            "state/province",
            "province",
        ],
        "zip_code": [
            "zip",
            "zip code",
            "zipcode",
            "postal code",
            "postal",
        ],
    },

    "customer": {
        "name": [
            "name",
            "customer",
            "customer name",
            "customer company",
            "company",
            "company name",
        ],
        "first_name": [
            "first",
            "first name",
            "firstname",
            "given name",
        ],
        "last_name": [
            "last",
            "last name",
            "lastname",
            "surname",
            "family name",
        ],
        "phone": [
            "phone",
            "phone number",
            "mobile",
            "mobile number",
            "cell",
            "telephone",
        ],
        "email": [
            "email",
            "email address",
            "e-mail",
        ],
    },
}


# ============================================================
# Target field information
# ============================================================

def get_target_fields(target_model):
    """
    Return importable fields from a Django model.

    Automatically generated and reverse-relation fields are
    excluded.
    """

    fields = []

    for field in target_model._meta.get_fields():

        if field.auto_created:
            continue

        if field.many_to_many:
            continue

        if field.one_to_many:
            continue

        if field.primary_key:
            continue

        if getattr(
            field,
            "auto_now",
            False,
        ):
            continue

        if getattr(
            field,
            "auto_now_add",
            False,
        ):
            continue

        fields.append(field)

    return fields


# ============================================================
# Alias lookup
# ============================================================

def get_aliases_for_field(
    target_model_name,
    field_name,
):
    """
    Return known aliases for a target field.
    """

    model_name = (
        str(target_model_name)
        .strip()
        .lower()
    )

    aliases = FIELD_ALIASES.get(
        model_name,
        {},
    )

    field_aliases = aliases.get(
        field_name,
        [],
    )

    return {
        normalize_column_name(alias)
        for alias in field_aliases
    }


# ============================================================
# Exact matching
# ============================================================

def exact_match(
    source_column,
    target_fields,
):
    """
    Look for an exact normalized match between a source
    column and a Django field name.
    """

    normalized_source = normalize_column_name(
        source_column
    )

    for field in target_fields:

        normalized_field = normalize_column_name(
            field.name
        )

        if normalized_source == normalized_field:

            return {
                "field": field,
                "confidence": 1.0,
                "match_type": "exact",
            }

    return None


# ============================================================
# Alias matching
# ============================================================

def alias_match(
    source_column,
    target_model_name,
    target_fields,
):
    """
    Match a source column against known aliases.
    """

    normalized_source = normalize_column_name(
        source_column
    )

    matches = []

    for field in target_fields:

        aliases = get_aliases_for_field(
            target_model_name,
            field.name,
        )

        if normalized_source in aliases:

            matches.append(
                {
                    "field": field,
                    "confidence": 0.95,
                    "match_type": "alias",
                }
            )

    if len(matches) == 1:
        return matches[0]

    return None


# ============================================================
# Fuzzy matching
# ============================================================

def similarity_score(
    source_column,
    target_field_name,
):
    """
    Calculate a normalized similarity score between a source
    column and target field.
    """

    source = normalize_column_name(
        source_column
    )

    target = normalize_column_name(
        target_field_name
    )

    if not source or not target:
        return 0.0

    return SequenceMatcher(
        None,
        source,
        target,
    ).ratio()


def fuzzy_match(
    source_column,
    target_model_name,
    target_fields,
    threshold=0.75,
):
    """
    Find the best fuzzy target-field match.

    A match is only returned when the score meets the
    threshold.
    """

    candidates = []

    for field in target_fields:

        score = similarity_score(
            source_column,
            field.name,
        )

        # Also compare against aliases.
        aliases = get_aliases_for_field(
            target_model_name,
            field.name,
        )

        for alias in aliases:

            alias_score = SequenceMatcher(
                None,
                normalize_column_name(
                    source_column
                ),
                alias,
            ).ratio()

            score = max(
                score,
                alias_score,
            )

        candidates.append(
            {
                "field": field,
                "confidence": score,
                "match_type": "fuzzy",
            }
        )

    candidates.sort(
        key=lambda item: item["confidence"],
        reverse=True,
    )

    if not candidates:
        return None

    best = candidates[0]

    if best["confidence"] < threshold:
        return None

    return best


# ============================================================
# Automatic matching
# ============================================================

def match_source_column(
    source_column,
    target_model,
):
    """
    Attempt to automatically match one source column to a
    Django model field.

    Matching order:

        1. Exact
        2. Alias
        3. Fuzzy
        4. Unmapped
    """

    target_fields = get_target_fields(
        target_model
    )

    target_model_name = (
        target_model.__name__.lower()
    )

    # --------------------------------------------------------
    # Exact match
    # --------------------------------------------------------

    result = exact_match(
        source_column,
        target_fields,
    )

    if result:
        return result

    # --------------------------------------------------------
    # Alias match
    # --------------------------------------------------------

    result = alias_match(
        source_column,
        target_model_name,
        target_fields,
    )

    if result:
        return result

    # --------------------------------------------------------
    # Fuzzy match
    # --------------------------------------------------------

    result = fuzzy_match(
        source_column,
        target_model_name,
        target_fields,
    )

    if result:
        return result

    # --------------------------------------------------------
    # No match
    # --------------------------------------------------------

    return {
        "field": None,
        "confidence": 0.0,
        "match_type": "unmapped",
    }


# ============================================================
# Match all source columns
# ============================================================

def auto_map_columns(
    source_columns,
    target_model,
):
    """
    Automatically map all source columns to target model
    fields.

    Returns a list such as:

        [
            {
                "source_column": "Emp #",
                "target_field": "employee_number",
                "confidence": 0.95,
                "match_type": "alias",
            },
            ...
        ]
    """

    mappings = []

    for source_column in source_columns:

        result = match_source_column(
            source_column,
            target_model,
        )

        field = result.get(
            "field"
        )

        mappings.append(
            {
                "source_column": source_column,
                "target_field": (
                    field.name
                    if field
                    else ""
                ),
                "confidence": result.get(
                    "confidence",
                    0.0,
                ),
                "match_type": result.get(
                    "match_type",
                    "unmapped",
                ),
                "is_mapped": bool(field),
            }
        )

    return mappings


# ============================================================
# Required field detection
# ============================================================

def get_required_fields(target_model):
    """
    Return model fields that appear to be required for import.

    Primary keys and automatically generated fields are
    excluded.
    """

    required_fields = []

    for field in get_target_fields(
        target_model
    ):

        if getattr(
            field,
            "blank",
            False,
        ):
            continue

        if field.null:
            continue

        if field.has_default():
            continue

        if field.name in {
            "created_at",
            "updated_at",
        }:
            continue

        required_fields.append(
            field
        )

    return required_fields


def mark_required_mappings(
    mappings,
    target_model,
):
    """
    Mark automatically detected mappings as required when
    their target Django field is required.
    """

    required_fields = {
        field.name
        for field in get_required_fields(
            target_model
        )
    }

    for mapping in mappings:

        mapping["is_required"] = (
            mapping["target_field"]
            in required_fields
        )

    return mappings


# ============================================================
# Prevent duplicate target mappings
# ============================================================

def resolve_duplicate_target_mappings(
    mappings,
):
    """
    Prevent multiple source columns from automatically
    mapping to the same target field.

    The highest-confidence mapping wins.
    """

    grouped = {}

    for mapping in mappings:

        target_field = mapping.get(
            "target_field"
        )

        if not target_field:
            continue

        grouped.setdefault(
            target_field,
            [],
        ).append(mapping)

    for target_field, candidates in grouped.items():

        if len(candidates) <= 1:
            continue

        candidates.sort(
            key=lambda item: item.get(
                "confidence",
                0,
            ),
            reverse=True,
        )

        # Keep the strongest match.
        winner = candidates[0]

        for mapping in candidates[1:]:

            mapping["target_field"] = ""
            mapping["is_mapped"] = False
            mapping["match_type"] = (
                "duplicate"
            )
            mapping["confidence"] = 0.0

        winner["match_type"] = (
            winner.get(
                "match_type",
                "automatic",
            )
        )

    return mappings


# ============================================================
# Complete automatic mapping
# ============================================================

def generate_mappings(
    source_columns,
    target_model,
):
    """
    Generate the complete automatic mapping configuration.
    """

    mappings = auto_map_columns(
        source_columns,
        target_model,
    )

    mappings = mark_required_mappings(
        mappings,
        target_model,
    )

    mappings = resolve_duplicate_target_mappings(
        mappings
    )

    for index, mapping in enumerate(
        mappings
    ):
        mapping["column_order"] = index

    return mappings


# ============================================================
# Mapping summary
# ============================================================

def mapping_summary(mappings):
    """
    Return summary information for the mapping screen.
    """

    total = len(mappings)

    mapped = sum(
        1
        for mapping in mappings
        if mapping.get("is_mapped")
    )

    unmapped = total - mapped

    high_confidence = sum(
        1
        for mapping in mappings
        if (
            mapping.get("is_mapped")
            and mapping.get("confidence", 0)
            >= 0.90
        )
    )

    review_required = sum(
        1
        for mapping in mappings
        if (
            mapping.get("is_mapped")
            and mapping.get("confidence", 0)
            < 0.90
        )
    )

    required_unmapped = sum(
        1
        for mapping in mappings
        if (
            mapping.get("is_required")
            and not mapping.get("is_mapped")
        )
    )

    return {
        "total": total,
        "mapped": mapped,
        "unmapped": unmapped,
        "high_confidence": high_confidence,
        "review_required": review_required,
        "required_unmapped": required_unmapped,
        "ready": (
            total > 0
            and required_unmapped == 0
        ),
    }


# ============================================================
# Save generated mappings
# ============================================================

def save_mappings(
    data_import,
    mappings,
):
    """
    Persist automatically generated mappings to the
    DataImportColumn table.

    Existing mappings for this import are replaced.
    """

    DataImportColumn.objects.filter(
        data_import=data_import
    ).delete()

    objects = []

    for index, mapping in enumerate(
        mappings
    ):

        objects.append(
            DataImportColumn(
                data_import=data_import,
                source_column=mapping[
                    "source_column"
                ],
                target_field=mapping.get(
                    "target_field",
                    "",
                ),
                column_order=mapping.get(
                    "column_order",
                    index,
                ),
                is_required=mapping.get(
                    "is_required",
                    False,
                ),
                is_mapped=mapping.get(
                    "is_mapped",
                    False,
                ),
            )
        )

    DataImportColumn.objects.bulk_create(
        objects
    )

    return list(
        DataImportColumn.objects
        .filter(data_import=data_import)
        .order_by("column_order")
    )