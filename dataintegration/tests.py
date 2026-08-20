from datetime import date
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from openpyxl import Workbook

from .models import (
    DataImport,
    DataImportColumn,
)

from .importers import (
    read_csv,
    read_xlsx,
    read_import_rows,
)

from .mappings import (
    auto_map_columns,
    mapping_summary,
)

from .utils import (
    apply_mapping,
    clean_date,
    clean_email,
    clean_integer,
    clean_number,
    clean_phone,
    normalize_column_name,
    normalize_text,
)


# ============================================================
# Test model imports
# ============================================================

from users.models import CustomUser
from app.models import Company

# ============================================================
# DataImport model tests
# ============================================================

class DataImportModelTests(TestCase):

    def setUp(self):

        self.company = Company.objects.create(
            name="Test Company"
        )

        self.user = CustomUser.objects.create_user(
            email="test@example.com",
            password="testpassword",
            company=self.company,
        )

    def create_import(self):

        uploaded_file = SimpleUploadedFile(
            "employees.csv",
            (
                "Emp #,First,Last\n"
                "EMP001,John,Smith\n"
            ).encode(),
            content_type="text/csv",
        )

        return DataImport.objects.create(
            company=self.company,
            uploaded_by=self.user,
            file=uploaded_file,
            filename="employees.csv",
            source_type=DataImport.SourceType.CSV,
            target_model="Employee",
            status=DataImport.Status.UPLOADED,
        )

    def test_data_import_can_be_created(self):

        data_import = self.create_import()

        self.assertIsNotNone(
            data_import.id
        )

        self.assertEqual(
            data_import.company,
            self.company,
        )

        self.assertEqual(
            data_import.uploaded_by,
            self.user,
        )

        self.assertEqual(
            data_import.filename,
            "employees.csv",
        )

        self.assertEqual(
            data_import.source_type,
            DataImport.SourceType.CSV,
        )

        self.assertEqual(
            data_import.target_model,
            "Employee",
        )

        self.assertEqual(
            data_import.status,
            DataImport.Status.UPLOADED,
        )

    def test_default_row_counts_are_zero(self):

        data_import = self.create_import()

        self.assertEqual(
            data_import.total_rows,
            0,
        )

        self.assertEqual(
            data_import.valid_rows,
            0,
        )

        self.assertEqual(
            data_import.error_rows,
            0,
        )

    def test_string_representation(self):

        data_import = self.create_import()

        self.assertEqual(
            str(data_import),
            "employees.csv - Uploaded",
        )


# ============================================================
# DataImportColumn model tests
# ============================================================

class DataImportColumnModelTests(TestCase):

    def setUp(self):

        self.company = Company.objects.create(
            name="Mapping Company"
        )

        self.user = CustomUser.objects.create_user(
            email="mapping@example.com",
            password="testpassword",
            company=self.company,
        )

        uploaded_file = SimpleUploadedFile(
            "employees.csv",
            b"Emp #,First,Last\n",
            content_type="text/csv",
        )

        self.data_import = DataImport.objects.create(
            company=self.company,
            uploaded_by=self.user,
            file=uploaded_file,
            filename="employees.csv",
            source_type=DataImport.SourceType.CSV,
            target_model="Employee",
            status=DataImport.Status.MAPPING,
        )

    def test_mapping_can_be_created(self):

        mapping = DataImportColumn.objects.create(
            data_import=self.data_import,
            source_column="Emp #",
            target_field="employee_number",
            column_order=0,
            is_required=True,
            is_mapped=True,
        )

        self.assertEqual(
            mapping.source_column,
            "Emp #",
        )

        self.assertEqual(
            mapping.target_field,
            "employee_number",
        )

        self.assertTrue(
            mapping.is_required
        )

        self.assertTrue(
            mapping.is_mapped
        )

    def test_mapping_relationship(self):

        DataImportColumn.objects.create(
            data_import=self.data_import,
            source_column="Emp #",
            target_field="employee_number",
            column_order=0,
        )

        DataImportColumn.objects.create(
            data_import=self.data_import,
            source_column="First",
            target_field="first_name",
            column_order=1,
        )

        self.assertEqual(
            self.data_import.columns.count(),
            2,
        )

    def test_mapping_ordering(self):

        DataImportColumn.objects.create(
            data_import=self.data_import,
            source_column="Last",
            target_field="last_name",
            column_order=2,
        )

        DataImportColumn.objects.create(
            data_import=self.data_import,
            source_column="Emp #",
            target_field="employee_number",
            column_order=0,
        )

        DataImportColumn.objects.create(
            data_import=self.data_import,
            source_column="First",
            target_field="first_name",
            column_order=1,
        )

        columns = list(
            self.data_import.columns.all()
        )

        self.assertEqual(
            columns[0].source_column,
            "Emp #",
        )

        self.assertEqual(
            columns[1].source_column,
            "First",
        )

        self.assertEqual(
            columns[2].source_column,
            "Last",
        )

    def test_duplicate_source_column_is_rejected(self):

        DataImportColumn.objects.create(
            data_import=self.data_import,
            source_column="Emp #",
            target_field="employee_number",
        )

        with self.assertRaises(Exception):

            DataImportColumn.objects.create(
                data_import=self.data_import,
                source_column="Emp #",
                target_field="first_name",
            )


