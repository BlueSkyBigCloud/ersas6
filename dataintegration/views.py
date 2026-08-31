import os

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST
from .models import *
import logging
from .services import run_import_from_file


logger = logging.getLogger(__name__)

# ============================================================
# Helpers
# ============================================================

def get_company_import(request, import_id):
    """
    Return a DataImport belonging to the currently authenticated
    user's company.

    This is important for multi-company data isolation.
    """

    if not request.user.is_authenticated:
        raise Http404

    return get_object_or_404(
        DataImport,
        id=import_id,
        company=request.user.company,
    )


def detect_source_type(filename):
    """
    Determine the source file type from its extension.
    """

    extension = os.path.splitext(filename)[1].lower()

    if extension == ".csv":
        return DataImport.SourceType.CSV

    if extension == ".xlsx":
        return DataImport.SourceType.XLSX

    if extension == ".xls":
        return DataImport.SourceType.XLS

    if extension == ".dat":
        return DataImport.SourceType.DAT

    return DataImport.SourceType.OTHER


def get_target_model_name(data_import):
    """
    Normalize the target model name.

    Eventually this can be replaced by a registry of supported
    import targets.
    """

    return data_import.target_model.lower().strip()


# ============================================================
# Dashboard
# ============================================================

@login_required
def integration_dashboard(request):
    """
    Main Data Integration dashboard.
    """

    imports = (
        DataImport.objects
        .filter(company=request.user.company)
        .select_related("uploaded_by")
        .order_by("-created_at")
    )

    context = {
        "imports": imports,
        "total_imports": imports.count(),
        "completed_imports": imports.filter(
            status=DataImport.Status.COMPLETED
        ).count(),
        "failed_imports": imports.filter(
            status=DataImport.Status.FAILED
        ).count(),
        "active_imports": imports.exclude(
            status__in=[
                DataImport.Status.COMPLETED,
                DataImport.Status.FAILED,
                DataImport.Status.CANCELLED,
            ]
        ).count(),
    }

    return render(
        request,
        "data_integration/dashboard.html",
        context,
    )


# ============================================================
# Upload
# ============================================================

@login_required
@require_http_methods(["GET", "POST"])
def integration_upload(request):
    """
    Upload a CSV/XLSX/XLS/DAT file and create a DataImport record.
    """

    if request.method == "GET":
        return render(
            request,
            "data_integration/upload.html",
        )

    uploaded_file = request.FILES.get("file")

    if not uploaded_file:
        messages.error(
            request,
            "Please select a file to upload.",
        )

        return render(
            request,
            "data_integration/upload.html",
        )

    filename = uploaded_file.name
    source_type = detect_source_type(filename)

    allowed_types = {
        DataImport.SourceType.CSV,
        DataImport.SourceType.XLSX,
        DataImport.SourceType.XLS,
        DataImport.SourceType.DAT,
    }

    if source_type not in allowed_types:
        messages.error(
            request,
            "Unsupported file type. Please upload a CSV, XLS, XLSX, or DAT file.",
        )

        return render(
            request,
            "data_integration/upload.html",
        )

    try:
        data_import = DataImport.objects.create(
            company=request.user.company,
            uploaded_by=request.user,
            file=uploaded_file,
            filename=filename,
            source_type=source_type,
            target_model="",
            status=DataImport.Status.UPLOADED,
        )

    except Exception as exc:
        messages.error(
            request,
            f"Unable to create import: {exc}",
        )

        return render(
            request,
            "data_integration/upload.html",
        )

    return redirect(
        "dataintegration:integration_analyze",
        import_id=data_import.id,
    )


