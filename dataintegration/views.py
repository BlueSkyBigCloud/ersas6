
import os
import logging

from collections import Counter

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import (
    require_http_methods,
    require_POST,
)

from django.apps import apps

from .models import *
from .services import run_import_from_file
from .importers import read_import_rows
from .validators import (
    is_empty,
    normalize_value,
    validate_import,
    update_import_validation_status,
)

from business.models import Customer
from app.models import *


logger = logging.getLogger("dataintegration")


# ============================================================
# Helpers
# ============================================================

def get_company_import(request, import_id):
    """
    Return a DataImport belonging to the currently authenticated
    user's company.
    """

    logger.debug(
        "DATAIMPORT GET COMPANY IMPORT START "
        "import_id=%s user_id=%s",
        import_id,
        getattr(request.user, "id", None),
    )

    if not request.user.is_authenticated:
        logger.warning(
            "DATAIMPORT GET COMPANY IMPORT REJECTED "
            "import_id=%s reason=unauthenticated",
            import_id,
        )
        raise Http404

    company = getattr(request.user, "company", None)

    if not company:
        logger.warning(
            "DATAIMPORT GET COMPANY IMPORT REJECTED "
            "import_id=%s user_id=%s reason=no_company",
            import_id,
            request.user.id,
        )
        raise Http404

    data_import = get_object_or_404(
        DataImport,
        id=import_id,
        company=company,
    )

    logger.debug(
        "DATAIMPORT GET COMPANY IMPORT COMPLETE "
        "import_id=%s company_id=%s status=%s "
        "filename=%s target_model=%s",
        data_import.id,
        data_import.company_id,
        data_import.status,
        data_import.filename,
        data_import.target_model,
    )

    return data_import


