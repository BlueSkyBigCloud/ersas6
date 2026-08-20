from django.apps import apps
from django.db import transaction

from .models import DataImport, DataImportColumn
from .utils import (
    apply_mapping,
    clean_boolean,
    clean_date,
    clean_datetime,
    clean_email,
    clean_identifier,
    clean_integer,
    clean_number,
    clean_phone,
    clean_value,
)


# ============================================================
# Target model helpers
# ============================================================

SUPPORTED_MODELS = {
    "employee": "Employee",
    "employees": "Employee",
    "equipment": "Equipment",
    "location": "Location",
    "locations": "Location",
    "customer": "Customer",
    "customers": "Customer",
}


def get_target_model(target_model):
    """
    Resolve the target Django model.

    Only models explicitly listed in SUPPORTED_MODELS can be
    imported. This prevents an import file from specifying an
    arbitrary Django model.
    """

    if not target_model:
        raise ValueError(
            "No target model has been specified."
        )

    normalized = (
        str(target_model)
        .strip()
        .lower()
    )

    model_name = SUPPORTED_MODELS.get(
        normalized
    )

    if not model_name:
        raise ValueError(
            f"Unsupported import target: {target_model}"
        )

    # Search installed Django applications for the model.
    for model in apps.get_models():

        if model.__name__.lower() == model_name.lower():
            return model

    raise ValueError(
        f"Unable to locate Django model '{model_name}'."
    )


# ============================================================
# Mapping helpers
# ============================================================

def get_import_mappings(data_import):
    """
    Return the saved column mappings for an import.
    """

    return list(
        DataImportColumn.objects
        .filter(
            data_import=data_import,
            is_mapped=True,
        )
        .order_by("column_order")
    )


# ============================================================
# Field conversion
# ============================================================

def convert_field_value(value, field):
    """
    Convert an imported value into a value appropriate for
    the target Django model field.

    This handles common Django field types before the value
    reaches the model.
    """

    value = clean_value(value)

    if value is None:
        return None

    field_class = field.__class__.__name__

    # --------------------------------------------------------
    # Integer
    # --------------------------------------------------------

    if field_class in {
        "IntegerField",
        "PositiveIntegerField",
        "PositiveSmallIntegerField",
        "SmallIntegerField",
        "BigIntegerField",
        "PositiveBigIntegerField",
    }:
        return clean_integer(value)

    # --------------------------------------------------------
    # Decimal / Float
    # --------------------------------------------------------

    if field_class in {
        "DecimalField",
        "FloatField",
    }:
        return clean_number(value)

    # --------------------------------------------------------
    # Boolean
    # --------------------------------------------------------

    if field_class == "BooleanField":
        return clean_boolean(value)

    # --------------------------------------------------------
    # Date
    # --------------------------------------------------------

    if field_class == "DateField":
        return clean_date(value)

    # --------------------------------------------------------
    # DateTime
    # --------------------------------------------------------

    if field_class == "DateTimeField":
        return clean_datetime(value)

    # --------------------------------------------------------
    # Email
    # --------------------------------------------------------

    if field_class == "EmailField":
        return clean_email(value)

    # --------------------------------------------------------
    # Text / Char fields
    # --------------------------------------------------------

    if field_class in {
        "CharField",
        "TextField",
        "SlugField",
        "URLField",
    }:
        return str(value).strip()

    return value


def prepare_mapped_row(
    row,
    data_import,
    mappings,
    target_model,
):
    """
    Convert a source row into a dictionary containing target
    model field names and correctly converted values.
    """

    mapped_row = apply_mapping(
        row,
        mappings,
    )

    prepared = {}

    for field_name, value in mapped_row.items():

        try:
            field = target_model._meta.get_field(
                field_name
            )

        except Exception:
            raise ValueError(
                f"Target field '{field_name}' does not "
                f"exist on {target_model.__name__}."
            )

        # ----------------------------------------------------
        # Do not allow automatic assignment of these fields.
        # ----------------------------------------------------

        if field.primary_key:
            continue

        if field.auto_created:
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

        prepared[field_name] = convert_field_value(
            value,
            field,
        )

    return prepared


# ============================================================
# Company handling
# ============================================================

def model_has_company(model):
    """
    Determine whether a model contains a company field.
    """

    try:
        model._meta.get_field("company")
        return True

    except Exception:
        return False


def add_company_to_row(
    mapped_row,
    data_import,
    target_model,
):
    """
    Add the current company to a target object when the model
    supports a company ForeignKey.
    """

    if model_has_company(target_model):
        mapped_row["company"] = data_import.company

    return mapped_row


