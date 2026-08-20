import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation


# ============================================================
# General value helpers
# ============================================================

def is_empty(value):
    """
    Determine whether an imported value should be considered
    empty.
    """

    if value is None:
        return True

    if isinstance(value, str):
        return not value.strip()

    return False


def clean_value(value):
    """
    Clean a value coming from an imported file.
    """

    if value is None:
        return None

    if isinstance(value, str):
        value = value.strip()

        if not value:
            return None

    return value


def normalize_text(value):
    """
    Normalize text for comparisons.

    Example:

        "  Employee Number  "
        -> "employee number"
    """

    if value is None:
        return ""

    return " ".join(
        str(value).strip().lower().split()
    )


# ============================================================
# Column helpers
# ============================================================

def normalize_column_name(value):
    """
    Normalize a source column name for matching.

    Examples:

        "Employee Number" -> "employee number"
        "Employee_Number" -> "employee number"
        "Emp #"           -> "emp"
    """

    if value is None:
        return ""

    value = str(value).strip().lower()

    # Replace underscores and hyphens with spaces.
    value = value.replace("_", " ")
    value = value.replace("-", " ")

    # Remove punctuation.
    value = re.sub(
        r"[^a-z0-9\s]",
        " ",
        value,
    )

    # Collapse whitespace.
    value = " ".join(
        value.split()
    )

    return value


def normalize_field_name(value):
    """
    Normalize a Django target field name.

    Example:

        "Employee Number"
        -> "employee_number"
    """

    if value is None:
        return ""

    value = str(value).strip().lower()

    value = re.sub(
        r"[^a-z0-9]+",
        "_",
        value,
    )

    return value.strip("_")


# ============================================================
# Number helpers
# ============================================================

def clean_number(value):
    """
    Convert an imported number to a Decimal.

    Handles common values such as:

        "$1,250.00"
        "1,250"
        "1250.00"
        " 1250 "
    """

    if is_empty(value):
        return None

    if isinstance(value, Decimal):
        return value

    if isinstance(value, (int, float)):
        return Decimal(
            str(value)
        )

    value = str(value).strip()

    # Remove common formatting.
    value = value.replace(
        ",",
        "",
    )

    value = value.replace(
        "$",
        "",
    )

    value = value.replace(
        "%",
        "",
    )

    try:

        return Decimal(value)

    except InvalidOperation:

        raise ValueError(
            f"Invalid numeric value: {value}"
        )


# ============================================================
# Integer helpers
# ============================================================

def clean_integer(value):
    """
    Convert a value to an integer.
    """

    if is_empty(value):
        return None

    if isinstance(value, bool):
        return int(value)

    try:

        return int(
            float(
                str(value).replace(
                    ",",
                    "",
                ).strip()
            )
        )

    except (ValueError, TypeError):

        raise ValueError(
            f"Invalid integer value: {value}"
        )


# ============================================================
# Boolean helpers
# ============================================================

TRUE_VALUES = {
    "true",
    "yes",
    "y",
    "1",
    "on",
}

FALSE_VALUES = {
    "false",
    "no",
    "n",
    "0",
    "off",
}


def clean_boolean(value):
    """
    Convert common imported boolean values to True/False.
    """

    if is_empty(value):
        return None

    if isinstance(value, bool):
        return value

    normalized = (
        str(value)
        .strip()
        .lower()
    )

    if normalized in TRUE_VALUES:
        return True

    if normalized in FALSE_VALUES:
        return False

    raise ValueError(
        f"Invalid boolean value: {value}"
    )


# ============================================================
# Date helpers
# ============================================================

DATE_FORMATS = [
    "%Y-%m-%d",
    "%m/%d/%Y",
    "%m/%d/%y",
    "%m-%d-%Y",
    "%m-%d-%y",
    "%Y/%m/%d",
    "%B %d, %Y",
    "%b %d, %Y",
]


def clean_date(value):
    """
    Convert a common imported date value into a Python date.

    Supports:

        2026-08-19
        08/19/2026
        08-19-2026
        August 19, 2026
        Excel datetime/date values
    """

    if is_empty(value):
        return None

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    value = str(value).strip()

    for date_format in DATE_FORMATS:

        try:

            return datetime.strptime(
                value,
                date_format,
            ).date()

        except ValueError:
            continue

    raise ValueError(
        f"Invalid date value: {value}"
    )


# ============================================================
# DateTime helpers
# ============================================================

DATETIME_FORMATS = [
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%m/%d/%Y %H:%M:%S",
    "%m/%d/%Y %H:%M",
    "%m/%d/%y %H:%M",
]


def clean_datetime(value):
    """
    Convert an imported value into a Python datetime.
    """

    if is_empty(value):
        return None

    if isinstance(value, datetime):
        return value

    if isinstance(value, date):
        return datetime.combine(
            value,
            datetime.min.time(),
        )

    value = str(value).strip()

    for datetime_format in DATETIME_FORMATS:

        try:

            return datetime.strptime(
                value,
                datetime_format,
            )

        except ValueError:
            continue

    try:

        return datetime.fromisoformat(
            value
        )

    except ValueError:

        raise ValueError(
            f"Invalid datetime value: {value}"
        )


