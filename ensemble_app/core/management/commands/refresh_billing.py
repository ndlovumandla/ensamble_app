import csv
from datetime import datetime
from django.core.management.base import BaseCommand
from core.models import SLA, BillingHistory
from dateutil import parser as date_parser


class Command(BaseCommand):
    help = "Clear all billing history and re-import clean data from CSV"

    def add_arguments(self, parser):
        parser.add_argument(
            'csv_path',
            type=str,
            help='Full path to the CSV file to import (e.g. billing_export.csv)'
        )

    def handle(self, *args, **options):
        csv_path = options['csv_path']
        created, errors = 0, 0

        self.stdout.write(self.style.WARNING("⚠️ Deleting all existing billing history..."))
        BillingHistory.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("✅ All existing billing records deleted."))

        try:
            with open(csv_path, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    sla_ref = row.get("SLA No.")
                    tranche = row.get("Tranche No") or "Not specified"

                    try:
                        sla = SLA.objects.get(sla_reference=sla_ref)

                        bill = BillingHistory(
                            sla=sla,
                            invoice_type=tranche,
                            invoice_number=row.get("Invoice No") or None,
                            invoice_date=self.parse_date(row.get("Invoice Date")),
                            due_date=self.parse_date(row.get("Due Date")),
                            payment_date=self.parse_date(row.get("Payment Date")),
                            amount=float(row.get("Amount") or 0.0),
                            billed=row.get("Billed", "").strip().lower() in ("yes", "true", "1")
                        )
                        bill.save()
                        created += 1
                        self.stdout.write(f"🧾 Created: SLA {sla_ref} | {tranche}")

                    except SLA.DoesNotExist:
                        self.stderr.write(f"❌ SLA not found: {sla_ref}")
                        errors += 1
                    except Exception as e:
                        self.stderr.write(f"⚠️ Error on SLA {sla_ref}, tranche {tranche}: {e}")
                        errors += 1

            self.stdout.write(self.style.SUCCESS(
                f"\n🎉 Done! {created} billing records imported, {errors} errors."
            ))

        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f"❌ File not found: {csv_path}"))

    def parse_date(self, date_str):
        if not date_str or not date_str.strip():
            return None
        try:
            return date_parser.parse(date_str.strip()).date()
        except Exception:
            raise ValueError(f"Unrecognised date format: {date_str}")
