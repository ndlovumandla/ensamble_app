import requests
import json
import time
import os
from datetime import datetime
from django.core.management.base import BaseCommand

API_KEY = 'eyJhbGciOiJIUzI1NiIsImtpZCI6Ijg4YmYzNWNmLWM3ODEtNDQ3ZC1hYzc5LWMyODczMjNkNzg3ZCIsInR5cCI6IkpXVCJ9.eyJvcmdhbml6YXRpb25JZCI6IjFmNGYyNDQxLTQ3MGUtNGNhNy1iYTUxLTgzMmI2OTlkNTY1MiIsImludGVncmF0aW9uSWQiOiJmOWIxYjEyNi05YjU0LTQ5ODQtYjFhYS1kOGI1MGM4YTAyZTUiLCJjbGllbnRJZCI6IjNkZTNmODMwLWNiYzctNDZlNi1iOTZlLTVmMDE2NzcyMTgzMCIsImp0aSI6ImIxYzE3ZDM2LTczMmMtNDlkOS05MjMyLTEyZTE3Y2QyNTI5OSIsImlhdCI6MTc1MTM3NjExNiwiaXNzIjoiaHR0cHM6Ly93d3cuY29nbml0b2Zvcm1zLmNvbS8iLCJhdWQiOiJhcGkifQ.LlXhdzbRoutDVFHF9ZS82ApxS8Dt5unYn0tvlqab7_Y'  # <-- Replace with your real API key
BASE_URL = "https://www.cognitoforms.com/api"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def get_forms():
    url = f"{BASE_URL}/forms"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()

def get_entry(form_id, entry_id, retries=3, delay=5):
    url = f"{BASE_URL}/forms/{form_id}/entries/{entry_id}"
    for attempt in range(retries):
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            return None
        elif response.status_code == 429:
            retry_after = response.headers.get('Retry-After', delay)
            time.sleep(float(retry_after))
            continue
        else:
            break
    return None

class Command(BaseCommand):
    help = 'Fetch LIF entries from Cognito and save as JSON'

    def add_arguments(self, parser):
        parser.add_argument('--form', type=str, required=True, help='Cognito Form ID')
        parser.add_argument('--entry', type=str, help='Single Entry ID')
        parser.add_argument('--max', type=int, help='Max Entry ID to try (for range)')

    def handle(self, *args, **options):
        form_id = options['form']
        entry_id = options.get('entry')
        max_entry_id = options.get('max')
        entries = []

        if entry_id:
            entry = get_entry(form_id, entry_id)
            if entry:
                entries.append(entry)
        elif max_entry_id:
            for eid in range(1, max_entry_id + 1):
                self.stdout.write(f"Fetching entry {eid}")
                entry = get_entry(form_id, str(eid))
                if entry:
                    entries.append(entry)
        else:
            self.stdout.write(self.style.ERROR("Specify --entry or --max"))

        if entries:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"cognito_entries_{form_id}_{timestamp}.json"
            data_dir = os.path.join("ensemble_app", "core", "cognito_data")
            os.makedirs(data_dir, exist_ok=True)  # <-- Ensure directory exists
            with open(os.path.join(data_dir, filename), "w") as f:
                json.dump(entries, f, indent=2)
            self.stdout.write(self.style.SUCCESS(f"Saved {len(entries)} entries to {filename}"))
        else:
            self.stdout.write(self.style.WARNING("No entries found"))