# ============================================================
# Utility tests
# ============================================================

class DataIntegrationUtilsTests(TestCase):

    def test_normalize_text(self):

        result = normalize_text(
            "  John    Smith  "
        )

        self.assertEqual(
            result,
            "john smith",
        )

    def test_normalize_column_name(self):

        result = normalize_column_name(
            "Employee_Number"
        )

        self.assertEqual(
            result,
            "employee number",
        )

    def test_clean_phone(self):

        result = clean_phone(
            "(775) 555-1234"
        )

        self.assertEqual(
            result,
            "7755551234",
        )

    def test_clean_email(self):

        result = clean_email(
            " TEST@Example.COM "
        )

        self.assertEqual(
            result,
            "test@example.com",
        )

    def test_clean_integer(self):

        result = clean_integer(
            "1,250"
        )

        self.assertEqual(
            result,
            1250,
        )

    def test_clean_number(self):

        result = clean_number(
            "$1,250.50"
        )

        self.assertEqual(
            str(result),
            "1250.50",
        )

    def test_clean_date(self):

        result = clean_date(
            "08/19/2026"
        )

        self.assertEqual(
            result,
            date(2026, 8, 19),
        )


# ============================================================
# CSV importer tests
# ============================================================

class CSVImporterTests(TestCase):

    def test_csv_is_read_correctly(self):

        csv_data = (
            "Emp #,First,Last,Mobile\n"
            "EMP001,John,Smith,7755551234\n"
            "EMP002,Jane,Doe,7755555678\n"
        ).encode()

        rows = read_csv(
            csv_data
        )

        self.assertEqual(
            len(rows),
            2,
        )

        self.assertEqual(
            rows[0]["Emp #"],
            "EMP001",
        )

        self.assertEqual(
            rows[0]["First"],
            "John",
        )

        self.assertEqual(
            rows[1]["Last"],
            "Doe",
        )

    def test_csv_detects_semicolon(self):

        csv_data = (
            "Emp #;First;Last\n"
            "EMP001;John;Smith\n"
        ).encode()

        rows = read_csv(
            csv_data
        )

        self.assertEqual(
            len(rows),
            1,
        )

        self.assertEqual(
            rows[0]["Emp #"],
            "EMP001",
        )

    def test_csv_skips_empty_rows(self):

        csv_data = (
            "Emp #,First,Last\n"
            "EMP001,John,Smith\n"
            ",,\n"
            "EMP002,Jane,Doe\n"
        ).encode()

        rows = read_csv(
            csv_data
        )

        self.assertEqual(
            len(rows),
            2,
        )

    def test_csv_with_utf8_bom(self):

        csv_data = (
            "\ufeffEmp #,First,Last\n"
            "EMP001,John,Smith\n"
        ).encode(
            "utf-8-sig"
        )

        rows = read_csv(
            csv_data
        )

        self.assertEqual(
            rows[0]["Emp #"],
            "EMP001",
        )


# ============================================================
# XLSX importer tests
# ============================================================