# ============================================================
# Analyze
# ============================================================
@login_required
@require_http_methods(["GET", "POST"])
def integration_analyze(request, import_id):
    """
    Analyze the uploaded file and determine:

    - column headers
    - total data rows
    - detected target model

    The actual file parsing is handled by importers.py.
    """

    data_import = get_company_import(
        request,
        import_id,
    )

    # --------------------------------------------------------
    # Prevent analysis of completed/cancelled imports
    # --------------------------------------------------------

    if data_import.status in [
        DataImport.Status.COMPLETED,
        DataImport.Status.CANCELLED,
    ]:
        messages.warning(
            request,
            "This import can no longer be analyzed.",
        )

        return redirect(
            "dataintegration:integration_dashboard"
        )

    # --------------------------------------------------------
    # Set status
    # --------------------------------------------------------

    data_import.status = DataImport.Status.ANALYZING

    data_import.save(
        update_fields=["status"]
    )

    try:

        # ----------------------------------------------------
        # Analyze uploaded file
        # ----------------------------------------------------

        from .importers import analyze_import_file

        analysis_data = analyze_import_file(
            data_import
        )

        logger.info(
            "ANALYZE RESULT - import_id=%s analysis_data=%r",
            data_import.id,
            analysis_data,
        )

        # ----------------------------------------------------
        # Validate importer response
        # ----------------------------------------------------

        if not isinstance(
            analysis_data,
            dict,
        ):
            raise ValueError(
                "File analyzer returned an invalid result."
            )

        headers = analysis_data.get(
            "headers",
            [],
        )

        logger.info(
            "ANALYZE HEADERS - import_id=%s headers=%r count=%s",
            data_import.id,
            headers,
            len(headers),
        )

        total_rows = analysis_data.get(
            "total_rows",
            0,
        )

        detected_model = analysis_data.get(
            "detected_model"
        )

        # ----------------------------------------------------
        # Basic validation of analysis results
        # ----------------------------------------------------

        if not isinstance(
            headers,
            list,
        ):
            raise ValueError(
                "File analyzer returned invalid column headers."
            )

        # ----------------------------------------------------
        # Create DataImportColumn records
        # ----------------------------------------------------

        DataImportColumn.objects.filter(
            data_import=data_import
        ).delete()

        column_objects = []

        for column_order, header in enumerate(headers):

            if header is None:
                continue

            header = str(header).strip()

            if not header:
                continue

            column_objects.append(
                DataImportColumn(
                    data_import=data_import,
                    source_column=header,
                    target_field="",
                    column_order=column_order,
                    is_required=False,
                    is_mapped=False,
                )
            )


        DataImportColumn.objects.bulk_create(
            column_objects
        )

        logger.info(
            "ANALYZE COLUMNS CREATED - import_id=%s count=%s",
            data_import.id,
            len(column_objects),
        )

        try:
            total_rows = int(
                total_rows
            )
        except (
            TypeError,
            ValueError,
        ):
            raise ValueError(
                "File analyzer returned an invalid row count."
            )

        if total_rows < 0:
            raise ValueError(
                "File analyzer returned a negative row count."
            )

        # ----------------------------------------------------
        # Save detected model
        # ----------------------------------------------------

        if detected_model:
            data_import.target_model = str(
                detected_model
            ).strip()

        # ----------------------------------------------------
        # Save analysis statistics
        # ----------------------------------------------------

        data_import.total_rows = total_rows

        data_import.status = DataImport.Status.MAPPING

        data_import.save(
            update_fields=[
                "target_model",
                "total_rows",
                "status",
            ]
        )

    except Exception as exc:

        # ----------------------------------------------------
        # Mark import as failed
        # ----------------------------------------------------

        data_import.status = DataImport.Status.FAILED

        data_import.save(
            update_fields=["status"]
        )

        messages.error(
            request,
            f"Unable to analyze the file: {exc}",
        )

        return redirect(
            "dataintegration:integration_dashboard"
        )

    # --------------------------------------------------------
    # Render analysis results
    # --------------------------------------------------------

    context = {
        "data_import": data_import,
        "analysis": analysis_data,
    }

    return render(
        request,
        "data_integration/analyze.html",
        context,
    )



# ============================================================
# Validation
# ============================================================
from .importers import read_import_rows
from .validators import (
    validate_import,
    update_import_validation_status,
)


