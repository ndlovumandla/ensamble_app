from django.core.management.base import BaseCommand
from core.models import SessionDate, VenueBooking, Venue
from datetime import time, datetime

class Command(BaseCommand):
    help = 'Auto-book all virtual sessions that do not have a VenueBooking'

    def handle(self, *args, **options):
        virtual_sessions = SessionDate.objects.filter(
            preferred_training_methodology__icontains="virtual session"
        )
        virtual_venue = Venue.objects.filter(name__icontains="virtual session").first()
        if not virtual_venue:
            self.stdout.write(self.style.WARNING('No virtual venue found.'))
            return

        created_count = 0
        for session in virtual_sessions:
            exists = VenueBooking.objects.filter(session_date=session, venue=virtual_venue).exists()
            if not exists:
                start_dt = datetime.combine(session.start_date, time(8, 0))
                end_dt = datetime.combine(session.end_date, time(17, 0))
                VenueBooking.objects.create(
                    session_date=session,
                    venue=virtual_venue,
                    start_datetime=start_dt,
                    end_datetime=end_dt,
                    booking_purpose="Auto-booked virtual session",
                    status="booked"
                )
                created_count += 1
        self.stdout.write(self.style.SUCCESS(f"Auto-booked {created_count} virtual sessions."))