class XLSXImporterTests(TestCase):

    def create_xlsx(self):

        workbook = Workbook()

        worksheet = workbook.active

        worksheet.append([
            "Emp #",
            "First",
            "Last",
            "Mobile",
        ])

        worksheet.append([
            "EMP001",
            "John",
            "Smith",
            "7755551234",
        ])

        worksheet.append([
            "EMP002",
            "Jane",
            "Doe",
            "7755555678",
        ])

        output = BytesIO()

        workbook.save(
            output
        )

        return output.getvalue()

    def test_xlsx_is_read_correctly(self):

        file_data = self.create_xlsx()

        rows = read_xlsx(
            file_data
        )

        self.assertEqual(
            len(rows),
            2,
        )

        self.assertEqual(
            rows[0]["Emp #"],
            "EMP001",
        )

        self.assertEqual(
            rows[1]["First"],
            "Jane",
        )

    def test_xlsx_skips_empty_rows(self):

        workbook = Workbook()

        worksheet = workbook.active

        worksheet.append([
            "Emp #",
            "First",
            "Last",
        ])

        worksheet.append([
            "EMP001",
            "John",
            "Smith",
        ])

        worksheet.append([
            None,
            None,
            None,
        ])

        output = BytesIO()

        workbook.save(
            output
        )

        rows = read_xlsx(
            output.getvalue()
        )

        self.assertEqual(
            len(rows),
            1,
        )


# ============================================================
# read_import_rows tests
# ============================================================

class ReadImportRowsTests(TestCase):

    def setUp(self):

        self.company = Company.objects.create(
            name="File Company"
        )

        self.user = CustomUser.objects.create_user(
            email="file@example.com",
            password="testpassword",
            company=self.company,
        )

    def test_read_import_rows_csv(self):

        uploaded_file = SimpleUploadedFile(
            "employees.csv",
            (
                "Emp #,First,Last\n"
                "EMP001,John,Smith\n"
                "EMP002,Jane,Doe\n"
            ).encode(),
            content_type="text/csv",
        )

        data_import = DataImport.objects.create(
            company=self.company,
            uploaded_by=self.user,
            file=uploaded_file,
            filename="employees.csv",
            source_type=DataImport.SourceType.CSV,
            target_model="Employee",
            status=DataImport.Status.UPLOADED,
        )

        rows = read_import_rows(
            data_import
        )

        self.assertEqual(
            len(rows),
            2,
        )

        self.assertEqual(
            rows[0]["Emp #"],
            "EMP001",
        )

        self.assertEqual(
            rows[1]["Last"],
            "Doe",
        )


# ============================================================
# Mapping tests
# ============================================================

class MappingTests(TestCase):

    def test_employee_alias_mapping(self):

        from app.models import Employee

        mappings = auto_map_columns(
            [
                "Emp #",
                "First",
                "Last",
                "Mobile",
                "Job Title",
            ],
            Employee,
        )

        mapping_dict = {
            item["source_column"]:
            item["target_field"]
            for item in mappings
        }

        self.assertEqual(
            mapping_dict["Emp #"],
            "employee_number",
        )

        self.assertEqual(
            mapping_dict["First"],
            "first_name",
        )

        self.assertEqual(
            mapping_dict["Last"],
            "last_name",
        )

        self.assertEqual(
            mapping_dict["Mobile"],
            "phone_number",
        )

        self.assertEqual(
            mapping_dict["Job Title"],
            "position",
        )

    def test_unknown_column_is_unmapped(self):

        from app.models import Employee

        mappings = auto_map_columns(
            [
                "Something Completely Unknown"
            ],
            Employee,
        )

        self.assertEqual(
            len(mappings),
            1,
        )

        self.assertFalse(
            mappings[0]["is_mapped"]
        )

        self.assertEqual(
            mappings[0]["target_field"],
            "",
        )

    def test_mapping_summary(self):

        mappings = [
            {
                "source_column": "Emp #",
                "target_field": "employee_number",
                "confidence": 0.95,
                "is_mapped": True,
                "is_required": True,
            },
            {
                "source_column": "First",
                "target_field": "first_name",
                "confidence": 0.95,
                "is_mapped": True,
                "is_required": True,
            },
            {
                "source_column": "Unknown",
                "target_field": "",
                "confidence": 0,
                "is_mapped": False,
                "is_required": False,
            },
        ]

        summary = mapping_summary(
            mappings
        )

        self.assertEqual(
            summary["total"],
            3,
        )

        self.assertEqual(
            summary["mapped"],
            2,
        )

        self.assertEqual(
            summary["unmapped"],
            1,
        )


