from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from apps.accounts.models import Attendance, Employee
import random

class Command(BaseCommand):
    help = 'Create sample attendance records for testing'

    def handle(self, *args, **options):
        # Get some employees
        employees = Employee.objects.filter(employment_status='active')[:5]
        
        if not employees:
            self.stdout.write('No active employees found')
            return
        
        # Create attendance records for the last 7 days
        for employee in employees:
            for days_ago in range(7):
                date = timezone.now().date() - timedelta(days=days_ago)
                
                # Check if attendance already exists
                if Attendance.objects.filter(employee=employee, date=date).exists():
                    continue
                
                # Create sample attendance
                start_time = timezone.make_aware(
                    datetime.combine(date, datetime.min.time().replace(hour=9, minute=30))
                )
                end_time = timezone.make_aware(
                    datetime.combine(date, datetime.min.time().replace(hour=18, minute=30))
                )
                
                # Randomly assign different statuses
                statuses = ['present', 'half_day', 'present', 'present', 'half_day', 'present', 'present']
                status = random.choice(statuses)
                
                # Create attendance without calling save() first to avoid the relationship issue
                attendance = Attendance(
                    employee=employee,
                    date=date,
                    start_time=start_time if status != 'absent' else None,
                    end_time=end_time if status != 'absent' else None,
                    status=status,
                    final_status=status,
                    total_hours=8.0 if status != 'half_day' else 4.0,
                    break_hours=1.0,
                    overtime_hours=0.0
                )
                
                # Save without triggering calculate_hours to avoid the relationship issue
                super(Attendance, attendance).save(force_insert=True, using='default')
                
                self.stdout.write(f'Created attendance for {employee.full_name} on {date} - {status}')
        
        self.stdout.write('Sample attendance records created successfully!')