@login_required
@require_http_methods(["GET", "POST"])
def integration_validate(request, import_id):
    """
    Validate the mapped import before allowing the import operation.
    """

    data_import = get_company_import(
        request,
        import_id,
    )

    mappings = (
        DataImportColumn.objects
        .filter(data_import=data_import)
        .order_by("column_order")
    )

    if not mappings.exists():
        messages.error(
            request,
            "No column mappings have been configured.",
        )

        return redirect(
            "dataintegration:integration_mapping",
            import_id=data_import.id,
        )

    # --------------------------------------------------------
    # Set status to VALIDATING
    # --------------------------------------------------------

    data_import.status = DataImport.Status.VALIDATING

    data_import.save(
        update_fields=["status"]
    )

    try:
        # ----------------------------------------------------
        # Read the uploaded file
        # ----------------------------------------------------

        rows = read_import_rows(
            data_import
        )

        # ----------------------------------------------------
        # Validate the imported rows
        # ----------------------------------------------------

        validation_data = validate_import(
            data_import=data_import,
            rows=rows,
        )

        # ----------------------------------------------------
        # Update DataImport statistics/status
        # ----------------------------------------------------

        update_import_validation_status(
            data_import=data_import,
            validation_result=validation_data,
        )

    except Exception as exc:

        data_import.status = DataImport.Status.FAILED

        data_import.save(
            update_fields=["status"]
        )

        messages.error(
            request,
            f"Validation failed: {exc}",
        )

        return redirect(
            "dataintegration:integration_dashboard"
        )

    # --------------------------------------------------------
    # Refresh the object so the template receives the
    # current validation status/statistics.
    # --------------------------------------------------------

    data_import.refresh_from_db()

    context = {
        "data_import": data_import,
        "mappings": mappings,
        "validation": validation_data,
    }

    return render(
        request,
        "data_integration/validation.html",
        context,
    )


# ============================================================
# Import
# ============================================================

@login_required
@require_http_methods(["GET", "POST"])
def integration_mapping(request, import_id):
    """
    Display and save the column mapping and target model.
    """

    logger.info(
            "MAPPING CHECK - SECOND 222 integration_mapping VIEW "
            "user=%s import_id=%s method=%s",
            request.user.email,
            import_id,
            request.method,
        )

    data_import = get_company_import(
        request,
        import_id,
    )

    # --------------------------------------------------------
    # Verify import is available for mapping
    # --------------------------------------------------------

    if data_import.status not in [
        DataImport.Status.MAPPING,
        DataImport.Status.UPLOADED,
        DataImport.Status.ANALYZING,
    ]:
        messages.warning(
            request,
            "This import is not currently available for mapping.",
        )

        return redirect(
            "dataintegration:integration_dashboard"
        )

    # --------------------------------------------------------
    # Existing mappings
    # --------------------------------------------------------

    columns = (
        DataImportColumn.objects
        .filter(
            data_import=data_import
        )
        .order_by("column_order")
    )

    # --------------------------------------------------------
    # GET
    # --------------------------------------------------------

    if request.method == "GET":

        context = {
            "data_import": data_import,
            "columns": columns,
        }

        return render(
            request,
            "data_integration/mapping.html",
            context,
        )

    # --------------------------------------------------------
    # POST
    # --------------------------------------------------------

    try:

        with transaction.atomic():

            # ------------------------------------------------
            # Target Model
            # ------------------------------------------------

            target_model = request.POST.get(
                "target_model",
                ""
            ).strip()

            if not target_model:

                messages.error(
                    request,
                    "Please select a target model before continuing.",
                )

                return redirect(
                    "dataintegration:integration_mapping",
                    import_id=data_import.id,
                )

            # ------------------------------------------------
            # Save target model
            # ------------------------------------------------

            data_import.target_model = target_model

            # ------------------------------------------------
            # Remove existing mappings
            # ------------------------------------------------

            DataImportColumn.objects.filter(
                data_import=data_import
            ).delete()

            # ------------------------------------------------
            # Recreate mappings
            # ------------------------------------------------

            column_index = 0

            while True:

                source_column = request.POST.get(
                    f"source_column_{column_index}"
                )

                target_field = request.POST.get(
                    f"target_field_{column_index}"
                )

                # No more columns submitted

                if source_column is None:
                    break

                source_column = source_column.strip()

                target_field = (
                    target_field or ""
                ).strip()

                is_required = (
                    request.POST.get(
                        f"is_required_{column_index}"
                    ) == "on"
                )

                # ------------------------------------------------
                # Create mapping
                # ------------------------------------------------

                if source_column:

                    DataImportColumn.objects.create(
                        data_import=data_import,
                        source_column=source_column,
                        target_field=target_field,
                        column_order=column_index,
                        is_required=is_required,
                        is_mapped=bool(
                            target_field
                        ),
                    )

                column_index += 1

            # ------------------------------------------------
            # Make sure at least one field was mapped
            # ------------------------------------------------

            mapped_columns = (
                DataImportColumn.objects
                .filter(
                    data_import=data_import,
                    is_mapped=True,
                )
                .count()
            )

            if mapped_columns == 0:

                raise ValueError(
                    "At least one source column must be mapped "
                    "to a target field."
                )

            # ------------------------------------------------
            # Move import to validation
            # ------------------------------------------------

            data_import.status = (
                DataImport.Status.VALIDATING
            )

            data_import.save(
                update_fields=[
                    "target_model",
                    "status",
                ]
            )

    except Exception as exc:

        messages.error(
            request,
            f"Unable to save the mapping: {exc}",
        )

        return redirect(
            "dataintegration:integration_mapping",
            import_id=data_import.id,
        )

    # --------------------------------------------------------
    # Continue to validation
    # --------------------------------------------------------

    return redirect(
        "dataintegration:integration_validate",
        import_id=data_import.id,
    )


