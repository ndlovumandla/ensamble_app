import os
import pandas as pd
import re
from decimal import Decimal, ROUND_HALF_UP
from django.core.management.base import BaseCommand
from core.models import SLA

class Command(BaseCommand):
    help = 'Processes billing.xlsx and exports a cleaned CSV for billing import.'

    def handle(self, *args, **kwargs):
        input_path = r"C:\Users\34621\Documents\ensemble_app\billing.xlsx"
        output_path = r"C:\Users\34621\Documents\ensemble_app\billing_import.csv"
        sla_col = "SLA No."  # Adjust if necessary

        def round_float(val, decimals=2):
            if isinstance(val, float):
                return float(Decimal(str(val)).quantize(Decimal(f'1.{"0" * decimals}'), rounding=ROUND_HALF_UP))
            return val

        try:
            df = pd.read_excel(input_path)
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"❌ Failed to read Excel: {e}"))
            return

        output_rows = []

        for _, row in df.iterrows():
            sla = row.get(sla_col)
            for col in df.columns:
                if col != sla_col and "Tranche" in col:
                    month = col.replace(" Tranche", "")
                    tranche = row.get(col, "")
                    inv_date = row.get(month + " Invoice Date", "")
                    pay_date = row.get(month + " Payment Date", "")
                    amount = row.get(month + " Amount", "")

                    if pd.notna(tranche) and tranche:
                        match = re.match(r"(T\d+|initiation|progress|final)\s*([A-Za-z0-9\-]*)?", str(tranche).strip())
                        t_num = match.group(1) if match else ""
                        inv_num = match.group(2).strip() if match and match.group(2) else ""

                        output_rows.append({
                            "SLA No.": sla,
                            "Tranche No.": t_num,
                            "Invoice No.": inv_num,
                            "Invoice Date": inv_date if pd.notna(inv_date) else "",
                            "Due Date": month if not inv_num else "",
                            "Payment Date": pay_date if pd.notna(pay_date) else "",
                            "Amount": round_float(amount if pd.notna(amount) else "")
                        })

        output_df = pd.DataFrame(output_rows)
        output_df["Invoice No."] = output_df["Invoice No."].astype(str)

        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            output_df.to_csv(output_path, index=False)
            self.stdout.write(self.style.SUCCESS(f"✔ Created billing_import.csv at {output_path}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"❌ Failed to write CSV: {e}"))