from datetime import date, datetime

from django.core.exceptions import ValidationError
from django.db.models import Q

from .models import DataImport, DataImportColumn


# ============================================================
# General helpers
# ============================================================

def is_empty(value):
    """
    Return True when a value should be considered empty.
    """

    if value is None:
        return True

    if isinstance(value, str):
        return not value.strip()

    return False


def normalize_value(value):
    """
    Normalize an imported value for validation and comparison.
    """

    if value is None:
        return ""

    if isinstance(value, str):
        return value.strip()

    return value


def get_model_field(model, field_name):
    """
    Safely retrieve a Django model field.
    """

    try:
        return model._meta.get_field(field_name)
    except Exception:
        return None


# ============================================================
# Required field validation
# ============================================================

def validate_required_fields(row, mappings):
    """
    Validate all required mapped fields.

    Returns a list of error dictionaries.
    """

    errors = []

    for mapping in mappings:

        if not mapping.is_required:
            continue

        value = row.get(mapping.source_column)

        if is_empty(value):

            errors.append({
                "source_column": mapping.source_column,
                "target_field": mapping.target_field,
                "message": (
                    f"{mapping.source_column} is required."
                ),
            })

    return errors


# ============================================================
# Mapping validation
# ============================================================

def validate_mappings(data_import):
    """
    Validate the DataImportColumn configuration.

    This checks that:

    - mappings exist
    - source columns are unique
    - target fields are populated
    - target fields exist on the target model
    """

    errors = []

    mappings = list(
        DataImportColumn.objects
        .filter(data_import=data_import)
        .order_by("column_order")
    )

    if not mappings:
        errors.append({
            "message": "No column mappings have been configured."
        })

        return errors

    target_model = get_target_model(
        data_import.target_model
    )

    if target_model is None:
        errors.append({
            "message": (
                f"Unsupported target model: "
                f"{data_import.target_model}"
            )
        })

        return errors

    source_columns = set()
    target_fields = set()

    for mapping in mappings:

        source_column = mapping.source_column.strip()
        target_field = mapping.target_field.strip()

        # ----------------------------------------------------
        # Source column
        # ----------------------------------------------------

        if not source_column:

            errors.append({
                "message": "A source column cannot be empty."
            })

        elif source_column in source_columns:

            errors.append({
                "source_column": source_column,
                "message": (
                    f"Duplicate source column: "
                    f"{source_column}"
                ),
            })

        else:

            source_columns.add(source_column)

        # ----------------------------------------------------
        # Target field
        # ----------------------------------------------------

        if mapping.is_mapped and not target_field:

            errors.append({
                "source_column": source_column,
                "message": (
                    f"{source_column} does not have "
                    f"a target field."
                ),
            })

            continue

        if not target_field:
            continue

        if target_field in target_fields:

            errors.append({
                "target_field": target_field,
                "message": (
                    f"Target field '{target_field}' "
                    f"is mapped more than once."
                ),
            })

        else:

            target_fields.add(target_field)

        # ----------------------------------------------------
        # Does target field actually exist?
        # ----------------------------------------------------

        field = get_model_field(
            target_model,
            target_field,
        )

        if field is None:

            errors.append({
                "source_column": source_column,
                "target_field": target_field,
                "message": (
                    f"Target field '{target_field}' "
                    f"does not exist on "
                    f"{target_model.__name__}."
                ),
            })

    return errors


# ============================================================
# Target model lookup
# ============================================================

def get_target_model(model_name):
    """
    Resolve a supported Django model from its name.

    Keep this explicit rather than allowing users to import
    arbitrary Django models.
    """

    if not model_name:
        return None

    model_name = model_name.lower().strip()

    # --------------------------------------------------------
    # Import these lazily to avoid circular imports.
    # --------------------------------------------------------

    try:
        from app.models import Employee
    except ImportError:
        Employee = None

    try:
        from app.models import Equipment
    except ImportError:
        Equipment = None

    try:
        from app.models import Location
    except ImportError:
        Location = None

    try:
        from business.models import Customer
    except ImportError:
        Customer = None

    model_map = {}

    if Employee:
        model_map["employee"] = Employee
        model_map["employees"] = Employee

    if Equipment:
        model_map["equipment"] = Equipment

    if Location:
        model_map["location"] = Location
        model_map["locations"] = Location

    if Customer:
        model_map["customer"] = Customer
        model_map["customers"] = Customer

    return model_map.get(model_name)


# ============================================================
# Field type validation
# ============================================================