# ============================================================
# Results
# ============================================================

@login_required
def integration_results(request, import_id):
    """
    Display the final result of an import.
    """

    data_import = get_company_import(
        request,
        import_id,
    )

    mappings = (
        DataImportColumn.objects
        .filter(data_import=data_import)
        .order_by("column_order")
    )

    context = {
        "data_import": data_import,
        "mappings": mappings,
    }

    return render(
        request,
        "data_integration/results.html",
        context,
    )


# ============================================================
# Cancel
# ============================================================

@login_required
@require_POST
def integration_cancel(request, import_id):
    """
    Cancel an import that has not completed.
    """

    data_import = get_company_import(
        request,
        import_id,
    )

    if data_import.status in [
        DataImport.Status.COMPLETED,
        DataImport.Status.FAILED,
        DataImport.Status.CANCELLED,
    ]:
        messages.warning(
            request,
            "This import cannot be cancelled.",
        )

        return redirect(
            "dataintegration:integration_dashboard"
        )

    data_import.status = DataImport.Status.CANCELLED

    data_import.save(
        update_fields=["status"]
    )

    messages.success(
        request,
        "Import cancelled.",
    )

    return redirect(
        "dataintegration:integration_dashboard"
    )

from .services import run_import 

@login_required
@require_POST
def integration_import(request, import_id):
    """
    Execute an import that has successfully passed validation.
    """

    logger.info(
        "IMPORT START requested: import_id=%s user_id=%s",
        import_id,
        request.user.id,
    )

    data_import = get_company_import(
        request,
        import_id,
    )

    logger.info(
        "IMPORT START loaded: import_id=%s status=%s",
        data_import.id,
        data_import.status,
    )

    # --------------------------------------------------------
    # Verify import is ready
    # --------------------------------------------------------

    if data_import.status != DataImport.Status.READY:

        logger.warning(
            "IMPORT START rejected: import_id=%s status=%s expected=%s",
            data_import.id,
            data_import.status,
            DataImport.Status.READY,
        )

        messages.error(
            request,
            "This import is not ready to be imported.",
        )

        return redirect(
            "dataintegration:integration_validate",
            import_id=data_import.id,
        )

    # --------------------------------------------------------
    # Execute import
    # --------------------------------------------------------

    logger.info(
        "IMPORT EXECUTION beginning: import_id=%s",
        data_import.id,
    )

    try:

        with transaction.atomic():

            logger.info(
                "IMPORT TRANSACTION opened: import_id=%s",
                data_import.id,
            )

            # -----------------------------------------------
            # Run the actual importer
            # -----------------------------------------------

            logger.info(
                "IMPORT RUNNER starting: import_id=%s",
                data_import.id,
            )

            result = run_import(
                data_import=data_import,
            )

            logger.info(
                "IMPORT RUNNER completed: import_id=%s result=%s",
                data_import.id,
                result,
            )

            # -----------------------------------------------
            # Update import statistics
            # -----------------------------------------------

            validated_count = result.get(
                "validated_count",
                0,
            )

            updated_count = result.get(
                "updated_count",
                0,
            )

            skipped_count = result.get(
                "skipped_count",
                0,
            )

            error_count = result.get(
                "error_count",
                0,
            )

            logger.info(
                (
                    "IMPORT STATISTICS: import_id=%s "
                    "validated=%s updated=%s skipped=%s errors=%s"
                ),
                data_import.id,
                validated_count,
                updated_count,
                skipped_count,
                error_count,
            )

            # -----------------------------------------------
            # Complete import
            # -----------------------------------------------

            data_import.status = (
                DataImport.Status.COMPLETED
            )

            data_import.completed_at = timezone.now()

            data_import.save(
                update_fields=[
                    "status",
                    "completed_at",
                ]
            )

            logger.info(
                "IMPORT COMPLETED: import_id=%s status=%s completed_at=%s",
                data_import.id,
                data_import.status,
                data_import.completed_at,
            )

    except Exception as exc:

        logger.exception(
            "IMPORT FAILED: import_id=%s error=%s",
            data_import.id,
            exc,
        )

        data_import.status = (
            DataImport.Status.FAILED
        )

        data_import.save(
            update_fields=[
                "status",
            ]
        )

        logger.info(
            "IMPORT STATUS updated to FAILED: import_id=%s",
            data_import.id,
        )

        messages.error(
            request,
            f"Import failed: {exc}",
        )

        return redirect(
            "dataintegration:integration_validate",
            import_id=data_import.id,
        )

    # --------------------------------------------------------
    # Display import results
    # --------------------------------------------------------

    logger.info(
        (
            "IMPORT RESULTS redirect: import_id=%s "
            "validated=%s updated=%s skipped=%s errors=%s"
        ),
        data_import.id,
        validated_count,
        updated_count,
        skipped_count,
        error_count,
    )

    messages.success(
        request,
        (
            f"Import completed successfully. "
            f"{validated_count} record(s) validated."
        ),
    )

    return redirect(
        "dataintegration:integration_results",
        import_id=data_import.id,
    )