def detect_source_type(filename):
    """
    Determine the source file type from its extension.
    """

    extension = os.path.splitext(filename)[1].lower()

    logger.debug(
        "DATAIMPORT SOURCE TYPE DETECTION "
        "filename=%s extension=%s",
        filename,
        extension,
    )

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
    """

    target_model = (
        data_import.target_model or ""
    ).lower().strip()

    logger.debug(
        "DATAIMPORT TARGET MODEL NORMALIZED "
        "import_id=%s target_model=%s",
        data_import.id,
        target_model,
    )

    return target_model


# ============================================================
# Dashboard
# ============================================================

@login_required
def integration_dashboard(request):

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

    logger.debug(
        "DATAIMPORT UPLOAD START "
        "user_id=%s method=%s",
        request.user.id,
        request.method,
    )

    if request.method == "GET":

        logger.debug(
            "DATAIMPORT UPLOAD GET "
            "user_id=%s",
            request.user.id,
        )

        return render(
            request,
            "data_integration/upload.html",
        )

    # --------------------------------------------------------
    # Receive uploaded file
    # --------------------------------------------------------

    uploaded_file = request.FILES.get("file")

    if not uploaded_file:

        logger.warning(
            "DATAIMPORT UPLOAD FAILED "
            "user_id=%s reason=no_file",
            request.user.id,
        )

        messages.error(
            request,
            "Please select a file to upload.",
        )

        return render(
            request,
            "data_integration/upload.html",
        )

    filename = uploaded_file.name

    logger.debug(
        "DATAIMPORT UPLOAD FILE RECEIVED "
        "user_id=%s filename=%s size=%s content_type=%s",
        request.user.id,
        filename,
        uploaded_file.size,
        uploaded_file.content_type,
    )

    # --------------------------------------------------------
    # Detect source type
    # --------------------------------------------------------

    source_type = detect_source_type(
        filename
    )

    logger.debug(
        "DATAIMPORT UPLOAD SOURCE DETECTED "
        "user_id=%s filename=%s source_type=%s",
        request.user.id,
        filename,
        source_type,
    )

    allowed_types = {
        DataImport.SourceType.CSV,
        DataImport.SourceType.XLSX,
        DataImport.SourceType.XLS,
        DataImport.SourceType.DAT,
    }

    logger.debug(
        "DATAIMPORT UPLOAD ALLOWED TYPES "
        "filename=%s source_type=%s allowed=%s",
        filename,
        source_type,
        source_type in allowed_types,
    )

    if source_type not in allowed_types:

        logger.warning(
            "DATAIMPORT UPLOAD REJECTED "
            "user_id=%s filename=%s source_type=%s "
            "reason=unsupported_type",
            request.user.id,
            filename,
            source_type,
        )

        messages.error(
            request,
            "Unsupported file type. "
            "Please upload a CSV, XLS, XLSX, or DAT file.",
        )

        return render(
            request,
            "data_integration/upload.html",
        )

    # --------------------------------------------------------
    # Create DataImport
    # --------------------------------------------------------

    logger.debug(
        "DATAIMPORT UPLOAD DATABASE CREATE START "
        "user_id=%s company_id=%s filename=%s source_type=%s",
        request.user.id,
        request.user.company_id,
        filename,
        source_type,
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

        logger.debug(
            "DATAIMPORT UPLOAD DATABASE CREATE COMPLETE "
            "import_id=%s company_id=%s filename=%s "
            "status=%s",
            data_import.id,
            data_import.company_id,
            data_import.filename,
            data_import.status,
        )

    except Exception as exc:

        logger.exception(
            "DATAIMPORT UPLOAD DATABASE CREATE FAILED "
            "user_id=%s filename=%s error=%s",
            request.user.id,
            filename,
            exc,
        )

        messages.error(
            request,
            f"Unable to create import: {exc}",
        )

        return render(
            request,
            "data_integration/upload.html",
        )

    # --------------------------------------------------------
    # Storage information
    #
    # Do NOT log credentials, Authorization headers, or
    # signed S3 URLs.
    # --------------------------------------------------------

    logger.debug(
        "DATAIMPORT UPLOAD STORAGE COMPLETE "
        "import_id=%s filename=%s "
        "storage_name=%s",
        data_import.id,
        filename,
        getattr(
            data_import.file,
            "name",
            None,
        ),
    )

    logger.debug(
        "DATAIMPORT UPLOAD COMPLETE "
        "import_id=%s status=%s",
        data_import.id,
        data_import.status,
    )

    logger.debug(
        "DATAIMPORT UPLOAD REDIRECT "
        "import_id=%s destination=integration_analyze",
        data_import.id,
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
    """

    logger.debug(
        "DATAIMPORT ANALYZE START "
        "import_id=%s user_id=%s method=%s",
        import_id,
        request.user.id,
        request.method,
    )

    # --------------------------------------------------------
    # Load import
    # --------------------------------------------------------

    data_import = get_company_import(
        request,
        import_id,
    )

    logger.debug(
        "DATAIMPORT ANALYZE IMPORT LOADED "
        "import_id=%s company_id=%s filename=%s "
        "source_type=%s target_model=%s status=%s",
        data_import.id,
        data_import.company_id,
        data_import.filename,
        data_import.source_type,
        data_import.target_model,
        data_import.status,
    )

    # --------------------------------------------------------
    # Prevent analysis of completed/cancelled imports
    # --------------------------------------------------------

    if data_import.status in [
        DataImport.Status.COMPLETED,
        DataImport.Status.CANCELLED,
    ]:

        logger.warning(
            "DATAIMPORT ANALYZE REJECTED "
            "import_id=%s status=%s reason=terminal_status",
            data_import.id,
            data_import.status,
        )

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

    old_status = data_import.status

    data_import.status = DataImport.Status.ANALYZING

    data_import.save(
        update_fields=["status"]
    )

    logger.debug(
        "DATAIMPORT ANALYZE STATUS CHANGE "
        "import_id=%s old_status=%s new_status=%s",
        data_import.id,
        old_status,
        data_import.status,
    )

    try:

        # ----------------------------------------------------
        # Import analyzer
        # ----------------------------------------------------

        logger.debug(
            "DATAIMPORT ANALYZE IMPORTER START "
            "import_id=%s",
        )

        from .importers import analyze_import_file

        analysis_data = analyze_import_file(
            data_import
        )

        logger.debug(
            "DATAIMPORT ANALYZE IMPORTER COMPLETE "
            "import_id=%s result_type=%s result_keys=%s",
            data_import.id,
            type(analysis_data).__name__,
            (
                list(analysis_data.keys())
                if isinstance(analysis_data, dict)
                else None
            ),
        )

        # ----------------------------------------------------
        # Validate analyzer response
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

        total_rows = analysis_data.get(
            "total_rows",
            0,
        )

        detected_model = analysis_data.get(
            "detected_model"
        )

        logger.debug(
            "DATAIMPORT ANALYZE RESULT "
            "import_id=%s header_count=%s "
            "total_rows=%s detected_model=%s",
            data_import.id,
            len(headers) if isinstance(headers, list) else None,
            total_rows,
            detected_model,
        )

        # ----------------------------------------------------
        # Headers
        # ----------------------------------------------------

        if not isinstance(
            headers,
            list,
        ):
            raise ValueError(
                "File analyzer returned invalid column headers."
            )

        logger.debug(
            "DATAIMPORT ANALYZE HEADERS "
            "import_id=%s headers=%s",
            data_import.id,
            headers,
        )

        # ----------------------------------------------------
        # Delete previous columns
        # ----------------------------------------------------

        deleted_count, _ = (
            DataImportColumn.objects
            .filter(
                data_import=data_import
            )
            .delete()
        )

        logger.debug(
            "DATAIMPORT ANALYZE OLD COLUMNS REMOVED "
            "import_id=%s deleted=%s",
            data_import.id,
            deleted_count,
        )

        # ----------------------------------------------------
        # Create DataImportColumn records
        # ----------------------------------------------------

        column_objects = []

        for column_order, header in enumerate(headers):

            if header is None:
                logger.debug(
                    "DATAIMPORT ANALYZE HEADER SKIPPED "
                    "import_id=%s column_order=%s reason=none",
                    data_import.id,
                    column_order,
                )
                continue

            header = str(header).strip()

            if not header:
                logger.debug(
                    "DATAIMPORT ANALYZE HEADER SKIPPED "
                    "import_id=%s column_order=%s reason=empty",
                    data_import.id,
                    column_order,
                )
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

            logger.debug(
                "DATAIMPORT ANALYZE COLUMN DISCOVERED "
                "import_id=%s column_order=%s source_column=%s",
                data_import.id,
                column_order,
                header,
            )

        DataImportColumn.objects.bulk_create(
            column_objects
        )

        logger.debug(
            "DATAIMPORT ANALYZE COLUMNS CREATED "
            "import_id=%s count=%s",
            data_import.id,
            len(column_objects),
        )

        # ----------------------------------------------------
        # Validate row count
        # ----------------------------------------------------

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

        logger.debug(
            "DATAIMPORT ANALYZE ROW COUNT VALID "
            "import_id=%s total_rows=%s",
            data_import.id,
            total_rows,
        )

        # ----------------------------------------------------
        # Save detected model
        # ----------------------------------------------------

        if detected_model:

            data_import.target_model = str(
                detected_model
            ).strip()

            logger.debug(
                "DATAIMPORT ANALYZE TARGET MODEL DETECTED "
                "import_id=%s target_model=%s",
                data_import.id,
                data_import.target_model,
            )

        else:

            logger.debug(
                "DATAIMPORT ANALYZE TARGET MODEL NOT DETECTED "
                "import_id=%s",
                data_import.id,
            )

        # ----------------------------------------------------
        # Save analysis
        # ----------------------------------------------------

        data_import.total_rows = total_rows

        data_import.status = (
            DataImport.Status.MAPPING
        )

        data_import.save(
            update_fields=[
                "target_model",
                "total_rows",
                "status",
            ]
        )

        logger.debug(
            "DATAIMPORT ANALYZE COMPLETE "
            "import_id=%s total_rows=%s "
            "columns=%s target_model=%s status=%s",
            data_import.id,
            total_rows,
            len(column_objects),
            data_import.target_model,
            data_import.status,
        )

    except Exception as exc:

        logger.exception(
            "DATAIMPORT ANALYZE FAILED "
            "import_id=%s filename=%s error=%s",
            data_import.id,
            data_import.filename,
            exc,
        )

        data_import.status = (
            DataImport.Status.FAILED
        )

        data_import.save(
            update_fields=["status"]
        )

        logger.debug(
            "DATAIMPORT ANALYZE STATUS FAILED "
            "import_id=%s status=%s",
            data_import.id,
            data_import.status,
        )

        messages.error(
            request,
            f"Unable to analyze the file: {exc}",
        )

        return redirect(
            "dataintegration:integration_dashboard"
        )

    # --------------------------------------------------------
    # Render
    # --------------------------------------------------------

    logger.debug(
        "DATAIMPORT ANALYZE RENDER "
        "import_id=%s template=data_integration/analyze.html",
        data_import.id,
    )

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
# TARGET FIELD MAPPING HELPER
# ============================================================