def validate_field_type(value, field):
    """
    Validate an imported value against a Django model field.

    Returns None when valid, otherwise an error message.
    """

    if is_empty(value):
        return None

    value = normalize_value(value)

    field_class = field.__class__.__name__

    # --------------------------------------------------------
    # Integer fields
    # --------------------------------------------------------

    if field_class in [
        "IntegerField",
        "PositiveIntegerField",
        "PositiveSmallIntegerField",
        "SmallIntegerField",
        "BigIntegerField",
        "PositiveBigIntegerField",
    ]:

        try:
            int(str(value))
        except (TypeError, ValueError):

            return (
                f"Value '{value}' is not a valid "
                f"integer."
            )

    # --------------------------------------------------------
    # Decimal / Float
    # --------------------------------------------------------

    elif field_class in [
        "DecimalField",
        "FloatField",
    ]:

        try:
            float(str(value).replace(",", ""))
        except (TypeError, ValueError):

            return (
                f"Value '{value}' is not a valid "
                f"number."
            )

    # --------------------------------------------------------
    # Boolean
    # --------------------------------------------------------

    elif field_class == "BooleanField":

        valid_values = {
            "true",
            "false",
            "yes",
            "no",
            "1",
            "0",
            "y",
            "n",
        }

        if str(value).lower() not in valid_values:

            return (
                f"Value '{value}' is not a valid "
                f"boolean."
            )

    # --------------------------------------------------------
    # Date
    # --------------------------------------------------------

    elif field_class == "DateField":

        if not isinstance(value, date):

            try:

                datetime.strptime(
                    str(value),
                    "%Y-%m-%d",
                )

            except ValueError:

                return (
                    f"Value '{value}' is not a valid "
                    f"date. Expected YYYY-MM-DD."
                )

    # --------------------------------------------------------
    # DateTime
    # --------------------------------------------------------

    elif field_class == "DateTimeField":

        if not isinstance(value, datetime):

            try:

                datetime.fromisoformat(
                    str(value)
                )

            except ValueError:

                return (
                    f"Value '{value}' is not a valid "
                    f"date/time."
                )

    return None


# ============================================================
# Row validation
# ============================================================

def validate_row(row, data_import, mappings=None):
    """
    Validate one imported row.

    Returns:

    {
        "valid": True/False,
        "errors": [],
        "warnings": [],
    }
    """

    if mappings is None:

        mappings = (
            DataImportColumn.objects
            .filter(data_import=data_import)
            .order_by("column_order")
        )

    mappings = list(mappings)

    errors = []
    warnings = []

    # --------------------------------------------------------
    # Required fields
    # --------------------------------------------------------

    errors.extend(
        validate_required_fields(
            row,
            mappings,
        )
    )

    # --------------------------------------------------------
    # Target model
    # --------------------------------------------------------

    target_model = get_target_model(
        data_import.target_model
    )

    if target_model is None:

        errors.append({
            "message": (
                f"Unsupported target model: "
                f"{data_import.target_model}"
            )
        })

        return {
            "valid": False,
            "errors": errors,
            "warnings": warnings,
        }

    # --------------------------------------------------------
    # Validate individual fields
    # --------------------------------------------------------

    for mapping in mappings:

        if not mapping.is_mapped:
            continue

        source_column = mapping.source_column
        target_field_name = mapping.target_field

        value = row.get(source_column)

        field = get_model_field(
            target_model,
            target_field_name,
        )

        if field is None:

            errors.append({
                "source_column": source_column,
                "target_field": target_field_name,
                "message": (
                    f"Target field '{target_field_name}' "
                    f"does not exist."
                ),
            })

            continue

        error_message = validate_field_type(
            value,
            field,
        )

        if error_message:

            errors.append({
                "source_column": source_column,
                "target_field": target_field_name,
                "value": value,
                "message": error_message,
            })

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }


# ============================================================
# Duplicate detection
# ============================================================

def find_duplicate_employee(
    data_import,
    row,
    mappings=None,
):
    """
    Look for an existing Employee belonging to the same company.

    This intentionally scopes the query to the current company.

    Returns the existing employee or None.
    """

    target_model = get_target_model(
        data_import.target_model
    )

    if target_model is None:
        return None

    if target_model.__name__.lower() != "employee":
        return None

    if mappings is None:

        mappings = (
            DataImportColumn.objects
            .filter(data_import=data_import)
            .order_by("column_order")
        )

    mappings = list(mappings)

    # --------------------------------------------------------
    # Find employee_number mapping
    # --------------------------------------------------------

    employee_number_column = None

    for mapping in mappings:

        if mapping.target_field == "employee_number":

            employee_number_column = mapping.source_column
            break

    if not employee_number_column:
        return None

    employee_number = row.get(
        employee_number_column
    )

    if is_empty(employee_number):
        return None

    employee_number = normalize_value(
        employee_number
    )

    # --------------------------------------------------------
    # Company-scoped lookup
    # --------------------------------------------------------

    if not hasattr(target_model, "company"):
        return None

    return (
        target_model.objects
        .filter(
            company=data_import.company,
            employee_number=employee_number,
        )
        .first()
    )


