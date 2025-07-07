from django.core.management.base import BaseCommand
from core.models import LIFTemplateFieldMap
from core.forms import PLACEHOLDER_CHOICES, LIF_FIELD_CHOICES

class Command(BaseCommand):
    help = "Fix LIFTemplateFieldMap mappings to match allowed choices"

    def handle(self, *args, **options):
        valid_placeholders = set(x[0] for x in PLACEHOLDER_CHOICES)
        valid_lif_fields = set(x[0] for x in LIF_FIELD_CHOICES)
        to_delete = []
        to_fix_placeholder = []
        to_fix_lif_field = []

        for m in LIFTemplateFieldMap.objects.all():
            if m.placeholder not in valid_placeholders or m.lif_field not in valid_lif_fields:
                self.stdout.write(f"Invalid mapping: {m.placeholder} → {m.lif_field}")
                # Option 1: Delete invalid mappings
                to_delete.append(m.id)
                # Option 2: (Optional) Fix to a default value instead of deleting
                # if m.placeholder not in valid_placeholders:
                #     m.placeholder = '{{national_id}}'
                #     to_fix_placeholder.append(m)
                # if m.lif_field not in valid_lif_fields:
                #     m.lif_field = 'national_id'
                #     to_fix_lif_field.append(m)

        if to_delete:
            LIFTemplateFieldMap.objects.filter(id__in=to_delete).delete()
            self.stdout.write(self.style.SUCCESS(f"Deleted {len(to_delete)} invalid mappings."))

        # Uncomment below if you want to fix instead of delete
        # for m in to_fix_placeholder + to_fix_lif_field:
        #     m.save()
        # self.stdout.write(self.style.SUCCESS(f"Fixed {len(to_fix_placeholder) + len(to_fix_lif_field)} mappings."))

        self.stdout.write(self.style.SUCCESS("Database mappings are now valid."))