# ============================================================
# apply_mapping tests
# ============================================================

class ApplyMappingTests(TestCase):

    def test_apply_mapping(self):

        row = {
            "Emp #": "EMP001",
            "First": "John",
            "Last": "Smith",
        }

        mappings = [
            DataImportColumn(
                source_column="Emp #",
                target_field="employee_number",
                is_mapped=True,
            ),
            DataImportColumn(
                source_column="First",
                target_field="first_name",
                is_mapped=True,
            ),
            DataImportColumn(
                source_column="Last",
                target_field="last_name",
                is_mapped=True,
            ),
        ]

        result = apply_mapping(
            row,
            mappings,
        )

        self.assertEqual(
            result["employee_number"],
            "EMP001",
        )

        self.assertEqual(
            result["first_name"],
            "John",
        )

        self.assertEqual(
            result["last_name"],
            "Smith",
        )


# ============================================================
# Status tests
# ============================================================

class DataImportStatusTests(TestCase):

    def test_all_statuses_exist(self):

        expected_statuses = {
            "UPLOADED",
            "ANALYZING",
            "MAPPING",
            "VALIDATING",
            "READY",
            "IMPORTING",
            "COMPLETED",
            "FAILED",
            "CANCELLED",
        }

        actual_statuses = {
            value
            for value, label
            in DataImport.Status.choices
        }

        self.assertEqual(
            actual_statuses,
            expected_statuses,
        )


# ============================================================
# Source type tests
# ============================================================

class DataImportSourceTypeTests(TestCase):

    def test_all_source_types_exist(self):

        expected_source_types = {
            "CSV",
            "XLSX",
            "XLS",
            "DAT",
            "OTHER",
        }

        actual_source_types = {
            value
            for value, label
            in DataImport.SourceType.choices
        }

        self.assertEqual(
            actual_source_types,
            expected_source_types,
        )


# ============================================================
# Company isolation tests
# ============================================================

class CompanyIsolationTests(TestCase):

    def setUp(self):

        self.company_a = Company.objects.create(
            name="Company A"
        )

        self.company_b = Company.objects.create(
            name="Company B"
        )

        self.user_a = CustomUser.objects.create_user(
            email="usera@example.com",
            password="testpassword",
            company=self.company_a,
        )

        self.user_b = CustomUser.objects.create_user(
            email="userb@example.com",
            password="testpassword",
            company=self.company_b,
        )

    def test_import_belongs_to_correct_company(self):

        uploaded_file = SimpleUploadedFile(
            "employees.csv",
            b"Emp #,First,Last\nEMP001,John,Smith\n",
            content_type="text/csv",
        )

        data_import = DataImport.objects.create(
            company=self.company_a,
            uploaded_by=self.user_a,
            file=uploaded_file,
            filename="employees.csv",
            source_type=DataImport.SourceType.CSV,
            target_model="Employee",
            status=DataImport.Status.UPLOADED,
        )

        self.assertEqual(
            data_import.company,
            self.company_a,
        )

        self.assertNotEqual(
            data_import.company,
            self.company_b,
        )

    def test_company_has_related_imports(self):

        uploaded_file = SimpleUploadedFile(
            "employees.csv",
            b"Emp #,First,Last\n",
            content_type="text/csv",
        )

        DataImport.objects.create(
            company=self.company_a,
            uploaded_by=self.user_a,
            file=uploaded_file,
            filename="employees.csv",
            source_type=DataImport.SourceType.CSV,
            target_model="Employee",
            status=DataImport.Status.UPLOADED,
        )

        self.assertEqual(
            self.company_a.data_imports.count(),
            1,
        )

        self.assertEqual(
            self.company_b.data_imports.count(),
            0,
        )