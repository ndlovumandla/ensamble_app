import csv
import re
from django.core.management.base import BaseCommand
from core.models import SLA, SLA_Qualifications


class Command(BaseCommand):
    help = 'Import SLA Pricing from CSV and update SLA Qualifications'

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, required=True, help='Path to CSV file')

    def handle(self, *args, **options):
        file_path = options['file']

        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    try:
                        sla = SLA.objects.get(sla_reference=row["SLA No."].strip())
                        sla_quals = SLA_Qualifications.objects.filter(sla=sla)

                        if sla_quals.count() != 1:
                            self.stdout.write(self.style.WARNING(
                                f"[SKIPPED] {row['SLA No.']}: Not a single-qual SLA ({sla_quals.count()} quals)"
                            ))
                            continue

                        sla_qual = sla_quals.first()

                        sla_qual.learnership = float(row["Learnership"] or 0)
                        sla_qual.recruitment = float(row["Recruitment"] or 0)
                        sla_qual.hosting = float(row["Hosting"] or 0)
                        sla_qual.technology = float(row["Technology"] or 0)
                        sla_qual.venue = float(row["Venue"] or 0)
                        sla_qual.stipends = float(row["Stipends"] or 0)
                        sla_qual.consulting = float(row["Consulting"] or 0)

                        sla_qual.save()

                        self.stdout.write(self.style.SUCCESS(f"[UPDATED] SLA Qual for {sla.sla_reference}"))

                    except SLA.DoesNotExist:
                        self.stdout.write(self.style.ERROR(f"[ERROR] SLA {row['SLA No.']} not found"))

                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"[ERROR] SLA {row['SLA No.']} - {e}"))

            self.stdout.write(self.style.SUCCESS("✔ Pricing import complete."))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"[ERROR] File not found: {file_path}"))
