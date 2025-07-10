from django.core.management.base import BaseCommand
from django.db import connections, transaction
from core.models import Group, SessionDate, ProjectPlan, Module, Learner, VenueBooking
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Sync data from MSSQL to Postgres for Group, SessionDate, ProjectPlan, Module, Learner"

    def handle(self, *args, **options):
        self.sync_modules()
        self.sync_learners()
        self.sync_groups()
        self.sync_projectplans()
        self.sync_sessiondates()
        

    def sync_groups(self):
        mapping = {
            'id': 'ID',
            'projectcode': 'ProjectCode',
            'name': 'Title',
            'start_date': 'StartDate',
            'end_date': 'EndDate',
            'project_lead_id': 'ProjectLeadId',
            'etqa_lead_id': 'ETQAAdministratorId',
        }
        with connections['mssql'].cursor() as cursor:
            cursor.execute("SELECT ID, ProjectCode, Title, StartDate, EndDate, ProjectLeadId, ETQAAdministratorId FROM Projects")
            columns = [col[0] for col in cursor.description]
            for row in cursor.fetchall():
                data = dict(zip(columns, row))
                # Remove project_lead_id and etqa_lead_id from defaults for now
                defaults = {k: data[v] for k, v in mapping.items() if k not in ['id', 'project_lead_id', 'etqa_lead_id']}
                obj, created = Group.objects.update_or_create(
                    id=data['ID'],
                    defaults=defaults
                )
                if created:
                    self.stdout.write(f"Group {obj.id} created.")
                else:
                    changed = []
                    for k in defaults:
                        if getattr(obj, k) != defaults[k]:
                            changed.append(k)
                    if changed:
                        self.stdout.write(f"Group {obj.id} updated fields: {changed}")
                    else:
                        self.stdout.write(f"Group {obj.id} already up-to-date, skipping.")

    def has_cancelled_booking(self, session_date_id):
        """
        Check if a session date has any cancelled bookings.
        If so, we should preserve the cancellation and not allow rebooking.
        """
        return VenueBooking.objects.filter(
            session_date_id=session_date_id,
            status='cancelled'
        ).exists()

    def sync_sessiondates(self):
        mapping = {
            'id': 'Id',
            'start_date': 'SessionStart',
            'end_date': 'SessionEnd',
            'preferred_training_methodology': 'PreferredTrainingMethodology',
            'project_plan_id': 'ProjectPlanId',
        }
        with connections['mssql'].cursor() as cursor:
            cursor.execute("SELECT Id, SessionStart, SessionEnd, PreferredTrainingMethodology, ProjectPlanId FROM ModuleBriefingSessionDates")
            columns = [col[0] for col in cursor.description]
            for row in cursor.fetchall():
                data = dict(zip(columns, row))
                defaults = {k: data[v] for k, v in mapping.items() if k != 'id'}

                # Check for cancelled bookings before making any changes
                has_cancelled = self.has_cancelled_booking(data['Id'])

                # Fetch the existing object if it exists
                try:
                    obj = SessionDate.objects.get(id=data['Id'])
                    created = False
                except SessionDate.DoesNotExist:
                    obj = None
                    created = True

                if created:
                    obj = SessionDate.objects.create(id=data['Id'], **defaults)
                    self.stdout.write(f"SessionDate {obj.id} created.")
                    
                    # If this is a new session date but it has cancelled bookings, 
                    # log this unusual situation
                    if has_cancelled:
                        self.stdout.write(
                            self.style.WARNING(
                                f"Warning: New SessionDate {obj.id} has existing cancelled bookings. "
                                "This may indicate data inconsistency."
                            )
                        )
                else:
                    changed = []
                    # Robust comparison: handle date/time/None/str mismatches
                    for k, v in defaults.items():
                        old = getattr(obj, k)
                        new = v
                        # Special handling for date/datetime fields
                        if k in ['start_date', 'end_date']:
                            # Convert both to date for comparison
                            try:
                                old_val = old.date() if hasattr(old, 'date') else old
                            except Exception:
                                old_val = old
                            try:
                                new_val = new.date() if hasattr(new, 'date') else new
                            except Exception:
                                new_val = new
                            # If still string, try to parse
                            if isinstance(old_val, str):
                                old_val = old_val[:10]
                            if isinstance(new_val, str):
                                new_val = new_val[:10]
                        else:
                            old_val = str(old) if old is not None else None
                            new_val = str(new) if new is not None else None
                        if old_val != new_val:
                            changed.append(k)
                            setattr(obj, k, v)
                    
                    if changed:
                        obj.save()
                        
                        # Special handling for sessions with cancelled bookings
                        if has_cancelled:
                            # Only delete non-cancelled bookings if start_date or end_date changed
                            if 'start_date' in changed or 'end_date' in changed:
                                # Delete only non-cancelled bookings to preserve cancellation status
                                deleted, deletion_details = VenueBooking.objects.filter(
                                    session_date_id=obj.id
                                ).exclude(status='cancelled').delete()
                                
                                # Count preserved cancelled bookings
                                cancelled_count = VenueBooking.objects.filter(
                                    session_date_id=obj.id,
                                    status='cancelled'
                                ).count()
                                
                                cache.set(f'sessiondate_changed_{obj.id}', True, timeout=3600)
                                self.stdout.write(
                                    self.style.SUCCESS(
                                        f"SessionDate {obj.id} updated fields: {changed}. "
                                        f"Deleted {deleted} non-cancelled booking(s). "
                                        f"Preserved {cancelled_count} cancelled booking(s)."
                                    )
                                )
                            else:
                                self.stdout.write(
                                    f"SessionDate {obj.id} updated fields: {changed}. "
                                    f"No bookings deleted (has cancelled bookings)."
                                )
                        else:
                            # Normal handling for sessions without cancelled bookings
                            if 'start_date' in changed or 'end_date' in changed:
                                deleted, _ = VenueBooking.objects.filter(session_date_id=obj.id).delete()
                                cache.set(f'sessiondate_changed_{obj.id}', True, timeout=3600)
                                self.stdout.write(
                                    f"SessionDate {obj.id} updated fields: {changed}. "
                                    f"Deleted {deleted} VenueBooking(s)."
                                )
                            else:
                                self.stdout.write(
                                    f"SessionDate {obj.id} updated fields: {changed}. "
                                    "No bookings deleted."
                                )
                    else:
                        if has_cancelled:
                            self.stdout.write(
                                f"SessionDate {obj.id} already up-to-date, skipping. "
                                "(Has cancelled bookings preserved)"
                            )
                        else:
                            self.stdout.write(f"SessionDate {obj.id} already up-to-date, skipping.")

    def sync_projectplans(self):
        mapping = {
            'id': 'Id',
            'remedial_briefing_session_start_date': 'RemedialBriefingSessionStartDate',
            'complete_formative_poe_date': 'CompleteFormativePoEDate',
            'summative_qa_session_start_date': 'SummativeQASessionStartDate',
            'complete_summative_poe_date': 'CompleteSummativePoEDate',
            'assessment_date': 'AssessmentDate',
            'summative_qa_session_end_date': 'SummativeQASessionEndDate',
            'remediation_submission_date': 'RemediationSubmissionDate',
            'remediation_assessment_date': 'RemediationAssessmentDate',
            'module_briefing_session_start_date': 'ModuleBriefingSessionStartDate',
            'module_briefing_session_end_date': 'ModuleBriefingSessionEndDate',
            'remedial_briefing_session_end_date': 'RemedialBriefingSessionEndDate',
            'assessment_book_in_date': 'AssessmentBookInDate',
            'assessment_book_out_date': 'AssessmentBookOutDate',
            'results_release_due_date': 'ResultsReleaseDueDate',
            'remediation_booked_in_date': 'RemediationBookedInDate',
            'remediation_booked_out_date': 'RemediationBookedOutDate',
            'remediation_results_release_due_date': 'RemediationResultsReleaseDueDate',
            # SKIP the following for now:
            # 'assessment_person_id': 'AssessmentPersonId',
            'group_id': 'ProjectId',
            'module_id': 'ModuleId',
            # 'module_briefing_session_person_id': 'ModuleBriefingSessionPersonId',
            # 'remedial_briefing_session_person_id': 'RemedialBriefingSessionPersonId',
            # 'remediation_assessment_person_id': 'RemediationAssessmentPersonId',
            # 'summative_qa_session_person_id': 'SummativeQASessionPersonId',
            # 'client_report_date': 'ClientReportDate',
            # 'client_report_person_id': 'ClientReportPersonId',
        }
        with connections['mssql'].cursor() as cursor:
            cursor.execute("""
                SELECT Id, RemedialBriefingSessionStartDate, CompleteFormativePoEDate, SummativeQASessionStartDate,
                       CompleteSummativePoEDate, AssessmentDate, SummativeQASessionEndDate, RemediationSubmissionDate,
                       RemediationAssessmentDate, ModuleBriefingSessionStartDate, ModuleBriefingSessionEndDate,
                       RemedialBriefingSessionEndDate, AssessmentBookInDate, AssessmentBookOutDate, ResultsReleaseDueDate,
                       RemediationBookedInDate, RemediationBookedOutDate, RemediationResultsReleaseDueDate,
                       ProjectId, ModuleId
                FROM ProjectPlans
            """)
            columns = [col[0] for col in cursor.description]
            for row in cursor.fetchall():
                data = dict(zip(columns, row))
                # Remove skipped fields from defaults
                defaults = {k: data[v] for k, v in mapping.items() if k != 'id'}
                obj, created = ProjectPlan.objects.update_or_create(
                    id=data['Id'],
                    defaults=defaults
                )
                if created:
                    self.stdout.write(f"ProjectPlan {obj.id} created.")
                else:
                    changed = []
                    for k in defaults:
                        if getattr(obj, k) != defaults[k]:
                            changed.append(k)
                    if changed:
                        self.stdout.write(f"ProjectPlan {obj.id} updated fields: {changed}")
                    else:
                        self.stdout.write(f"ProjectPlan {obj.id} already up-to-date, skipping.")

    def sync_modules(self):
        mapping = {
            'id': 'Id',
            'name': 'Title',
        }
        with connections['mssql'].cursor() as cursor:
            cursor.execute("SELECT Id, Title FROM Modules")
            columns = [col[0] for col in cursor.description]
            for row in cursor.fetchall():
                data = dict(zip(columns, row))
                defaults = {k: data[v] for k, v in mapping.items() if k != 'id'}
                obj, created = Module.objects.update_or_create(
                    id=data['Id'],
                    defaults=defaults
                )
                if created:
                    self.stdout.write(f"Module {obj.id} created.")
                else:
                    changed = []
                    for k in defaults:
                        if getattr(obj, k) != defaults[k]:
                            changed.append(k)
                    if changed:
                        self.stdout.write(f"Module {obj.id} updated fields: {changed}")
                    else:
                        self.stdout.write(f"Module {obj.id} already up-to-date, skipping.")

    def sync_learners(self):
        mapping = {
            'id': 'Id',
            'FirstName': 'FirstName',
            'Surname': 'Surname',
            'IDNumber': 'IDNumber',
            'Gender': 'Gender',
            'Equity': 'Equity',
            'EmailAddress': 'EmailAddress',
        }
        with connections['mssql'].cursor() as cursor:
            cursor.execute("SELECT Id, FirstName, Surname, IDNumber, Gender, Equity, EmailAddress FROM Learners")
            columns = [col[0] for col in cursor.description]
            for row in cursor.fetchall():
                data = dict(zip(columns, row))
                defaults = {k: data[v] for k, v in mapping.items() if k != 'id'}

                # Try to find by id or IDNumber
                learner = None
                if data.get('IDNumber'):
                    learner = Learner.objects.filter(IDNumber=data['IDNumber']).first()
                if not learner:
                    learner = Learner.objects.filter(id=data['Id']).first()

                if learner:
                    changed = []
                    for k, v in defaults.items():
                        if getattr(learner, k) != v:
                            setattr(learner, k, v)
                            changed.append(k)
                    learner.save()
                    if changed:
                        self.stdout.write(f"Learner {learner.id} updated fields: {changed}")
                    else:
                        self.stdout.write(f"Learner {learner.id} already up-to-date, skipping.")
                else:
                    obj = Learner.objects.create(id=data['Id'], **defaults)
                    self.stdout.write(f"Learner {obj.id} created.")