from celery import shared_task
from django.core.management import call_command
import traceback

@shared_task
def sync_mssql_to_postgres_task():
    try:
        call_command('sync_mssql_to_postgres')
    except Exception as e:
        print("Error in sync_mssql_to_postgres_task:", e)
        traceback.print_exc()
        raise