
import csv
from django.core.management.base import BaseCommand
from priceanalysis.models import Analysis_ZipCode

class Command(BaseCommand):
    help = "Load ZIP/state list into Analysis_ZipCode using bulk_create"

    def add_arguments(self, parser):
        parser.add_argument(
            "--truncate",
            action="store_true",
            help="Truncate Analysis_ZipCode table before loading",
        )
        parser.add_argument(
            "--file",
            type=str,
            default="zip_state_list.csv",
            help="Path to the CSV file",
        )

    def handle(self, *args, **options):
        csv_file = options["file"]
        truncate = options["truncate"]

        if truncate:
            self.stdout.write("Truncating Analysis_ZipCode table...")
            Analysis_ZipCode.objects.all().delete()

        batch_size = 1000
        batch = []
        total = 0

        with open(csv_file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Handle either header format
                zip_code = row.get("zip_code") or row.get("PHYSICAL ZIP")
                state_code = row.get("state_code") or row.get("PHYSICAL STATE")
                if not zip_code or not state_code:
                    continue

                batch.append(
                    Analysis_ZipCode(zip_code=zip_code.strip(), state_code=state_code.strip())
                )

                if len(batch) >= batch_size:
                    Analysis_ZipCode.objects.bulk_create(batch, ignore_conflicts=True)
                    total += len(batch)
                    self.stdout.write(f"Inserted {total} rows...")
                    batch = []

            # Insert remaining rows
            if batch:
                Analysis_ZipCode.objects.bulk_create(batch, ignore_conflicts=True)
                total += len(batch)

        self.stdout.write(self.style.SUCCESS(f"Finished loading {total} ZIPs into Analysis_ZipCode"))