def get_import_target_fields():

    logger.debug(
        "DATAIMPORT TARGET FIELDS START"
    )

    target_models = {
        "Employee": Employee,
        "Equipment": Equipment,
        "Location": Location,
        "Customer": Customer,
        "ServiceRequest": ServiceRequest,
    }

    model_fields = {}

    for model_name, model_class in target_models.items():

        fields = []

        logger.debug(
            "DATAIMPORT TARGET FIELDS MODEL "
            "model=%s",
            model_name,
        )

        for field in model_class._meta.fields:

            if field.name in [
                "id",
                "company",
                "created_at",
                "updated_at",
            ]:
                continue

            if field.is_relation:
                logger.debug(
                    "DATAIMPORT TARGET FIELD SKIPPED RELATION "
                    "model=%s field=%s",
                    model_name,
                    field.name,
                )
                continue

            fields.append({
                "name": field.name,
                "label": field.verbose_name.title(),
            })

        model_fields[model_name] = fields

        logger.debug(
            "DATAIMPORT TARGET FIELDS MODEL COMPLETE "
            "model=%s field_count=%s fields=%s",
            model_name,
            len(fields),
            [field["name"] for field in fields],
        )

    logger.debug(
        "DATAIMPORT TARGET FIELDS COMPLETE "
        "model_count=%s",
        len(model_fields),
    )

    return model_fields


