import os
import pandas as pd
from django.core.management.base import BaseCommand
from core.models import SLA, SLA_Qualifications


class Command(BaseCommand):
    help = 'Exports SLA totals to Excel with only SLA No. and Total Value'

    def handle(self, *args, **kwargs):
        output_path = r"C:\temp\sla_totals.xlsx"
        data = []

        for sla in SLA.objects.all().order_by("sla_reference"):
            total = 0.0
            quals = SLA_Qualifications.objects.filter(sla=sla)

            for qual in quals:
                qual_total = qual.learner_count * (
                    (qual.learnership or 0) +
                    (qual.recruitment or 0) +
                    (qual.hosting or 0) +
                    (qual.technology or 0) +
                    (qual.venue or 0) +
                    (qual.stipends or 0) +
                    (qual.consulting or 0)
                )
                total += qual_total

            data.append({
                "SLA No.": sla.sla_reference,
                "Total Value": round(total, 2)
            })

        df = pd.DataFrame(data)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_excel(output_path, index=False)

        self.stdout.write(self.style.SUCCESS(f"✔ Exported 2-column SLA totals to {output_path}"))