# ============================================================
# Duplicate rows inside the uploaded file
# ============================================================

def find_duplicate_rows(
    rows,
    mappings,
):
    """
    Find duplicate business identifiers inside the uploaded
    file itself.

    Returns:

    {
        identifier: [row numbers]
    }
    """

    identifier_column = None

    for mapping in mappings:

        if mapping.target_field == "employee_number":

            identifier_column = mapping.source_column
            break

    if not identifier_column:
        return {}

    seen = {}
    duplicates = {}

    for row_number, row in enumerate(
        rows,
        start=1,
    ):

        value = normalize_value(
            row.get(identifier_column)
        )

        if not value:
            continue

        if value in seen:

            duplicates.setdefault(
                value,
                [seen[value]],
            )

            duplicates[value].append(
                row_number
            )

        else:

            seen[value] = row_number

    return duplicates


# ============================================================
# Full import validation
# ============================================================

def validate_import(data_import, rows):
    """
    Validate the complete import.

    This function does not modify the imported target records.

    Returns a structure suitable for validation.html.
    """

    mappings = list(
        DataImportColumn.objects
        .filter(data_import=data_import)
        .order_by("column_order")
    )

    results = []
    valid_rows = 0
    error_rows = 0
    warning_count = 0

    # --------------------------------------------------------
    # Validate mapping first
    # --------------------------------------------------------

    mapping_errors = validate_mappings(
        data_import
    )

    if mapping_errors:

        return {
            "valid": False,
            "total_rows": len(rows),
            "valid_rows": 0,
            "error_rows": len(rows),
            "warning_count": 0,
            "mapping_errors": mapping_errors,
            "rows": [],
        }

    # --------------------------------------------------------
    # Duplicate rows within source file
    # --------------------------------------------------------

    duplicate_rows = find_duplicate_rows(
        rows,
        mappings,
    )

    duplicate_row_numbers = set()

    for row_numbers in duplicate_rows.values():

        duplicate_row_numbers.update(
            row_numbers
        )

    # --------------------------------------------------------
    # Validate each row
    # --------------------------------------------------------

    for row_number, row in enumerate(
        rows,
        start=1,
    ):

        row_result = validate_row(
            row,
            data_import,
            mappings,
        )

        row_errors = row_result["errors"]
        row_warnings = row_result["warnings"]

        # ----------------------------------------------------
        # Duplicate in source file
        # ----------------------------------------------------

        if row_number in duplicate_row_numbers:

            identifier = None

            for mapping in mappings:

                if (
                    mapping.target_field
                    == "employee_number"
                ):

                    identifier = row.get(
                        mapping.source_column
                    )

                    break

            row_errors.append({
                "message": (
                    f"Duplicate employee number "
                    f"'{identifier}' found in "
                    f"the uploaded file."
                )
            })

        # ----------------------------------------------------
        # Existing database record
        # ----------------------------------------------------

        existing_record = find_duplicate_employee(
            data_import,
            row,
            mappings,
        )

        if existing_record:

            row_warnings.append({
                "message": (
                    "An employee with this employee "
                    "number already exists."
                ),
                "existing_id": str(
                    existing_record.pk
                ),
            })

        # ----------------------------------------------------
        # Count results
        # ----------------------------------------------------

        if row_errors:

            error_rows += 1

        else:

            valid_rows += 1

        warning_count += len(
            row_warnings
        )

        results.append({
            "row_number": row_number,
            "data": row,
            "valid": not bool(row_errors),
            "errors": row_errors,
            "warnings": row_warnings,
        })

    return {
        "valid": error_rows == 0,
        "total_rows": len(rows),
        "valid_rows": valid_rows,
        "error_rows": error_rows,
        "warning_count": warning_count,
        "mapping_errors": [],
        "rows": results,
    }


# ============================================================
# Update DataImport validation statistics
# ============================================================

def update_import_validation_status(
    data_import,
    validation_result,
):
    """
    Update DataImport with validation statistics.

    Does not import any records.
    """

    data_import.total_rows = validation_result.get(
        "total_rows",
        0,
    )

    data_import.valid_rows = validation_result.get(
        "valid_rows",
        0,
    )

    data_import.error_rows = validation_result.get(
        "error_rows",
        0,
    )

    if validation_result.get("valid"):

        data_import.status = DataImport.Status.READY

    else:

        data_import.status = DataImport.Status.VALIDATING

    data_import.save(
        update_fields=[
            "total_rows",
            "valid_rows",
            "error_rows",
            "status",
        ]
    )

    return data_import