# ============================================================
# Phone helpers
# ============================================================

def clean_phone(value):
    """
    Normalize a phone number while preserving the digits.

    Example:

        (775) 555-1234
        -> 7755551234
    """

    if is_empty(value):
        return None

    value = str(value).strip()

    # Preserve a leading + for international numbers.
    if value.startswith("+"):
        return "+" + re.sub(
            r"\D",
            "",
            value,
        )

    return re.sub(
        r"\D",
        "",
        value,
    )


# ============================================================
# Email helpers
# ============================================================

EMAIL_PATTERN = re.compile(
    r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
)


def is_valid_email(value):
    """
    Basic email validation.
    """

    if is_empty(value):
        return False

    return bool(
        EMAIL_PATTERN.match(
            str(value).strip()
        )
    )


def clean_email(value):
    """
    Normalize an email address.
    """

    if is_empty(value):
        return None

    value = str(value).strip().lower()

    if not is_valid_email(value):

        raise ValueError(
            f"Invalid email address: {value}"
        )

    return value


# ============================================================
# Identifier helpers
# ============================================================

def clean_identifier(value):
    """
    Normalize business identifiers such as:

        EMP-001
        emp001
        EMP 001
    """

    if is_empty(value):
        return None

    value = str(value).strip().upper()

    return value


# ============================================================
# Row helpers
# ============================================================

def row_is_empty(row):
    """
    Determine whether an imported row contains any data.
    """

    if not row:
        return True

    return not any(
        not is_empty(value)
        for value in row.values()
    )


def clean_row(row):
    """
    Clean all values in an imported row.
    """

    if not row:
        return {}

    return {
        key: clean_value(value)
        for key, value in row.items()
    }


# ============================================================
# Mapping helpers
# ============================================================

def build_mapping_dict(mappings):
    """
    Convert DataImportColumn objects into a simple dictionary.

    Example:

        {
            "Emp #": "employee_number",
            "First": "first_name",
            "Last": "last_name",
        }
    """

    mapping_dict = {}

    for mapping in mappings:

        if not mapping.is_mapped:
            continue

        source_column = mapping.source_column

        target_field = mapping.target_field

        if not source_column or not target_field:
            continue

        mapping_dict[
            source_column
        ] = target_field

    return mapping_dict


def apply_mapping(row, mappings):
    """
    Convert a source row into a target-field dictionary.

    Example:

        Source:

        {
            "Emp #": "EMP001",
            "First": "John",
            "Last": "Smith",
        }

        Result:

        {
            "employee_number": "EMP001",
            "first_name": "John",
            "last_name": "Smith",
        }
    """

    mapped_row = {}

    for mapping in mappings:

        if not mapping.is_mapped:
            continue

        source_column = mapping.source_column
        target_field = mapping.target_field

        if not source_column or not target_field:
            continue

        mapped_row[target_field] = clean_value(
            row.get(source_column)
        )

    return mapped_row


# ============================================================
# Duplicate helpers
# ============================================================

def make_row_signature(row, fields):
    """
    Create a deterministic signature for a row.

    Useful for detecting duplicate rows inside an import.
    """

    values = []

    for field in fields:

        value = row.get(field)

        if isinstance(value, str):
            value = normalize_text(value)

        elif value is None:
            value = ""

        else:
            value = str(value)

        values.append(value)

    return "|".join(values)


# ============================================================
# File helpers
# ============================================================

def get_file_extension(filename):
    """
    Return a normalized file extension.

    Example:

        employees.XLSX -> ".xlsx"
    """

    if not filename:
        return ""

    return (
        "." + filename.rsplit(".", 1)[1].lower()
        if "." in filename
        else ""
    )


def is_supported_file(filename):
    """
    Determine whether a filename has a supported import type.
    """

    supported_extensions = {
        ".csv",
        ".xlsx",
        ".xls",
        ".dat",
    }

    return (
        get_file_extension(filename)
        in supported_extensions
    )


# ============================================================
# Validation summary
# ============================================================

def build_validation_summary(validation_result):
    """
    Build a simple summary suitable for templates.
    """

    total_rows = validation_result.get(
        "total_rows",
        0,
    )

    valid_rows = validation_result.get(
        "valid_rows",
        0,
    )

    error_rows = validation_result.get(
        "error_rows",
        0,
    )

    warning_count = validation_result.get(
        "warning_count",
        0,
    )

    return {
        "total_rows": total_rows,
        "valid_rows": valid_rows,
        "error_rows": error_rows,
        "warning_count": warning_count,
        "has_errors": error_rows > 0,
        "has_warnings": warning_count > 0,
        "ready": (
            total_rows > 0
            and error_rows == 0
        ),
    }

