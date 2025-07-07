import csv
from django.core.management.base import BaseCommand
from core.models import BillingHistory


class Command(BaseCommand):
    help = "Export all billing history records to a CSV file"

    def add_arguments(self, parser):
        parser.add_argument(
            'output_path',
            type=str,
            help='Full file path where the billing data should be exported (e.g. C:\\path\\to\\billing_export.csv)'
        )

    def handle(self, *args, **options):
        output_path = options['output_path']

        try:
            with open(output_path, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "SLA No.", "Tranche No", "Invoice No", "Invoice Date",
                    "Due Date", "Payment Date", "Amount", "Billed"
                ])

                for bill in BillingHistory.objects.all().order_by("sla__sla_reference"):
                    writer.writerow([
                        bill.sla.sla_reference,
                        bill.invoice_type or "",
                        bill.invoice_number or "",
                        bill.invoice_date or "",
                        bill.due_date or "",
                        bill.payment_date or "",
                        f"{bill.amount:.2f}",
                        "Yes" if bill.billed else "No"
                    ])

            self.stdout.write(self.style.SUCCESS(f"✅ Export complete: {output_path}"))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"❌ Failed to export billing data: {e}"))
