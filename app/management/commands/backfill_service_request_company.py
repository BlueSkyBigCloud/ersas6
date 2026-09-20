from django.core.management.base import BaseCommand
from app.models import ServiceRequest


class Command(BaseCommand):
    help = "Backfill ServiceRequest.company from created_by_user.company"

    def handle(self, *args, **options):
        self.stdout.write(
            "Starting ServiceRequest company backfill..."
        )

        service_requests = (
            ServiceRequest.objects
            .select_related("created_by_user__company")
            .filter(company__isnull=True)
        )

        total = service_requests.count()

        self.stdout.write(
            f"ServiceRequests needing company: {total}"
        )

        updated = 0
        missing = []

        for service_request in service_requests:
            user = service_request.created_by_user

            if user and user.company_id:
                ServiceRequest.objects.filter(
                    pk=service_request.pk
                ).update(
                    company_id=user.company_id
                )

                updated += 1

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Updated ServiceRequest "
                        f"{service_request.pk} -> "
                        f"Company {user.company_id}"
                    )
                )

            else:
                missing.append(service_request.pk)

                self.stdout.write(
                    self.style.WARNING(
                        f"NO COMPANY: ServiceRequest "
                        f"{service_request.pk}"
                    )
                )

        self.stdout.write("")
        self.stdout.write("====================================")
        self.stdout.write("ServiceRequest Company Backfill")
        self.stdout.write("====================================")
        self.stdout.write(
            f"Total needing company: {total}"
        )
        self.stdout.write(
            f"Updated:               {updated}"
        )
        self.stdout.write(
            f"Missing company:       {len(missing)}"
        )

        if missing:
            self.stdout.write("")
            self.stdout.write(
                "ServiceRequests with no company:"
            )

            for service_request_id in missing:
                self.stdout.write(
                    f"  {service_request_id}"
                )
        else:
            self.stdout.write("")
            self.stdout.write(
                self.style.SUCCESS(
                    "All ServiceRequests were assigned a company."
                )
            )