from .importers import read_import_rows
from app.models import *
@login_required
@require_POST
def integration_create_import_models(request, import_id):
    """
    Create target-model records from a READY DataImport.

    Only rows that individually passed validation are imported.
    """

    logger.info(
        "CREATE MODELS START: import_id=%s user_id=%s",
        import_id,
        request.user.id,
    )

    # --------------------------------------------------------
    # Get DataImport belonging to user's company
    # --------------------------------------------------------

    data_import = get_company_import(
        request,
        import_id,
    )

    logger.info(
        "CREATE MODELS LOADED: import_id=%s status=%s target_model=%s",
        data_import.id,
        data_import.status,
        data_import.target_model,
    )

    # --------------------------------------------------------
    # Must be READY
    # --------------------------------------------------------

    if data_import.status != DataImport.Status.READY:

        messages.error(
            request,
            "This import is not ready to be imported.",
        )

        return redirect(
            "dataintegration:integration_validate",
            import_id=data_import.id,
        )

    # --------------------------------------------------------
    # Resolve target model
    # --------------------------------------------------------

    target_model = get_target_model(
        data_import.target_model
    )

    if target_model is None:

        messages.error(
            request,
            f"Unsupported target model: {data_import.target_model}",
        )

        return redirect(
            "dataintegration:integration_validate",
            import_id=data_import.id,
        )

    logger.info(
        "CREATE MODELS TARGET: import_id=%s model=%s",
        data_import.id,
        target_model.__name__,
    )

    # --------------------------------------------------------
    # Get mapped columns
    # --------------------------------------------------------

    mappings = list(
        DataImportColumn.objects
        .filter(
            data_import=data_import,
            is_mapped=True,
        )
        .order_by("column_order")
    )

    if not mappings:

        messages.error(
            request,
            "No mapped columns were found for this import.",
        )

        return redirect(
            "dataintegration:integration_validate",
            import_id=data_import.id,
        )

    # --------------------------------------------------------
    # Read uploaded file
    # --------------------------------------------------------

    try:

        rows = read_import_rows(
            data_import
        )

    except Exception as exc:

        logger.exception(
            "CREATE MODELS READ FAILED: import_id=%s",
            data_import.id,
        )

        messages.error(
            request,
            f"Unable to read the import file: {exc}",
        )

        return redirect(
            "dataintegration:integration_validate",
            import_id=data_import.id,
        )

    if not rows:

        messages.error(
            request,
            "The import file does not contain any records.",
        )

        return redirect(
            "dataintegration:integration_validate",
            import_id=data_import.id,
        )

    # --------------------------------------------------------
    # Validate again
    #
    # We intentionally revalidate here because the current
    # validation results are stored as statistics, not as
    # persistent row records.
    # --------------------------------------------------------

    try:

        validation_result = validate_import(
            data_import=data_import,
            rows=rows,
        )

    except Exception as exc:

        logger.exception(
            "CREATE MODELS VALIDATION FAILED: import_id=%s",
            data_import.id,
        )

        messages.error(
            request,
            f"Unable to validate the import: {exc}",
        )

        return redirect(
            "dataintegration:integration_validate",
            import_id=data_import.id,
        )

    # --------------------------------------------------------
    # Create target records
    # --------------------------------------------------------

    created_count = 0
    skipped_count = 0

    try:

        with transaction.atomic():

            for row_result in validation_result["rows"]:

                # ------------------------------------------------
                # Import ONLY individually valid rows
                # ------------------------------------------------

                if not row_result["valid"]:

                    skipped_count += 1

                    logger.info(
                        (
                            "CREATE MODELS SKIPPED: "
                            "import_id=%s row=%s errors=%s"
                        ),
                        data_import.id,
                        row_result["row_number"],
                        row_result["errors"],
                    )

                    continue

                row = row_result["data"]

                # ------------------------------------------------
                # Build target model data
                # ------------------------------------------------

                model_data = {}

                for mapping in mappings:

                    target_field = (
                        mapping.target_field or ""
                    ).strip()

                    if not target_field:
                        continue

                    source_column = (
                        mapping.source_column
                    )

                    value = row.get(
                        source_column
                    )

                    value = normalize_value(
                        value
                    )

                    if is_empty(value):
                        continue

                    model_data[target_field] = value

                # ------------------------------------------------
                # Automatically assign company if target model
                # has a company field.
                # ------------------------------------------------

                try:

                    target_model._meta.get_field(
                        "company"
                    )

                    model_data["company"] = (
                        data_import.company
                    )

                except Exception:

                    pass

                # ------------------------------------------------
                # Create target record
                # ------------------------------------------------

                target_model.objects.create(
                    **model_data
                )

                created_count += 1

                logger.info(
                    (
                        "CREATE MODELS CREATED: "
                        "import_id=%s row=%s model=%s"
                    ),
                    data_import.id,
                    row_result["row_number"],
                    target_model.__name__,
                )

            # ----------------------------------------------------
            # Mark DataImport completed
            # ----------------------------------------------------

            data_import.status = (
                DataImport.Status.COMPLETED
            )

            data_import.completed_at = (
                timezone.now()
            )

            data_import.save(
                update_fields=[
                    "status",
                    "completed_at",
                ]
            )

    except Exception as exc:

        logger.exception(
            "CREATE MODELS FAILED: import_id=%s error=%s",
            data_import.id,
            exc,
        )

        data_import.status = (
            DataImport.Status.FAILED
        )

        data_import.save(
            update_fields=[
                "status",
            ]
        )

        messages.error(
            request,
            f"Import failed: {exc}",
        )

        return redirect(
            "dataintegration:integration_validate",
            import_id=data_import.id,
        )

    # --------------------------------------------------------
    # Success
    # --------------------------------------------------------

    logger.info(
        (
            "CREATE MODELS COMPLETED: "
            "import_id=%s created=%s skipped=%s"
        ),
        data_import.id,
        created_count,
        skipped_count,
    )

    messages.success(
        request,
        (
            f"Import completed successfully. "
            f"{created_count} "
            f"{data_import.target_model} "
            f"record(s) created."
        ),
    )

    if skipped_count:

        messages.info(
            request,
            (
                f"{skipped_count} invalid "
                f"record(s) were skipped."
            ),
        )

    return redirect(
        "dataintegration:integration_results",
        import_id=data_import.id,
    )