# ============================================================
# Employee duplicate handling
# ============================================================

def find_existing_record(
    target_model,
    mapped_row,
    data_import,
):
    """
    Find an existing record using the model's business
    identifier.

    For V1, Employee uses employee_number.

    The query is always company-scoped when the target model
    contains a company field.
    """

    if target_model.__name__.lower() != "employee":
        return None

    employee_number = mapped_row.get(
        "employee_number"
    )

    if not employee_number:
        return None

    queryset = target_model.objects.all()

    if model_has_company(target_model):
        queryset = queryset.filter(
            company=data_import.company
        )

    return queryset.filter(
        employee_number=employee_number
    ).first()


# ============================================================
# Create one record
# ============================================================

def create_import_record(
    data_import,
    row,
    mappings,
    target_model,
):
    """
    Convert and create one target model record.

    Returns:

        {
            "status": "created",
            "object": object,
        }

    or:

        {
            "status": "skipped",
            "object": existing_object,
        }
    """

    mapped_row = prepare_mapped_row(
        row=row,
        data_import=data_import,
        mappings=mappings,
        target_model=target_model,
    )

    mapped_row = add_company_to_row(
        mapped_row,
        data_import,
        target_model,
    )

    # --------------------------------------------------------
    # Check for existing business record.
    # --------------------------------------------------------

    existing_record = find_existing_record(
        target_model=target_model,
        mapped_row=mapped_row,
        data_import=data_import,
    )

    if existing_record:

        return {
            "status": "skipped",
            "object": existing_record,
        }

    # --------------------------------------------------------
    # Create the record.
    # --------------------------------------------------------

    obj = target_model.objects.create(
        **mapped_row
    )

    return {
        "status": "created",
        "object": obj,
    }


# ============================================================
# Import all rows
# ============================================================

@transaction.atomic
def run_import(
    data_import,
    rows,
):
    """
    Import validated rows into the target Django model.

    This function assumes validation has already occurred.

    It does not read the uploaded file itself.
    """

    if data_import.status != DataImport.Status.READY:
        raise ValueError(
            "This import is not ready to be imported."
        )

    if not rows:
        raise ValueError(
            "There are no rows available to import."
        )

    target_model = get_target_model(
        data_import.target_model
    )

    mappings = get_import_mappings(
        data_import
    )

    if not mappings:
        raise ValueError(
            "No column mappings have been configured."
        )

    # --------------------------------------------------------
    # Set import status.
    # --------------------------------------------------------

    data_import.status = DataImport.Status.IMPORTING

    data_import.save(
        update_fields=["status"]
    )

    validated_count = 0
    skipped_count = 0
    error_count = 0

    created_records = []
    errors = []
    skipped_records = []

    # --------------------------------------------------------
    # Process rows.
    # --------------------------------------------------------

    for row_number, row in enumerate(
        rows,
        start=1,
    ):

        try:

            result = create_import_record(
                data_import=data_import,
                row=row,
                mappings=mappings,
                target_model=target_model,
            )

            if result["status"] == "created":

                validated_count += 1

                created_records.append(
                    result["object"]
                )

            elif result["status"] == "skipped":

                skipped_count += 1

                skipped_records.append({
                    "row_number": row_number,
                    "object": result["object"],
                })

        except Exception as exc:

            error_count += 1

            errors.append({
                "row_number": row_number,
                "message": str(exc),
                "data": row,
            })

    # --------------------------------------------------------
    # Determine final status.
    # --------------------------------------------------------

    if error_count > 0:

        data_import.status = DataImport.Status.FAILED

    else:

        data_import.status = DataImport.Status.COMPLETED

    data_import.valid_rows = validated_count
    data_import.error_rows = error_count

    from django.utils import timezone

    data_import.completed_at = timezone.now()

    data_import.save(
        update_fields=[
            "status",
            "valid_rows",
            "error_rows",
            "completed_at",
        ]
    )

    return {
        "success": error_count == 0,
        "total_rows": len(rows),
        "validated_count": validated_count,
        "skipped_count": skipped_count,
        "error_count": error_count,
        "created_records": created_records,
        "skipped_records": skipped_records,
        "errors": errors,
        "data_import": data_import,
    }


# ============================================================
# Convenience function
# ============================================================

def run_import_from_file(data_import):
    """
    Read the uploaded file and run the import.

    This is a convenience wrapper for callers that don't
    already have the rows in memory.
    """

    from .importers import read_import_rows

    rows = read_import_rows(
        data_import
    )

    return run_import(
        data_import=data_import,
        rows=rows,
    )