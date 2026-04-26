import csv
import os
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, IntegrityError
from priceanalysis.models import Analysis_ZipPrice, Analysis_ServiceType, Analysis_State


class Command(BaseCommand):
    help = "Load US pricing data from CSV into Analysis_ZipPrice"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            default="us_pricing.csv",
            help="Path to the CSV file",
        )
        parser.add_argument(
            "--truncate",
            action="store_true",
            help="Truncate Analysis_ZipPrice table before loading",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=1000,
            help="Number of rows per bulk insert",
        )

    def handle(self, *args, **options):
        csv_file = options["file"]
        truncate = options["truncate"]
        batch_size = options["batch_size"]

        if not os.path.exists(csv_file):
            raise CommandError(f"CSV file not found: {csv_file}")

        if truncate:
            self.stdout.write("Truncating Analysis_ZipPrice table...")
            Analysis_ZipPrice.objects.all().delete()

        total_inserted = 0
        row_errors = []
        batch = []

        # Caches
        service_type_cache = {}
        state_cache = {}

        try:
            with open(csv_file, newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)

                if not header:
                    raise CommandError("CSV file is empty or missing header.")

                with transaction.atomic():  # rollback on critical errors
                    for i, row in enumerate(reader, start=2):
                        if len(row) < 6:
                            row_errors.append(f"Row {i}: Missing required fields.")
                            continue

                        zip_code, state_code, service_type_name, avg_raw, min_raw, max_raw = row[:6]

                        # Parse prices
                        try:
                            avg_price = float(avg_raw)
                            min_price = float(min_raw)
                            max_price = float(max_raw)
                        except ValueError:
                            row_errors.append(f"Row {i}: Invalid price values.")
                            continue

                        # Service type cache
                        if service_type_name in service_type_cache:
                            service_type_obj = service_type_cache[service_type_name]
                        else:
                            service_type_obj, _ = Analysis_ServiceType.objects.get_or_create(
                                name=service_type_name
                            )
                            service_type_cache[service_type_name] = service_type_obj

                        # State cache
                        state_code_upper = state_code.upper()
                        if state_code_upper in state_cache:
                            state_obj = state_cache[state_code_upper]
                        else:
                            state_obj, _ = Analysis_State.objects.get_or_create(
                                code=state_code_upper,
                                defaults={"name": state_code_upper}
                            )
                            state_cache[state_code_upper] = state_obj

                        # Add to batch
                        batch.append(
                            Analysis_ZipPrice(
                                zip_code=zip_code.strip(),
                                state=state_obj,
                                service_type=service_type_obj,
                                avg_price=avg_price,
                                min_price=min_price,
                                max_price=max_price,
                            )
                        )

                        if len(batch) >= batch_size:
                            Analysis_ZipPrice.objects.bulk_create(batch)
                            total_inserted += len(batch)
                            self.stdout.write(f"Inserted {total_inserted} rows...")
                            batch = []

                    # Insert leftovers
                    if batch:
                        Analysis_ZipPrice.objects.bulk_create(batch)
                        total_inserted += len(batch)

        except IntegrityError as e:
            raise CommandError(f"Critical DB error: {str(e)}. No data saved.")

        # Show up to 5 non-critical row errors
        for err in row_errors[:5]:
            self.stdout.write(self.style.WARNING(err))

        self.stdout.write(
            self.style.SUCCESS(
                f"Finished loading {total_inserted} rows into Analysis_ZipPrice (with {len(row_errors)} non-critical errors)."
            )
        )