# ============================================================
# Mapping
# ============================================================

@login_required
@require_http_methods(["GET", "POST"])
def integration_mapping(request, import_id):
    """
    Display and save the column mapping and target model.
    """

    logger.debug(
        "DATAIMPORT MAPPING START "
        "user_id=%s import_id=%s method=%s",
        request.user.id,
        import_id,
        request.method,
    )

    data_import = get_company_import(
        request,
        import_id,
    )

    logger.debug(
        "DATAIMPORT MAPPING IMPORT LOADED "
        "import_id=%s filename=%s source_type=%s "
        "target_model=%s status=%s",
        data_import.id,
        data_import.filename,
        data_import.source_type,
        data_import.target_model,
        data_import.status,
    )

    # --------------------------------------------------------
    # Verify status
    # --------------------------------------------------------

    allowed_statuses = [
        DataImport.Status.MAPPING,
        DataImport.Status.UPLOADED,
        DataImport.Status.ANALYZING,
    ]

    if data_import.status not in allowed_statuses:

        logger.warning(
            "DATAIMPORT MAPPING REJECTED "
            "import_id=%s status=%s allowed=%s",
            data_import.id,
            data_import.status,
            allowed_statuses,
        )

        messages.warning(
            request,
            "This import is not currently available for mapping.",
        )

        return redirect(
            "dataintegration:integration_dashboard"
        )

    # --------------------------------------------------------
    # Existing columns
    # --------------------------------------------------------

    columns = (
        DataImportColumn.objects
        .filter(
            data_import=data_import
        )
        .order_by("column_order")
    )

    column_count = columns.count()

    logger.debug(
        "DATAIMPORT MAPPING COLUMNS LOADED "
        "import_id=%s count=%s",
        data_import.id,
        column_count,
    )

    # --------------------------------------------------------
    # GET
    # --------------------------------------------------------

    if request.method == "GET":

        model_fields = (
            get_import_target_fields()
        )

        logger.debug(
            "DATAIMPORT MAPPING GET "
            "import_id=%s column_count=%s "
            "model_count=%s",
            data_import.id,
            column_count,
            len(model_fields),
        )

        return render(
            request,
            "data_integration/mapping.html",
            {
                "data_import": data_import,
                "columns": columns,
                "model_fields": model_fields,
            },
        )

    # --------------------------------------------------------
    # POST
    # --------------------------------------------------------

    logger.debug(
        "DATAIMPORT MAPPING POST RECEIVED "
        "import_id=%s post_keys=%s",
        data_import.id,
        list(request.POST.keys()),
    )

    try:

        with transaction.atomic():

            # ------------------------------------------------
            # Target Model
            # ------------------------------------------------

            target_model = (
                request.POST.get(
                    "target_model",
                    "",
                )
                .strip()
            )

            logger.debug(
                "DATAIMPORT MAPPING TARGET MODEL "
                "import_id=%s target_model=%s",
                data_import.id,
                target_model,
            )

            if not target_model:

                logger.warning(
                    "DATAIMPORT MAPPING FAILED "
                    "import_id=%s reason=no_target_model",
                    data_import.id,
                )

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

            old_target_model = (
                data_import.target_model
            )

            data_import.target_model = (
                target_model
            )

            logger.debug(
                "DATAIMPORT MAPPING TARGET MODEL UPDATED "
                "import_id=%s old=%s new=%s",
                data_import.id,
                old_target_model,
                target_model,
            )

            # ------------------------------------------------
            # Remove existing mappings
            # ------------------------------------------------

            deleted_count, _ = (
                DataImportColumn.objects
                .filter(
                    data_import=data_import
                )
                .delete()
            )

            logger.debug(
                "DATAIMPORT MAPPING OLD MAPPINGS REMOVED "
                "import_id=%s deleted=%s",
                data_import.id,
                deleted_count,
            )

            # ------------------------------------------------
            # Recreate mappings
            # ------------------------------------------------

            column_index = 0
            submitted_count = 0
            mapped_count = 0
            unmapped_count = 0

            while True:

                source_column = request.POST.get(
                    f"source_column_{column_index}"
                )

                target_field = request.POST.get(
                    f"target_field_{column_index}"
                )

                if source_column is None:
                    break

                source_column = (
                    source_column.strip()
                )

                target_field = (
                    target_field or ""
                ).strip()

                is_required = (
                    request.POST.get(
                        f"is_required_{column_index}"
                    ) == "on"
                )

                submitted_count += 1

                if source_column:

                    is_mapped = bool(
                        target_field
                    )

                    DataImportColumn.objects.create(
                        data_import=data_import,
                        source_column=source_column,
                        target_field=target_field,
                        column_order=column_index,
                        is_required=is_required,
                        is_mapped=is_mapped,
                    )

                    if is_mapped:
                        mapped_count += 1
                    else:
                        unmapped_count += 1

                    logger.debug(
                        "DATAIMPORT MAPPING COLUMN "
                        "import_id=%s index=%s source=%s "
                        "target=%s mapped=%s required=%s",
                        data_import.id,
                        column_index,
                        source_column,
                        target_field or "<unmapped>",
                        is_mapped,
                        is_required,
                    )

                else:

                    logger.debug(
                        "DATAIMPORT MAPPING COLUMN SKIPPED "
                        "import_id=%s index=%s reason=empty_source",
                        data_import.id,
                        column_index,
                    )

                column_index += 1

            logger.debug(
                "DATAIMPORT MAPPING POST PROCESSED "
                "import_id=%s submitted=%s mapped=%s "
                "unmapped=%s",
                data_import.id,
                submitted_count,
                mapped_count,
                unmapped_count,
            )

            # ------------------------------------------------
            # Require at least one mapped field
            # ------------------------------------------------

            if mapped_count == 0:

                logger.warning(
                    "DATAIMPORT MAPPING FAILED "
                    "import_id=%s reason=no_mapped_columns",
                    data_import.id,
                )

                raise ValueError(
                    "At least one source column must be mapped "
                    "to a target field."
                )

            # ------------------------------------------------
            # Set validation status
            # ------------------------------------------------

            old_status = data_import.status

            data_import.status = (
                DataImport.Status.VALIDATING
            )

            data_import.save(
                update_fields=[
                    "target_model",
                    "status",
                ]
            )

            logger.debug(
                "DATAIMPORT MAPPING STATUS CHANGE "
                "import_id=%s old_status=%s new_status=%s",
                data_import.id,
                old_status,
                data_import.status,
            )

    except Exception as exc:

        logger.exception(
            "DATAIMPORT MAPPING FAILED "
            "import_id=%s error=%s",
            data_import.id,
            exc,
        )

        messages.error(
            request,
            f"Unable to save the mapping: {exc}",
        )

        return redirect(
            "dataintegration:integration_mapping",
            import_id=data_import.id,
        )

    logger.debug(
        "DATAIMPORT MAPPING COMPLETE "
        "import_id=%s target_model=%s "
        "mapped=%s unmapped=%s status=%s",
        data_import.id,
        data_import.target_model,
        mapped_count,
        unmapped_count,
        data_import.status,
    )

    return redirect(
        "dataintegration:integration_validate",
        import_id=data_import.id,
    )


