import ast
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand


class ViewModelAnalyzer(ast.NodeVisitor):
    """
    Analyze a views.py file and identify Django model queryset usage.
    """

    def __init__(self, source):
        self.source = source
        self.lines = source.splitlines()
        self.results = []

    def get_source_line(self, lineno):
        if 1 <= lineno <= len(self.lines):
            return self.lines[lineno - 1].strip()
        return ""

    def is_model_queryset_call(self, node):
        """
        Detect patterns such as:

            Employee.objects.all()
            Employee.objects.filter(...)
            Customer.objects.get(...)
            Invoice.objects.exclude(...)
            Model.objects.order_by(...)
        """

        if not isinstance(node.func, ast.Attribute):
            return None

        queryset_methods = {
            "all",
            "filter",
            "exclude",
            "get",
            "get_or_create",
            "update_or_create",
            "order_by",
            "select_related",
            "prefetch_related",
            "values",
            "values_list",
            "annotate",
            "aggregate",
            "exists",
            "count",
            "first",
            "last",
        }

        if node.func.attr not in queryset_methods:
            return None

        objects_attr = node.func.value

        if not isinstance(objects_attr, ast.Attribute):
            return None

        if objects_attr.attr != "objects":
            return None

        model_name = objects_attr.value

        if isinstance(model_name, ast.Name):
            return model_name.id

        return None

    def analyze_call(self, node, model_name):
        source_line = self.get_source_line(node.lineno)

        scope = {
            "company": False,
            "created_by_user": False,
            "request_user": False,
            "unscoped_all": False,
        }

        try:
            call_source = ast.get_source_segment(
                self.source,
                node
            ) or source_line
        except Exception:
            call_source = source_line

        normalized = call_source.replace(" ", "")

        # Company scoping
        if (
            "company=request.user.company" in normalized
            or "company_id=request.user.company.id" in normalized
            or "company_id=request.user.company_id" in normalized
            or "company__in=" in normalized
        ):
            scope["company"] = True

        # User scoping
        if (
            "created_by_user=request.user" in normalized
            or "created_by_user_id=request.user.id" in normalized
            or "created_by_user_id=request.user.pk" in normalized
        ):
            scope["created_by_user"] = True

        # General request.user use
        if "request.user" in normalized:
            scope["request_user"] = True

        # Bare .all()
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "all"
        ):
            scope["unscoped_all"] = True

        self.results.append(
            {
                "model": model_name,
                "line": node.lineno,
                "source": call_source,
                "scope": scope,
            }
        )

    def visit_Call(self, node):
        model_name = self.is_model_queryset_call(node)

        if model_name:
            self.analyze_call(node, model_name)

        self.generic_visit(node)


