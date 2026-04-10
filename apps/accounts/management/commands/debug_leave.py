from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.accounts.models import Employee
from django.test import Client
from django.conf import settings

class Command(BaseCommand):
    help = 'Debug leave page issue'

    def handle(self, *args, **options):
        self.stdout.write('Debugging leave page issue...')

        # Temporarily add testserver to ALLOWED_HOSTS
        original_hosts = settings.ALLOWED_HOSTS[:]
        settings.ALLOWED_HOSTS.append('testserver')

        try:
            # Get first user
            users = User.objects.all()
            if not users.exists():
                self.stdout.write(self.style.ERROR('No users found'))
                return

            user = users.first()
            self.stdout.write(f'Testing with user: {user.username} (ID: {user.id})')

            # Check if user has employee profile
            try:
                employee = user.employee
                self.stdout.write(self.style.SUCCESS(f'User has employee profile: {employee.full_name}'))
                has_employee = True
            except Employee.DoesNotExist:
                self.stdout.write(self.style.WARNING('User does NOT have employee profile'))
                has_employee = False

            # Test the leave page
            client = Client()
            client.login(username=user.username, password='password')  # Assuming default password

            self.stdout.write('Testing leave page access...')
            response = client.get('/accounts/leave/', follow=True)

            self.stdout.write(f'Response status: {response.status_code}')
            self.stdout.write(f'Response redirect chain: {response.redirect_chain}')

            if response.status_code == 200:
                self.stdout.write(self.style.SUCCESS('Leave page loaded successfully'))
                if 'Leave Management' in response.content.decode():
                    self.stdout.write(self.style.SUCCESS('Leave page content found'))
                else:
                    self.stdout.write(self.style.WARNING('Leave page loaded but content may be missing'))
            elif response.status_code == 302:
                self.stdout.write(f'Redirected to: {response.url}')
                if 'dashboard' in response.url:
                    self.stdout.write('User was redirected to dashboard (no employee profile)')
                else:
                    self.stdout.write(f'User was redirected to: {response.url}')
            else:
                self.stdout.write(self.style.ERROR(f'Unexpected status code: {response.status_code}'))

        finally:
            # Restore original ALLOWED_HOSTS
            settings.ALLOWED_HOSTS[:] = original_hosts

        self.stdout.write('Debug completed.')