# ============================================================
# Validation
# ============================================================

@login_required
@require_http_methods(["GET", "POST"])
def integration_validate(request, import_id):
    """
    Validate the mapped import before allowing the import operation.
    """

    logger.debug(
        "DATAIMPORT VALIDATE START "
        "import_id=%s user_id=%s method=%s",
        import_id,
        request.user.id,
        request.method,
    )

    # --------------------------------------------------------
    # Load DataImport
    # --------------------------------------------------------

    data_import = get_company_import(
        request,
        import_id,
    )

    logger.debug(
        "DATAIMPORT VALIDATE IMPORT LOADED "
        "import_id=%s filename=%s source_type=%s "
        "target_model=%s status=%s total_rows=%s",
        data_import.id,
        data_import.filename,
        data_import.source_type,
        data_import.target_model,
        data_import.status,
        data_import.total_rows,
    )

    # --------------------------------------------------------
    # Load mappings
    # --------------------------------------------------------

    mappings = (
        DataImportColumn.objects
        .filter(
            data_import=data_import
        )
        .order_by("column_order")
    )

    mapping_count = mappings.count()

    mapped_count = mappings.filter(
        is_mapped=True
    ).count()

    unmapped_count = mapping_count - mapped_count

    logger.debug(
        "DATAIMPORT VALIDATE MAPPINGS LOADED "
        "import_id=%s total=%s mapped=%s unmapped=%s",
        data_import.id,
        mapping_count,
        mapped_count,
        unmapped_count,
    )

    if not mapping_count:

        logger.warning(
            "DATAIMPORT VALIDATE REJECTED "
            "import_id=%s reason=no_mappings",
            data_import.id,
        )

        messages.error(
            request,
            "No column mappings have been configured.",
        )

        return redirect(
            "dataintegration:integration_mapping",
            import_id=data_import.id,
        )

    # --------------------------------------------------------
    # Log mapping definitions
    # --------------------------------------------------------

    mapping_debug = []

    for mapping in mappings:

        mapping_debug.append({
            "source": mapping.source_column,
            "target": mapping.target_field or None,
            "mapped": mapping.is_mapped,
            "required": mapping.is_required,
        })

    logger.debug(
        "DATAIMPORT VALIDATE MAPPING DETAILS "
        "import_id=%s mappings=%s",
        data_import.id,
        mapping_debug,
    )

    # --------------------------------------------------------
    # Set status
    # --------------------------------------------------------

    old_status = data_import.status

    data_import.status = (
        DataImport.Status.VALIDATING
    )

    data_import.save(
        update_fields=["status"]
    )

    logger.debug(
        "DATAIMPORT VALIDATE STATUS CHANGE "
        "import_id=%s old_status=%s new_status=%s",
        data_import.id,
        old_status,
        data_import.status,
    )

    try:

        # ----------------------------------------------------
        # Read file
        # ----------------------------------------------------

        logger.debug(
            "DATAIMPORT VALIDATE FILE READ START "
            "import_id=%s filename=%s source_type=%s",
            data_import.id,
            data_import.filename,
            data_import.source_type,
        )

        rows = read_import_rows(
            data_import
        )

        logger.debug(
            "DATAIMPORT VALIDATE FILE READ COMPLETE "
            "import_id=%s row_count=%s",
            data_import.id,
            len(rows),
        )

        if rows:

            first_row = rows[0]

            logger.debug(
                "DATAIMPORT VALIDATE FIRST ROW STRUCTURE "
                "import_id=%s field_count=%s fields=%s",
                data_import.id,
                len(first_row),
                list(first_row.keys()),
            )

        else:

            logger.warning(
                "DATAIMPORT VALIDATE FILE EMPTY "
                "import_id=%s",
                data_import.id,
            )

        # ----------------------------------------------------
        # Validate rows
        # ----------------------------------------------------

        logger.debug(
            "DATAIMPORT VALIDATE ENGINE START "
            "import_id=%s rows=%s mappings=%s target_model=%s",
            data_import.id,
            len(rows),
            mapping_count,
            data_import.target_model,
        )

        validation_data = validate_import(
            data_import=data_import,
            rows=rows,
        )

        # ----------------------------------------------------
        # Inspect validation result structure
        # ----------------------------------------------------

        logger.debug(
            "DATAIMPORT VALIDATE ENGINE COMPLETE "
            "import_id=%s result_type=%s result_keys=%s",
            data_import.id,
            type(validation_data).__name__,
            (
                list(validation_data.keys())
                if isinstance(
                    validation_data,
                    dict,
                )
                else None
            ),
        )

        validation_rows = []

        if isinstance(
            validation_data,
            dict,
        ):

            validation_rows = (
                validation_data.get(
                    "rows",
                    [],
                )
            )

        logger.debug(
            "DATAIMPORT VALIDATE RESULT ROWS "
            "import_id=%s count=%s",
            data_import.id,
            len(validation_rows),
        )

        # ----------------------------------------------------
        # Summarize validation without logging row data
        # ----------------------------------------------------

        valid_count = 0
        invalid_count = 0
        error_counter = Counter()

        for row_result in validation_rows:

            if row_result.get("valid"):
                valid_count += 1

            else:
                invalid_count += 1

                for error in row_result.get(
                    "errors",
                    [],
                ):

                    error_counter[
                        str(error)
                    ] += 1

        logger.debug(
            "DATAIMPORT VALIDATE SUMMARY "
            "import_id=%s total=%s valid=%s invalid=%s "
            "unique_errors=%s",
            data_import.id,
            len(validation_rows),
            valid_count,
            invalid_count,
            len(error_counter),
        )

        if error_counter:

            logger.debug(
                "DATAIMPORT VALIDATE ERROR SUMMARY "
                "import_id=%s errors=%s",
                data_import.id,
                dict(error_counter),
            )

        # ----------------------------------------------------
        # Update status/statistics
        # ----------------------------------------------------

        logger.debug(
            "DATAIMPORT VALIDATE STATUS UPDATE START "
            "import_id=%s",
            data_import.id,
        )

        update_import_validation_status(
            data_import=data_import,
            validation_result=validation_data,
        )

        data_import.refresh_from_db()

        logger.debug(
            "DATAIMPORT VALIDATE STATUS UPDATE COMPLETE "
            "import_id=%s status=%s total_rows=%s "
            "valid_rows=%s error_rows=%s",
            data_import.id,
            data_import.status,
            data_import.total_rows,
            data_import.valid_rows,
            data_import.error_rows,
        )

    except Exception as exc:

        logger.exception(
            "DATAIMPORT VALIDATE FAILED "
            "import_id=%s filename=%s "
            "target_model=%s error=%s",
            data_import.id,
            data_import.filename,
            data_import.target_model,
            exc,
        )

        data_import.status = (
            DataImport.Status.FAILED
        )

        data_import.save(
            update_fields=["status"]
        )

        logger.debug(
            "DATAIMPORT VALIDATE STATUS FAILED "
            "import_id=%s status=%s",
            data_import.id,
            data_import.status,
        )

        messages.error(
            request,
            f"Validation failed: {exc}",
        )

        return redirect(
            "dataintegration:integration_dashboard"
        )

    # --------------------------------------------------------
    # Final refresh
    # --------------------------------------------------------

    data_import.refresh_from_db()

    logger.debug(
        "DATAIMPORT VALIDATE COMPLETE "
        "import_id=%s status=%s total_rows=%s "
        "valid_rows=%s error_rows=%s",
        data_import.id,
        data_import.status,
        data_import.total_rows,
        data_import.valid_rows,
        data_import.error_rows,
    )

    context = {
        "data_import": data_import,
        "mappings": mappings,
        "validation": validation_data,
    }

    logger.debug(
        "DATAIMPORT VALIDATE RENDER "
        "import_id=%s template=data_integration/validation.html",
        data_import.id,
    )

    return render(
        request,
        "data_integration/validation.html",
        context,
    )