class Command(BaseCommand):
    help = (
        "Audit Django views.py files for model queries and "
        "company/created_by_user scoping."
    )

    def handle(self, *args, **options):

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "ProForOps View / Model Scope Audit"
            )
        )
        self.stdout.write("=" * 80)
        self.stdout.write("")

        # ---------------------------------------------------------
        # Build model registry
        # ---------------------------------------------------------

        model_registry = {}

        for model in apps.get_models():

            model_name = model.__name__

            model_registry[model_name] = model

        # ---------------------------------------------------------
        # Locate views.py files
        # ---------------------------------------------------------

        base_dir = Path(settings.BASE_DIR).resolve()

        search_roots = [
            base_dir,
            base_dir.parent,
        ]

        view_files = []

        for root in search_roots:
            view_files.extend(root.rglob("views.py"))

        # Remove duplicates
        view_files = sorted(set(
            path.resolve()
            for path in view_files
        ))

        if not view_files:
            self.stdout.write(
                self.style.WARNING(
                    "No views.py files were found."
                )
            )
            return

        total_queries = 0
        suspicious_queries = 0

        # ---------------------------------------------------------
        # Process each views.py
        # ---------------------------------------------------------

        for view_file in sorted(view_files):

            # Skip virtual environments
            if any(
                part in {
                    ".venv",
                    "venv",
                    "env",
                    "site-packages",
                    "node_modules",
                    "__pycache__",
                }
                for part in view_file.parts
            ):
                continue

            try:
                source = view_file.read_text(
                    encoding="utf-8"
                )
            except UnicodeDecodeError:
                continue

            try:
                tree = ast.parse(source)
            except SyntaxError as exc:

                self.stdout.write(
                    self.style.ERROR(
                        f"SYNTAX ERROR: {view_file}"
                    )
                )

                self.stdout.write(
                    f"    {exc}"
                )

                continue

            analyzer = ViewModelAnalyzer(source)
            analyzer.visit(tree)

            if not analyzer.results:
                continue

            try:
                relative_path = view_file.relative_to(base_dir)
            except ValueError:
                relative_path = view_file

            self.stdout.write("")
            self.stdout.write(
                self.style.HTTP_INFO(
                    f"FILE: {relative_path}"
                )
            )
            self.stdout.write("-" * 80)

            for result in analyzer.results:

                total_queries += 1

                model_name = result["model"]
                line = result["line"]
                source_line = result["source"]
                scope = result["scope"]

                model = model_registry.get(model_name)

                # -------------------------------------------------
                # Unknown model
                # -------------------------------------------------

                if model is None:

                    self.stdout.write(
                        self.style.WARNING(
                            f"[UNKNOWN MODEL] "
                            f"{model_name} "
                            f"(line {line})"
                        )
                    )

                    self.stdout.write(
                        f"    {source_line}"
                    )

                    continue

                # -------------------------------------------------
                # Inspect model fields
                # -------------------------------------------------

                field_names = {
                    field.name
                    for field in model._meta.get_fields()
                }

                has_company = "company" in field_names
                has_created_by_user = (
                    "created_by_user" in field_names
                )

                # -------------------------------------------------
                # Determine query scope
                # -------------------------------------------------

                if scope["company"]:

                    query_scope = "COMPANY"

                elif scope["created_by_user"]:

                    query_scope = "CREATED_BY_USER"

                elif scope["unscoped_all"]:

                    query_scope = "UNSCOPED .ALL()"

                elif scope["request_user"]:

                    query_scope = "REQUEST.USER"

                else:

                    query_scope = "NO_DETECTED_SCOPE"

                # -------------------------------------------------
                # Determine severity
                # -------------------------------------------------

                suspicious = False

                if query_scope in {
                    "UNSCOPED .ALL()",
                    "NO_DETECTED_SCOPE",
                }:

                    if has_company or has_created_by_user:
                        suspicious = True

                if suspicious:
                    suspicious_queries += 1

                # -------------------------------------------------
                # Display
                # -------------------------------------------------

                if suspicious:

                    prefix = self.style.ERROR(
                        "[REVIEW]"
                    )

                elif query_scope == "COMPANY":

                    prefix = self.style.SUCCESS(
                        "[COMPANY]"
                    )

                elif query_scope == "CREATED_BY_USER":

                    prefix = self.style.SUCCESS(
                        "[USER]"
                    )

                else:

                    prefix = self.style.WARNING(
                        f"[{query_scope}]"
                    )

                self.stdout.write(
                    f"{prefix} "
                    f"{model_name} "
                    f"(line {line})"
                )

                self.stdout.write(
                    f"    {source_line}"
                )

                self.stdout.write(
                    f"    model.company: "
                    f"{'YES' if has_company else 'NO'}"
                )

                self.stdout.write(
                    f"    model.created_by_user: "
                    f"{'YES' if has_created_by_user else 'NO'}"
                )

                self.stdout.write(
                    f"    detected scope: "
                    f"{query_scope}"
                )

        # ---------------------------------------------------------
        # Summary
        # ---------------------------------------------------------

        self.stdout.write("")
        self.stdout.write("=" * 80)
        self.stdout.write(
            self.style.SUCCESS(
                "AUDIT SUMMARY"
            )
        )
        self.stdout.write("=" * 80)

        self.stdout.write(
            f"views.py files scanned: {len(view_files)}"
        )

        self.stdout.write(
            f"model queries found: {total_queries}"
        )

        self.stdout.write(
            f"queries requiring review: "
            f"{suspicious_queries}"
        )

        self.stdout.write("")

        if suspicious_queries:

            self.stdout.write(
                self.style.ERROR(
                    "Potentially unscoped model queries were found."
                )
            )

            self.stdout.write(
                "Review every [REVIEW] entry before changing code."
            )

        else:

            self.stdout.write(
                self.style.SUCCESS(
                    "No obvious unscoped company/user queries found."
                )
            )