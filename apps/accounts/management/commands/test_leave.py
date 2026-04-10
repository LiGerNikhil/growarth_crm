from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.accounts.models import Employee, Leave
from django.utils import timezone
from datetime import date, timedelta

class Command(BaseCommand):
    help = 'Test leave management functionality'

    def handle(self, *args, **options):
        self.stdout.write('Testing leave management...')

        # Check if there's a user with employee profile
        users = User.objects.all()
        if not users.exists():
            self.stdout.write(self.style.ERROR('No users found. Please create a user first.'))
            return

        user = users.first()
        if not hasattr(user, 'employee'):
            self.stdout.write(self.style.WARNING(f'User {user.username} has no employee profile. Creating one...'))
            # Create a basic employee profile
            employee = Employee.objects.create(
                user=user,
                first_name='Test',
                last_name='User',
                email=user.email,
                role='employee',
                employment_status='active'
            )
            self.stdout.write(self.style.SUCCESS(f'Created employee profile for {user.username}'))

        employee = user.employee

        # Create a sample leave application
        leave = Leave.objects.create(
            employee=employee,
            leave_type='annual',
            start_date=date.today() + timedelta(days=7),
            end_date=date.today() + timedelta(days=10),
            reason='Testing leave management',
            additional_notes='This is a test leave application'
        )

        self.stdout.write(self.style.SUCCESS(f'Created sample leave application: {leave}'))

        # Test the leave_list view by importing and calling it
        from apps.accounts.views import leave_list
        from django.test import RequestFactory

        factory = RequestFactory()
        request = factory.get('/accounts/leave/')
        request.user = user

        try:
            response = leave_list(request)
            self.stdout.write(self.style.SUCCESS('Leave list view works correctly!'))
            self.stdout.write(f'Response status: {response.status_code}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error in leave_list view: {e}'))

        self.stdout.write('Leave management test completed.')
