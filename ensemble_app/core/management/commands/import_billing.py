import csv
from datetime import datetime
from django.core.management.base import BaseCommand
from core.models import SLA, BillingHistory
from dateutil import parser as date_parser


class Command(BaseCommand):
    help = "Import billing history from a CSV file"

    def add_arguments(self, parser):
        parser.add_argument(
            'csv_path',
            type=str,
            help='Full path to the CSV file to import (e.g. C:\\path\\to\\billing_import.csv)'
        )

    def handle(self, *args, **options):
        csv_path = options['csv_path']

        try:
            with open(csv_path, mode="r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                BillingHistory.objects.all().delete()  # ⚠️ Clear old records — backup first!

                for row in reader:
                    sla_ref = row.get("SLA No.")
                    try:
                        sla = SLA.objects.get(sla_reference=sla_ref)
                        BillingHistory.objects.create(
                            sla=sla,
                            invoice_date=self.parse_date(row.get("Invoice Date")),
                            due_date=self.parse_date(row.get("Due Date")),
                            invoice_type=row.get("Tranche No") or "Not specified",
                            invoice_number=row.get("Invoice No") or None,
                            payment_date=self.parse_date(row.get("Payment Date")),
                            amount=float(row.get("Amount", 0)) if row.get("Amount") else 0.0,
                            billed=bool(row.get("Invoice No") and row.get("Invoice Date"))
                        )
                        self.stdout.write(self.style.SUCCESS(
                            f"✅ Imported billing for {sla_ref}: {row.get('Tranche No')} ({row.get('Invoice No')})"
                        ))
                    except SLA.DoesNotExist:
                        self.stdout.write(self.style.ERROR(f"❌ SLA not found: {sla_ref}"))
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"⚠️ Error importing {sla_ref}: {e}"))
        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f"File not found: {csv_path}"))

    def parse_date(self, date_str):
        """Attempt to parse a date string in various common formats."""
        if not date_str or not date_str.strip():
            return None

        try:
            return datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
        except ValueError:
            pass

        try:
            return datetime.strptime(date_str.strip(), "%Y-%m-%d %H:%M:%S").date()
        except ValueError:
            pass

        try:
            return datetime.strptime(date_str.strip(), "%Y/%m/%d").date()
        except ValueError:
            pass

        try:
            return datetime.strptime(date_str.strip(), "%Y/%m/%d %H:%M:%S").date()
        except ValueError:
            pass

        try:
            return date_parser.parse(date_str.strip()).date()
        except Exception:
            raise ValueError(f"Unrecognised date format: {date_str}")
