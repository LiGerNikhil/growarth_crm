from django.db import models
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.db import signals
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db.models.signals import post_save, pre_save, post_delete
from django.db.models import Q, Sum
from django.core.exceptions import ValidationError
import os
import pytz
from datetime import datetime, time

# File size validation (10MB limit for employee documents)
def validate_file_size(value):
    """Validate that uploaded files are not larger than 10MB"""
    max_size = 10 * 1024 * 1024  # 10MB in bytes
    if value.size > max_size:
        raise ValidationError(f'File size cannot exceed 10MB. Current size: {value.size / (1024*1024):.1f}MB')

class Employee(models.Model):
    """Employee model with comprehensive onboarding details"""
    
    EMPLOYEE_TYPES = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
        ('intern', 'Intern'),
    ]
    
    DEPARTMENTS = [
        ('sales', 'Sales'),
        ('marketing', 'Marketing'),
        ('engineering', 'Engineering'),
        ('hr', 'Human Resources'),
        ('finance', 'Finance'),
        ('operations', 'Operations'),
        ('support', 'Customer Support'),
        ('admin', 'Administration'),
    ]
    
    STATUSES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('onboarding', 'Onboarding'),
        ('terminated', 'Terminated'),
    ]
    
    ROLES = [
        ('employee', 'Employee'),
        ('team_leader', 'Team Leader'),
        ('manager', 'Manager'),
        ('hr', 'HR'),
        ('admin', 'Admin'),
        ('superadmin', 'SuperAdmin'),
    ]
    
    # Link to Django User model for authentication
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee')
    
    # Basic Information
    employee_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    
    # Job Details
    employee_type = models.CharField(max_length=20, choices=EMPLOYEE_TYPES, default='full_time')
    department = models.CharField(max_length=20, choices=DEPARTMENTS)
    position = models.CharField(max_length=100)
    role = models.CharField(max_length=20, choices=ROLES, default='employee')
    
    # Hierarchy Relationships
    reports_to = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True, 
        related_name='subordinates',
        help_text="Reports to (Manager/Team Leader)"
    )
    manager = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True, 
        related_name='team_leaders',
        limit_choices_to={'role__in': ['manager', 'admin']},
        help_text="Manager for Team Leaders"
    )
    team_leader = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True, 
        related_name='team_members',
        limit_choices_to={'role': 'team_leader'},
        help_text="Team Leader for Employees"
    )
    
    # Onboarding Details
    hire_date = models.DateField()
    start_date = models.DateField()
    probation_end_date = models.DateField(blank=True, null=True)
    employment_status = models.CharField(max_length=20, choices=STATUSES, default='onboarding')
    
    # Compensation
    salary = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    bonus_percentage = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    
    # Personal Information
    date_of_birth = models.DateField(blank=True, null=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)
    
    # Emergency Contact
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    emergency_contact_relationship = models.CharField(max_length=50, blank=True)
    
    # System Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='created_employees')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Employee'
        verbose_name_plural = 'Employees'
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.employee_id or 'ID Pending'}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def days_employed(self):
        if self.start_date:
            return (timezone.now().date() - self.start_date).days
        return 0
    
    @property
    def is_admin(self):
        return self.role == 'admin'
    
    @property
    def is_superadmin(self):
        return self.role == 'superadmin'
    
    @property
    def is_manager(self):
        return self.role == 'manager'
    
    @property
    def is_hr(self):
        return self.role == 'hr'
    
    @property
    def is_team_leader(self):
        return self.role == 'team_leader'
    
    @property
    def can_bypass_geolocation(self):
        """Check if employee can bypass geolocation restrictions"""
        return self.role in ['superadmin', 'admin', 'hr', 'manager', 'team_leader']
    
    @property
    def requires_geolocation_check(self):
        """Check if employee requires geolocation verification for login"""
        return self.role == 'employee'
    
    @property
    def is_employee(self):
        return self.role == 'employee'
    
    @property
    def team_members_count(self):
        """Return the number of team members under this team leader"""
        return self.team_members.count()
    
    @property
    def team_leaders_count(self):
        """Return the number of team leaders under this manager"""
        return self.team_leaders.count()
    
    def can_manage_user(self, target_user):
        """Check if this user can manage the target user"""
        if self.is_superadmin:
            return True
        
        if self.is_admin:
            # Admin can manage managers, team leaders, employees, and HR
            return target_user.role in ['manager', 'team_leader', 'employee', 'hr']
        
        if self.is_hr:
            # HR can manage all employees except superadmins (same as admin access)
            return target_user.role != 'superadmin'
        
        if self.is_manager:
            # Manager can manage their team leaders and employees under those team leaders
            if target_user.is_team_leader and target_user.reports_to == self:
                return True
            if target_user.is_employee and target_user.reports_to and target_user.reports_to.reports_to == self:
                return True
        
        if self.is_team_leader:
            # Team leader can only manage employees assigned to them
            return target_user.is_employee and target_user.reports_to == self
        
        return False
    
    def can_view_user(self, target_user):
        """Check if this user can view the target user"""
        if self.is_superadmin:
            return True
        
        if self.is_admin:
            # Admin can view managers, team leaders, employees, and HR
            return target_user.role in ['manager', 'team_leader', 'employee', 'hr']
        
        if self.is_hr:
            # HR can view all employees except superadmins (same as admin access)
            return target_user.role != 'superadmin'
        
        if self.is_manager:
            # Manager can view their team leaders and employees under those team leaders
            if target_user.is_team_leader and target_user.reports_to == self:
                return True
            if target_user.is_employee and target_user.reports_to and target_user.reports_to.reports_to == self:
                return True
        
        if self.is_team_leader:
            # Team leader can view employees assigned to them
            return target_user.is_employee and target_user.team_leader == self
        
        # Employee can only view themselves
        return target_user == self
    
    def get_accessible_users(self):
        """Get all users this user can access"""
        if self.is_superadmin:
            return Employee.objects.all()  # Superadmin can access everyone including HR
        
        if self.is_admin:
            # Admin can access managers, team leaders, employees, and HR
            return Employee.objects.filter(role__in=['manager', 'team_leader', 'employee', 'hr'])
        
        if self.is_hr:
            # HR can access all employees
            return Employee.objects.all()
        
        if self.is_manager:
            # Get team leaders and their employees
            team_leaders = Employee.objects.filter(reports_to=self, role='team_leader', employment_status='active')
            team_member_ids = Employee.objects.filter(
                reports_to__in=team_leaders, 
                employment_status='active'
            ).values_list('id', flat=True)
            return Employee.objects.filter(
                models.Q(id__in=team_member_ids) | models.Q(id__in=team_leaders.values('id'))
            )
        
        if self.is_team_leader:
            return Employee.objects.filter(team_leader=self, employment_status='active')
        
        # Employee can only see themselves
        return Employee.objects.filter(id=self.id)
    
    def get_attendance_stats(self, start_date=None, end_date=None):
        """Get attendance statistics for this employee"""
        attendances = self.attendances.all()
        
        if start_date:
            attendances = attendances.filter(date__gte=start_date)
        if end_date:
            attendances = attendances.filter(date__lte=end_date)
        
        total_days = attendances.count()
        present_days = attendances.filter(status='present').count()
        late_days = attendances.filter(status='late').count()
        absent_days = attendances.filter(status='absent').count()
        
        # Calculate total hours
        total_hours = attendances.aggregate(
            total=Sum('total_hours')
        )['total'] or 0
        
        total_overtime = attendances.aggregate(
            total=Sum('overtime_hours')
        )['total'] or 0
        
        # Calculate attendance percentage
        attendance_percentage = (present_days / total_days * 100) if total_days > 0 else 0
        
        return {
            'total_days': total_days,
            'present_days': present_days,
            'late_days': late_days,
            'absent_days': absent_days,
            'total_hours': round(total_hours, 2),
            'total_overtime': round(total_overtime, 2),
            'attendance_percentage': round(attendance_percentage, 2),
        }
    
    @property
    def current_attendance(self):
        """Get today's attendance if active"""
        today = timezone.now().date()
        try:
            attendance = self.attendances.get(date=today, is_active=True)
            return attendance
        except Attendance.DoesNotExist:
            return None
    
    @property
    def is_currently_working(self):
        """Check if employee is currently working"""
        return self.current_attendance is not None
    
    @property
    def is_currently_on_break(self):
        """Check if employee is currently on break"""
        attendance = self.current_attendance
        if attendance:
            return attendance.breaks.filter(end_time__isnull=True).exists()
        return False
    
    def start_work(self):
        """Start work for today"""
        today = timezone.now().date()
        now = timezone.now()
        
        # Check if already have attendance record for today
        if self.attendances.filter(date=today).exists():
            return False, "Attendance record already exists for today"
        
        # Check if already working
        if self.is_currently_working:
            return False, "Already working"
        
        # Check if within shift hours (9:30 AM - 6:30 PM)
        expected_start = datetime.combine(today, time(9, 30))
        expected_end = datetime.combine(today, time(18, 30))
        expected_start = timezone.make_aware(expected_start)
        expected_end = timezone.make_aware(expected_end)
        
        if now < expected_start.replace(hour=8) or now > expected_end:
            return False, "Outside shift hours"
        
        # Create attendance record
        attendance = Attendance.objects.create(
            employee=self,
            date=today,
            start_time=now,
            is_active=True
        )
        
        # Check for late arrival
        if now > expected_start:
            minutes_late = int((now - expected_start).total_seconds() / 60)
            Violation.objects.create(
                employee=self,
                attendance=attendance,
                violation_type='late_arrival',
                description=f"Late arrival by {minutes_late} minutes",
                violation_time=now,
                expected_time=expected_start,
                time_difference_minutes=minutes_late
            )
        
        # Schedule automatic breaks
        # self._schedule_breaks(attendance)  # TODO: Implement automatic break scheduling
        
        return True, "Work started successfully"
    
    def end_work(self):
        """End work for today"""
        attendance = self.current_attendance
        if not attendance:
            return False, "Not currently working"
        
        now = timezone.now()
        attendance.end_time = now
        attendance.is_active = False
        attendance.save()
        
        # Check for early departure
        expected_end = datetime.combine(attendance.date, time(18, 30))
        expected_end = timezone.make_aware(expected_end)
        
        if now < expected_end:
            minutes_early = int((expected_end - now).total_seconds() / 60)
            Violation.objects.create(
                employee=self,
                attendance=attendance,
                violation_type='early_departure',
                description=f"Early departure by {minutes_early} minutes",
                violation_time=now,
                expected_time=expected_end,
                time_difference_minutes=-minutes_early
            )
        
        return True, "Work ended successfully"
    
    def start_break(self, break_type='other'):
        """Start a break for the current employee"""
        today = timezone.now().date()
        now = timezone.now()
        
        # Check if currently working
        if not self.is_currently_working:
            return False, "Not currently working"
        
        # Check if already on break
        if self.is_currently_on_break:
            return False, "Already on break"
        
        # Get current attendance
        attendance = self.current_attendance
        if not attendance:
            return False, "No active attendance found"
        # Check if it's within scheduled break times for auto-breaks
        # REMOVED: Time restrictions - employees can now take breaks at any time
        # if break_type in ['tea_morning', 'lunch', 'tea_afternoon']:
        #     # Allow starting auto-breaks within reasonable time windows
        #     break_windows = {
        #         'tea_morning': (time(10, 45), time(11, 30)),  # 10:45 AM - 11:30 AM
        #         'lunch': (time(12, 45), time(13, 45)),        # 12:45 PM - 1:45 PM
        #         'tea_afternoon': (time(15, 45), time(16, 30)) # 3:45 PM - 4:30 PM
        #     }
        #     
        #     if break_type in break_windows:
        #         start_window, end_window = break_windows[break_type]
        #         current_time = now.time()
        #         if not (start_window <= current_time <= end_window):
        #             return False, f"Can only start {break_type.replace('_', ' ')} break between {start_window.strftime('%I:%M %p')} and {end_window.strftime('%I:%M %p')}"

        # Create or update break record
        break_obj, created = Break.objects.get_or_create(
            attendance=attendance,
            break_type=break_type,
            start_time__isnull=False,
            end_time__isnull=True,
            defaults={'start_time': now}
        )
        
        if not created:
            return False, "Break already started"
        
        # Set start time if it wasn't set
        if not break_obj.start_time:
            break_obj.start_time = now
            break_obj.save()
        
        return True, f"{break_type.replace('_', ' ').title()} break started successfully"

    def end_break(self):
        """End the current break for the employee"""
        # Check if currently working
        if not self.is_currently_working:
            return False, "Not currently working"
        
        # Check if on break
        if not self.is_currently_on_break:
            return False, "Not currently on break"
        
        # Get current attendance
        attendance = self.current_attendance
        if not attendance:
            return False, "No active attendance found"
        
        # Find the active break (most recent one without end_time)
        active_break = attendance.breaks.filter(end_time__isnull=True).first()
        if not active_break:
            return False, "No active break found"
        
        now = timezone.now()
        
        # Check minimum break duration (5 minutes for tea breaks, 15 minutes for lunch)
        min_duration = {
            'tea_morning': 5,  # 5 minutes
            'lunch': 15,       # 15 minutes
            'tea_afternoon': 5, # 5 minutes
            'other': 1         # 1 minute for other breaks
        }.get(active_break.break_type, 1)
        
        if active_break.start_time:
            actual_duration = (now - active_break.start_time).total_seconds() / 60  # minutes
            if actual_duration < min_duration:
                return False, f"Break must be at least {min_duration} minutes long"
        
        # End the break
        active_break.end_time = now
        active_break.save()
        
        return True, f"{active_break.get_break_type_display()} ended successfully"
    
    def get_team_leaders(self):
        """Get team leaders for this manager"""
        if self.is_manager or self.is_admin or self.is_superadmin:
            return Employee.objects.filter(
                reports_to=self if not self.is_superadmin else None,
                role='team_leader',
                employment_status='active'
            )
        return Employee.objects.none()
    
    def get_team_members(self):
        """Get team members for this team leader"""
        if self.is_team_leader:
            return Employee.objects.filter(team_leader=self, employment_status='active')
        return Employee.objects.none()
    
    def get_full_name(self):
        """Get full name of employee"""
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_latest_phone_number(self):
        """Get the latest assigned phone number for this employee"""
        latest_phone = self.phone_numbers.filter(is_active=True).order_by('-assigned_date').first()
        return latest_phone.phone_number if latest_phone else None
    
    def get_all_phone_numbers(self):
        """Get all phone numbers assigned to this employee"""
        return self.phone_numbers.all()
    
    def get_role_display(self):
        """Get display name for employee role"""
        role_choices = {
            'employee': 'Employee',
            'team_leader': 'Team Leader', 
            'manager': 'Manager',
            'admin': 'Admin',
            'superadmin': 'Super Admin'
        }
        return role_choices.get(self.role, self.role.title())
    
    def get_all_underlying_users(self):
        """Get all users under this user in hierarchy"""
        if self.is_admin or self.is_superadmin:
            return Employee.objects.filter(role__in=['manager', 'team_leader', 'employee', 'hr'])
        
        if self.is_hr:
            # HR can see all employees except superadmins (same as admin access)
            return Employee.objects.exclude(role='superadmin')
        
        if self.is_manager:
            team_leaders = self.get_team_leaders()
            all_member_ids = []
            for tl in team_leaders:
                all_member_ids.extend(tl.get_team_members().values_list('id', flat=True))
            all_member_ids.extend(team_leaders.values_list('id', flat=True))
            return Employee.objects.filter(id__in=all_member_ids)
        
        if self.is_team_leader:
            return self.get_team_members()
        
        return Employee.objects.none()
    
    def save(self, *args, **kwargs):
        # Generate employee ID if not provided
        if not self.employee_id:
            last_employee = Employee.objects.all().order_by('employee_id').last()
            if last_employee and last_employee.employee_id:
                try:
                    last_num = int(last_employee.employee_id[3:])
                    self.employee_id = f"EMP{last_num + 1:04d}"
                except ValueError:
                    self.employee_id = "EMP0001"
            else:
                self.employee_id = "EMP0001"
        
        # Create/update user permissions based on role
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Set user permissions based on role
        self.set_user_permissions()
    
    def set_user_permissions(self):
        """Set Django user permissions based on employee role"""
        if not self.user:
            return
        
        # Remove staff status for non-manager roles
        if self.role == 'employee':
            self.user.is_staff = False
            self.user.is_superuser = False
            self.user.user_permissions.clear()
            self.user.groups.clear()
        
        elif self.role == 'team_leader':
            self.user.is_staff = True
            self.user.is_superuser = False
            self.set_team_leader_permissions()
        
        elif self.role == 'admin':
            self.user.is_staff = True
            self.user.is_superuser = False
            self.set_admin_permissions()
        
        elif self.role == 'manager':
            self.user.is_staff = True
            self.user.is_superuser = False
            self.set_manager_permissions()
        
        elif self.role == 'superadmin':
            self.user.is_staff = True
            self.user.is_superuser = True
            # SuperAdmin gets all permissions
        
        self.user.save()
    
    def set_team_leader_permissions(self):
        """Set permissions for team leaders"""
        self.user.user_permissions.clear()
        self.user.groups.clear()
        
        try:
            employee_ct = ContentType.objects.get_for_model(Employee)
            # Add view permissions for their team members
            view_permission = Permission.objects.get(
                content_type=employee_ct,
                codename='view_employee'
            )
            self.user.user_permissions.add(view_permission)
        except Permission.DoesNotExist:
            pass
    
    def set_admin_permissions(self):
        """Set permissions for admin users"""
        self.user.user_permissions.clear()
        self.user.groups.clear()
        
        try:
            employee_ct = ContentType.objects.get_for_model(Employee)
            # Add view and manage permissions for managers, team leaders, and employees
            permissions = Permission.objects.filter(
                content_type=employee_ct,
                codename__in=['view_employee', 'change_employee', 'add_employee', 'delete_employee']
            )
            self.user.user_permissions.add(*permissions)
        except Permission.DoesNotExist:
            pass
    def set_manager_permissions(self):
        """Set permissions for department managers"""
        self.user.user_permissions.clear()
        self.user.groups.clear()
        
        # Add view permissions for employees in their department
        try:
            employee_ct = ContentType.objects.get_for_model(Employee)
            view_permission = Permission.objects.get(
                content_type=employee_ct,
                codename='view_employee'
            )
            self.user.user_permissions.add(view_permission)
        except Permission.DoesNotExist:
            pass
    
    def set_hr_manager_permissions(self):
        """Set permissions for HR managers"""
        self.user.user_permissions.clear()
        self.user.groups.clear()
        
        try:
            employee_ct = ContentType.objects.get_for_model(Employee)
            # Add all employee permissions for HR
            permissions = Permission.objects.filter(content_type=employee_ct)
            self.user.user_permissions.add(*permissions)
        except:
            pass


class Team(models.Model):
    """Team model for organizing employees"""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    team_leader = models.OneToOneField(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='leading_team')
    department = models.CharField(max_length=20, choices=Employee.DEPARTMENTS)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Team'
        verbose_name_plural = 'Teams'
    
    def __str__(self):
        return f"{self.name} - {self.get_department_display()}"
    
    @property
    def member_count(self):
        """Return the number of active team members"""
        return Employee.objects.filter(team_leader=self.team_leader, employment_status='active').count()
    
    def get_members(self):
        """Get all active team members"""
        return Employee.objects.filter(team_leader=self.team_leader, employment_status='active')


class ManagerRequest(models.Model):
    """Model for tracking manager creation requests"""
    
    STATUSES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='manager_requests')
    requested_role = models.CharField(max_length=20, choices=Employee.ROLES)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUSES, default='pending')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='approved_manager_requests')
    approved_at = models.DateTimeField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Manager Request'
        verbose_name_plural = 'Manager Requests'
    
    def __str__(self):
        return f"{self.employee.full_name} - {self.get_requested_role_display()}"


class OnboardingTask(models.Model):
    """Onboarding checklist tasks for new employees"""
    
    STATUSES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('skipped', 'Skipped'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='onboarding_tasks')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUSES, default='pending')
    due_date = models.DateField(blank=True, null=True)
    completed_date = models.DateTimeField(blank=True, null=True)
    completed_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['due_date', 'created_at']
        verbose_name = 'Onboarding Task'
        verbose_name_plural = 'Onboarding Tasks'
    
    def __str__(self):
        return f"{self.title} - {self.employee.full_name}"


def get_upload_path(instance, filename):
    """Dynamic upload path for employee documents"""
    return f'employee_{instance.employee.id}/docs/{filename}'


class Document(models.Model):
    """Employee documents and files"""
    
    DOCUMENT_TYPES = [
        ('resume', 'Resume'),
        ('contract', 'Employment Contract'),
        ('id_proof', 'ID Proof'),
        ('address_proof', 'Address Proof'),
        ('experience_letter', 'Experience Letter'),
        ('salary_slip', 'Salary Slip'),
        ('bank_details', 'Bank Details/Passbook'),
        ('pan_card', 'PAN Card'),
        ('aadhaar_card', 'Aadhaar Card'),
        ('passport', 'Passport'),
        ('other', 'Other'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to=get_upload_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    
    # Bank details fields (for bank_details document type)
    bank_name = models.CharField(max_length=200, blank=True, null=True)
    account_number = models.CharField(max_length=50, blank=True, null=True)
    ifsc_code = models.CharField(max_length=20, blank=True, null=True)
    branch_name = models.CharField(max_length=200, blank=True, null=True)
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Document'
        verbose_name_plural = 'Documents'
    
    def __str__(self):
        return f"{self.title} - {self.employee.full_name}"


class ExcelBatch(models.Model):
    """Model to track Excel upload batches"""
    BATCH_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    batch_name = models.CharField(max_length=255)
    excel_file = models.FileField(upload_to='excel_batches/%Y/%m/')
    status = models.CharField(max_length=20, choices=BATCH_STATUS_CHOICES, default='pending')
    total_rows = models.IntegerField(default=0)
    processed_rows = models.IntegerField(default=0)
    failed_rows = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Excel Batch'
        verbose_name_plural = 'Excel Batches'
    
    def __str__(self):
        return f"{self.batch_name} - {self.status}"
    
    @property
    def progress_percentage(self):
        if self.total_rows == 0:
            return 0
        return int((self.processed_rows / self.total_rows) * 100)
    
    @property
    def is_completed(self):
        return self.status == 'completed'
    
    @property
    def is_failed(self):
        return self.status == 'failed'


class ExcelBatchRow(models.Model):
    """Model to store individual rows from Excel batches"""
    ROW_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processed', 'Processed'),
        ('failed', 'Failed'),
        ('skipped', 'Skipped'),
    ]
    
    batch = models.ForeignKey(ExcelBatch, on_delete=models.CASCADE, related_name='batch_rows')
    row_number = models.IntegerField()
    row_data = models.TextField()  # Store JSON data as text for SQLite compatibility
    status = models.CharField(max_length=20, choices=ROW_STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True, null=True)
    employee_created = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['row_number']
        verbose_name = 'Excel Batch Row'
        verbose_name_plural = 'Excel Batch Rows'
        unique_together = ['batch', 'row_number']
    
    def __str__(self):
        return f"Row {self.row_number} - {self.status}"
    
    def get_row_data(self):
        """Convert stored JSON text back to dictionary"""
        import json
        try:
            return json.loads(self.row_data)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_row_data(self, data):
        """Convert dictionary to JSON text for storage, handling pandas types"""
        import json
        import pandas as pd
        from datetime import datetime
        
        # Convert pandas types to serializable formats
        def serialize_value(value):
            # Handle NaN/NaT values first
            try:
                if pd.isna(value):
                    return None
            except:
                pass
            
            # Handle all Timestamp variants - convert to string if isoformat fails
            if 'Timestamp' in str(type(value)):
                try:
                    return str(value)
                except:
                    return str(value)
            
            # Handle datetime objects
            if isinstance(value, datetime):
                try:
                    return value.isoformat()
                except:
                    return str(value)
            
            # Handle any other non-serializable types
            try:
                json.dumps(value)
                return value
            except (TypeError, ValueError):
                return str(value)
        
        # Process the data
        if data:
            serialized_data = {}
            for k, v in data.items():
                serialized_data[k] = serialize_value(v)
            self.row_data = json.dumps(serialized_data)
        else:
            self.row_data = ""


class Lead(models.Model):
    """Model to store lead data from Excel batches"""
    LEAD_STATUS_CHOICES = [
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('interested', 'Interested'),
        ('not_interested', 'Not Interested'),
        ('not_eligible', 'Not Eligible'),
        ('converted', 'Converted'),
        ('follow_up', 'Follow Up Required'),
        ('file_login', 'File Login'),
        ('amount_disbursed', 'Amount Disbursed'),
    ]
    
    # Core metadata
    source = models.CharField(max_length=100, blank=True)  # Excel batch name or source type
    status = models.CharField(max_length=20, choices=LEAD_STATUS_CHOICES, default='new')
    notes = models.TextField(blank=True)
    
    # Assignment
    assigned_to = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_leads')
    assigned_at = models.DateTimeField(null=True, blank=True)
    assigned_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_leads_by')
    
    # All lead data stored as JSON (handles any Excel structure)
    data = models.TextField(blank=True)  # JSON data with all fields from Excel
    
    # Update tracking
    updated_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_leads')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_contacted = models.DateTimeField(null=True, blank=True)
    
    # Original batch reference
    batch_row = models.OneToOneField(ExcelBatchRow, on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Lead'
        verbose_name_plural = 'Leads'
    
    def __str__(self):
        name = self.get_full_name()
        return name or f"Lead {self.id}"
    
    def get_data(self):
        """Convert stored JSON text back to dictionary"""
        import json
        try:
            return json.loads(self.data) if self.data else {}
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_data(self, data_dict):
        """Convert dictionary to JSON text for storage, handling any pandas types"""
        import json
        import pandas as pd
        from pandas import Timestamp
        from datetime import datetime
        
        # Convert pandas types to serializable formats
        def serialize_value(value):
            # Debug: Print the type to see what's causing the error
            print(f"DEBUG: Processing value of type: {type(value)} - Value: {value}")
            
            # Handle NaN/NaT values first
            try:
                if pd.isna(value):
                    return None
            except:
                pass
            
            # Handle pandas Timestamp objects first (more specific)
            if 'pandas.Timestamp' in str(type(value)):
                try:
                    return value.isoformat()
                except:
                    return str(value)
            
            # Handle datetime objects
            if isinstance(value, datetime):
                try:
                    return value.isoformat()
                except:
                    return str(value)
            
            # Handle any other non-serializable types
            try:
                json.dumps(value)
                return value
            except (TypeError, ValueError) as e:
                print(f"DEBUG: JSON serialization failed for {type(value)}: {e}")
                return str(value)
        
        # Process the dictionary row by row
        if data_dict:
            serialized_data = {}
            for k, v in data_dict.items():
                serialized_data[k] = serialize_value(v)
            self.data = json.dumps(serialized_data)
        else:
            self.data = ""
    
    def get_full_name(self):
        """Get full name from data, trying various field names"""
        data = self.get_data()
        
        # Try common name field variations
        name_fields = ['name', 'full_name', 'full name', 'firstname lastname', 'first_name last_name', 'applicant name']
        for field in name_fields:
            if field in data and data[field] and str(data[field]).strip():
                return str(data[field]).strip()
        
        # Try separate first/last name
        first = data.get('first_name', '').strip() or data.get('firstname', '').strip()
        last = data.get('last_name', '').strip() or data.get('lastname', '').strip()
        if first or last:
            return f"{first} {last}".strip()
        
        return ""
    
    def get_email(self):
        """Get email from data"""
        data = self.get_data()
        return data.get('email', '').strip()
    
    def get_phone(self):
        """Get phone from data"""
        data = self.get_data()
        return data.get('mobile no.', '').strip() or data.get('phone', '').strip()
    
    def get_company(self):
        """Get company from data"""
        data = self.get_data()
        return data.get('company', '').strip()
    
    def get_position(self):
        """Get position from data"""
        data = self.get_data()
        return data.get('position', '').strip()
    
    def is_forwarded_to(self, employee):
        """Check if this lead is forwarded to a specific employee"""
        return self.forwards.filter(forwarded_to=employee).exists()
    
    def get_forward_to_employee(self, employee):
        """Get the forward record for a specific employee"""
        return self.forwards.filter(forwarded_to=employee).first()
    
    def is_forwarded(self):
        """Check if this lead is forwarded to any employee"""
        return self.forwards.exists()
    
    def save(self, *args, **kwargs):
        # Track who updated (if user is provided in context)
        from django.utils import timezone
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)


class LeadForward(models.Model):
    """Model to track leads forwarded from admin to employees"""
    
    # Lead information (stored as fields instead of foreign key)
    lead_id = models.CharField(
        max_length=100, 
        default='', 
        help_text='ID of the lead being forwarded'
    )
    lead_name = models.CharField(
        max_length=255, 
        default='', 
        help_text='Name of the lead'
    )
    lead_email = models.EmailField(
        blank=True, 
        help_text='Email of the lead', 
        max_length=254, 
        null=True
    )
    lead_phone = models.CharField(
        blank=True, 
        default='', 
        help_text='Phone number of the lead', 
        max_length=20, 
        null=True
    )
    lead_source = models.CharField(
        default='', 
        help_text='Source of the lead (e.g., Excel sheet name)', 
        max_length=100
    )
    
    # Forward relationships
    forwarded_to = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='received_forwards')
    forwarded_by = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='sent_forwards')
    
    # Forward details
    notes = models.TextField(
        blank=True, 
        default='', 
        help_text='Additional notes from team leader', 
        null=True
    )
    employee_notes = models.TextField(
        blank=True, 
        default='', 
        help_text='Notes added by employee', 
        null=True
    )
    
    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('forwarded', 'Forwarded'),
            ('accepted', 'Accepted'),
            ('rejected', 'Rejected'),
            ('completed', 'Completed'),
        ],
        default='pending',
        help_text='Current status of the forwarded lead'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True, 
        help_text='When the record was created'
    )
    forwarded_at = models.DateTimeField(
        auto_now_add=True, 
        help_text='When the lead was forwarded'
    )
    updated_at = models.DateTimeField(
        auto_now=True, 
        help_text='When the record was last updated'
    )
    accepted_at = models.DateTimeField(
        blank=True, 
        default=None, 
        help_text='When the lead was accepted by employee', 
        null=True
    )
    completed_at = models.DateTimeField(
        blank=True, 
        default=None, 
        help_text='When the lead was completed', 
        null=True
    )
    
    class Meta:
        ordering = ['-forwarded_at']
        verbose_name = 'Lead Forward'
        verbose_name_plural = 'Lead Forwards'
        indexes = [
            models.Index(fields=['forwarded_by', 'status'], name='accounts_le_forward_22601f_idx'),
            models.Index(fields=['forwarded_to', 'status'], name='accounts_le_forward_8783ba_idx'),
            models.Index(fields=['forwarded_at'], name='accounts_le_forward_db6b3b_idx'),
        ]
    
    def __str__(self):
        return f"Lead {self.lead_id} forwarded to {self.forwarded_to.get_full_name()}"
    
    def save(self, *args, **kwargs):
        # Update timestamps based on status changes
        from django.utils import timezone
        if self.status == 'accepted' and not self.accepted_at:
            self.accepted_at = timezone.now()
        elif self.status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()
        
        super().save(*args, **kwargs)


class LoginStatistics(models.Model):
    """Track login statistics for managers and team leaders"""
    
    manager = models.ForeignKey(
        Employee, 
        on_delete=models.CASCADE, 
        related_name='manager_login_stats',
        limit_choices_to={'role__in': ['manager', 'admin', 'superadmin']},
        help_text="Manager responsible for these statistics"
    )
    
    team_leader = models.ForeignKey(
        Employee, 
        on_delete=models.CASCADE, 
        related_name='team_leader_login_stats',
        limit_choices_to={'role': 'team_leader'},
        null=True, 
        blank=True,
        help_text="Team leader (optional - for manager-level stats)"
    )
    
    file_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of files processed"
    )
    
    login_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of logins recorded"
    )
    
    total_count = models.PositiveIntegerField(
        default=0,
        help_text="Total count for tracking"
    )
    
    date = models.DateField(
        default=timezone.now,
        help_text="Date for these statistics"
    )
    
    notes = models.TextField(
        blank=True,
        help_text="Additional notes or comments"
    )
    
    # System fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True,
        related_name='updated_login_stats'
    )
    
    class Meta:
        ordering = ['-date', 'manager', 'team_leader']
        verbose_name = 'Login Statistics'
        verbose_name_plural = 'Login Statistics'
        unique_together = ['manager', 'team_leader', 'date']
    
    def __str__(self):
        if self.team_leader:
            return f"{self.manager.full_name} - {self.team_leader.full_name} ({self.date})"
        return f"{self.manager.full_name} ({self.date})"


class UserActivityLog(models.Model):
    """Model to track user login/logout activities and session duration"""
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='activity_logs'
    )
    
    login_time = models.DateTimeField(
        help_text="Time when user logged in (IST)"
    )
    
    logout_time = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Time when user logged out (IST)"
    )
    
    session_duration = models.DurationField(
        null=True, 
        blank=True,
        help_text="Total duration of the session"
    )
    
    ip_address = models.GenericIPAddressField(
        null=True, 
        blank=True,
        help_text="IP address from which user logged in"
    )
    
    user_agent = models.TextField(
        null=True, 
        blank=True,
        help_text="Browser/device information"
    )
    
    is_active_session = models.BooleanField(
        default=True,
        help_text="Whether this session is currently active"
    )
    
    # System fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-login_time']
        verbose_name = 'User Activity Log'
        verbose_name_plural = 'User Activity Logs'
    
    def __str__(self):
        return f"{self.user.username} - {self.get_login_time_ist()} ({'Active' if self.is_active_session else 'Completed'})"
    
    def get_login_time_ist(self):
        """Get login time in Indian Standard Time"""
        ist = pytz.timezone('Asia/Kolkata')
        if self.login_time:
            return self.login_time.astimezone(ist).strftime('%Y-%m-%d %H:%M:%S')
        return 'N/A'
    
    def get_logout_time_ist(self):
        """Get logout time in Indian Standard Time"""
        ist = pytz.timezone('Asia/Kolkata')
        if self.logout_time:
            return self.logout_time.astimezone(ist).strftime('%Y-%m-%d %H:%M:%S')
        return 'N/A'
    
    def get_session_duration_display(self):
        """Get formatted session duration"""
        if self.session_duration:
            total_seconds = int(self.session_duration.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            if hours > 0:
                return f"{hours}h {minutes}m {seconds}s"
            elif minutes > 0:
                return f"{minutes}m {seconds}s"
            else:
                return f"{seconds}s"
        return 'N/A'
    
    def calculate_session_duration(self):
        """Calculate and save session duration"""
        if self.login_time and self.logout_time:
            self.session_duration = self.logout_time - self.login_time
            self.save()
        return self.session_duration


class EmployeePhone(models.Model):
    """Model to manage phone number assignments to employees"""
    
    PHONE_TYPES = [
        ('primary', 'Primary'),
        ('secondary', 'Secondary'),
        ('official', 'Official'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='phone_numbers')
    phone_number = models.CharField(max_length=20, unique=True)
    phone_type = models.CharField(max_length=20, choices=PHONE_TYPES, default='primary')
    is_active = models.BooleanField(default=True)
    assigned_date = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-assigned_date']
        verbose_name = 'Employee Phone Number'
        verbose_name_plural = 'Employee Phone Numbers'
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.phone_number}"


class LeadActivityLog(models.Model):
    """Model to track all lead interactions and updates"""
    
    ACTION_TYPES = [
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('assigned', 'Assigned'),
        ('unassigned', 'Unassigned'),
        ('status_changed', 'Status Changed'),
        ('note_added', 'Note Added'),
        ('contacted', 'Contacted'),
        ('converted', 'Converted'),
        ('deleted', 'Deleted'),
    ]
    
    lead = models.ForeignKey(
        Lead, 
        on_delete=models.CASCADE, 
        related_name='activity_logs'
    )
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='lead_activities'
    )
    
    action_type = models.CharField(
        max_length=20,
        choices=ACTION_TYPES,
        help_text="Type of action performed"
    )
    
    old_value = models.TextField(
        null=True, 
        blank=True,
        help_text="Previous value before update"
    )
    
    new_value = models.TextField(
        null=True, 
        blank=True,
        help_text="New value after update"
    )
    
    description = models.TextField(
        help_text="Detailed description of the action"
    )
    
    ip_address = models.GenericIPAddressField(
        null=True, 
        blank=True,
        help_text="IP address from which action was performed"
    )
    
    user_agent = models.TextField(
        null=True, 
        blank=True,
        help_text="Browser/device information"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Lead Activity Log'
        verbose_name_plural = 'Lead Activity Logs'
    
    def __str__(self):
        return f"{self.user.username} - {self.get_action_type_display()} - {self.created_at}"
    
    def get_created_at_ist(self):
        """Get created at time in Indian Standard Time"""
        ist = pytz.timezone('Asia/Kolkata')
        if self.created_at:
            return self.created_at.astimezone(ist).strftime('%Y-%m-%d %H:%M:%S')
        return 'N/A'
    
    def get_action_description(self):
        """Generate human-readable description of the action"""
        if self.action_type == 'created':
            return f"Created lead: {self.lead.get_full_name() if self.lead else 'Unknown'}"
        elif self.action_type == 'updated':
            return f"Updated lead: {self.lead.get_full_name() if self.lead else 'Unknown'}"
        elif self.action_type == 'assigned':
            return f"Assigned lead to {self.lead.assigned_to.get_full_name() if self.lead and self.lead.assigned_to else 'Unknown'}"
        elif self.action_type == 'unassigned':
            return f"Unassigned lead from {self.lead.assigned_to.get_full_name() if self.lead and self.lead.assigned_to else 'Unknown'}"
        elif self.action_type == 'status_changed':
            if self.old_value and self.new_value:
                return f"Changed status from '{self.old_value}' to '{self.new_value}'"
            return f"Changed lead status"
        elif self.action_type == 'note_added':
            return f"Added note: {self.description[:50]}{'...' if len(self.description) > 50 else ''}"
        elif self.action_type == 'contacted':
            return f"Contacted lead: {self.lead.get_full_name() if self.lead else 'Unknown'}"
        elif self.action_type == 'converted':
            return f"Converted lead: {self.lead.get_full_name() if self.lead else 'Unknown'}"
        elif self.action_type == 'deleted':
            return f"Deleted lead: {self.lead.get_full_name() if self.lead else 'Unknown'}"
        else:
            return f"Performed action: {self.get_action_type_display()}"


def log_lead_activity(lead, user, action_type, old_value=None, new_value=None, description=None, request=None):
    """
    Helper function to log lead activities
    """
    try:
        # Get IP address and user agent from request if available
        ip_address = None
        user_agent = None
        if request:
            # Get client IP address
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0]
            else:
                ip_address = request.META.get('REMOTE_ADDR')
            
            # Get user agent
            user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Create activity log
        LeadActivityLog.objects.create(
            lead=lead,
            user=user,
            action_type=action_type,
            old_value=str(old_value) if old_value else None,
            new_value=str(new_value) if new_value else None,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent
        )
    except Exception as e:
        # Log error but don't break main flow
        print(f"Error logging lead activity: {e}")
    
    @property
    def display_name(self):
        """Get display name for the statistics entry"""
        if self.team_leader:
            return f"{self.manager.full_name} - {self.team_leader.full_name}"
        return self.manager.full_name
    
    def get_created_at_display(self):
        """Get formatted created at time for admin display"""
        return self.created_at.strftime('%Y-%m-%d %H:%M')


# Signal handlers for user activity tracking
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.utils import timezone

@receiver(user_logged_in)
def user_login_handler(sender, request, user, **kwargs):
    """Handle user login signal"""
    try:
        # Get client IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')
        
        # Get user agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Create activity log entry
        UserActivityLog.objects.create(
            user=user,
            login_time=timezone.now(),
            ip_address=ip_address,
            user_agent=user_agent,
            is_active_session=True
        )
    except Exception as e:
        # Log error but don't break login process
        print(f"Error creating login activity log: {e}")


@receiver(user_logged_out)
def user_logout_handler(sender, request, user, **kwargs):
    """Handle user logout signal"""
    try:
        if user:
            # Find most recent active session for this user
            active_session = UserActivityLog.objects.filter(
                user=user,
                is_active_session=True
            ).latest('login_time')
            
            if active_session:
                # Update session with logout time and calculate duration
                active_session.logout_time = timezone.now()
                active_session.is_active_session = False
                active_session.calculate_session_duration()
    except Exception as e:
        # Log error but don't break logout process
        print(f"Error updating logout activity log: {e}")


# Lead activity tracking signals
@receiver(post_save, sender=Lead)
def lead_post_save_handler(sender, instance, created, **kwargs):
    """Handle lead creation and updates"""
    try:
        # Get the current user from the instance if it has assigned_by field
        # or use a default system user for system-generated activities
        user = getattr(instance, 'assigned_by', None)
        if not user and hasattr(instance, '_current_user'):
            user = getattr(instance, '_current_user', None)
        
        if user:
            if created:
                # Lead was created
                LeadActivityLog.objects.create(
                    lead=instance,
                    user=user,
                    action_type='created',
                    description=f"Created new lead: {instance.get_full_name()}"
                )
            else:
                # Lead was updated
                LeadActivityLog.objects.create(
                    lead=instance,
                    user=user,
                    action_type='updated',
                    description=f"Updated lead: {instance.get_full_name()}"
                )
    except Exception as e:
        print(f"Error creating lead activity log: {e}")


@receiver(post_delete, sender=Lead)
def lead_post_delete_handler(sender, instance, **kwargs):
    """Handle lead deletion"""
    try:
        # Get the current user from the instance if available
        user = getattr(instance, '_current_user', None)
        
        if user:
            LeadActivityLog.objects.create(
                lead=instance,
                user=user,
                action_type='deleted',
                description=f"Deleted lead: {instance.get_full_name()}"
            )
    except Exception as e:
        print(f"Error creating lead deletion activity log: {e}")


# Custom function to log lead assignments
def log_lead_assignment(lead, assigned_to, assigned_by=None):
    """Log lead assignment activity"""
    try:
        if assigned_by:
            LeadActivityLog.objects.create(
                lead=lead,
                user=assigned_by,
                action_type='assigned',
                old_value=lead.assigned_to.get_full_name() if lead.assigned_to else None,
                new_value=assigned_to.get_full_name(),
                description=f"Assigned lead '{lead.get_full_name()}' to {assigned_to.get_full_name()}"
            )
    except Exception as e:
        print(f"Error logging lead assignment: {e}")


# Custom function to log lead unassignment
def log_lead_unassignment(lead, unassigned_by=None):
    """Log lead unassignment activity"""
    try:
        if unassigned_by:
            LeadActivityLog.objects.create(
                lead=lead,
                user=unassigned_by,
                action_type='unassigned',
                old_value=lead.assigned_to.get_full_name() if lead.assigned_to else None,
                new_value=None,
                description=f"Unassigned lead '{lead.get_full_name()}' from {lead.assigned_to.get_full_name() if lead.assigned_to else 'unassigned'}"
            )
    except Exception as e:
        print(f"Error logging lead unassignment: {e}")


# Custom function to log lead status changes
def log_lead_status_change(lead, old_status, new_status, changed_by=None):
    """Log lead status change activity"""
    try:
        if changed_by:
            LeadActivityLog.objects.create(
                lead=lead,
                user=changed_by,
                action_type='status_changed',
                old_value=old_status,
                new_value=new_status,
                description=f"Changed lead status from '{old_status}' to '{new_status}' for {lead.get_full_name()}"
            )
    except Exception as e:
        print(f"Error logging lead status change: {e}")


class Attendance(models.Model):
    """Model to track employee attendance with shift timings"""

    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('early_leave', 'Early Leave'),
        ('half_day', 'Half Day'),
        ('full_day_present', 'Full Day Present'),
    ]

    FINAL_STATUS_CHOICES = [
        ('auto_calculated', 'Auto Calculated'),
        ('manually_corrected', 'Manually Corrected'),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='attendances'
    )
    date = models.DateField(help_text="Attendance date")
    start_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Actual start time"
    )
    end_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Actual end time"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='present'
    )

    # Shift timings (9:30 AM - 6:30 PM)
    expected_start_time = models.TimeField(
        default='09:30:00',
        help_text="Expected start time (9:30 AM)"
    )
    expected_end_time = models.TimeField(
        default='18:30:00',
        help_text="Expected end time (6:30 PM)"
    )

    # Calculated fields
    total_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Total working hours"
    )
    overtime_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Overtime hours after 6:30 PM"
    )
    break_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Total break time"
    )

    # Manual override fields for HR/Admin
    final_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='present',
        help_text="Final status after manual correction"
    )
    correction_status = models.CharField(
        max_length=20,
        choices=FINAL_STATUS_CHOICES,
        default='auto_calculated',
        help_text="Whether status is auto-calculated or manually corrected"
    )
    corrected_by = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='corrected_attendances',
        help_text="HR/Admin who corrected this attendance"
    )
    corrected_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the attendance was corrected"
    )
    correction_notes = models.TextField(
        blank=True,
        null=True,
        help_text="Notes for manual correction"
    )

    # Flags
    is_active = models.BooleanField(
        default=False,
        help_text="Whether employee is currently working"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
        unique_together = ['employee', 'date']
        verbose_name = 'Attendance'
        verbose_name_plural = 'Attendances'

    def __str__(self):
        return f"{self.employee.user.username} - {self.date}"

    @property
    def shift_duration(self):
        """Calculate total shift duration in hours"""
        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time
            return round(duration.total_seconds() / 3600, 2)
        return 0

    @property
    def is_late(self):
        """Check if employee started late"""
        if self.start_time:
            expected_start = datetime.combine(self.date, self.expected_start_time)
            expected_start = timezone.make_aware(expected_start)
            return self.start_time > expected_start
        return False

    @property
    def is_early_leave(self):
        """Check if employee left early"""
        if self.end_time:
            expected_end = datetime.combine(self.date, self.expected_end_time)
            expected_end = timezone.make_aware(expected_end)
            return self.end_time < expected_end
        return False

    def calculate_hours(self):
        """Calculate total hours, overtime, and break time"""
        if not self.start_time or not self.end_time:
            return

        # Get all breaks for this attendance
        breaks = self.breaks.all()
        total_break_time = sum(
            (b.end_time - b.start_time).total_seconds() / 3600
            for b in breaks if b.end_time and b.start_time
        )

        # Calculate total working time
        total_duration = (self.end_time - self.start_time).total_seconds() / 3600
        self.total_hours = round(total_duration - total_break_time, 2)
        self.break_hours = round(total_break_time, 2)

        # Calculate overtime (after 6:30 PM)
        shift_end = datetime.combine(self.date, self.expected_end_time)
        shift_end = timezone.make_aware(shift_end)

        if self.end_time > shift_end:
            overtime_duration = (self.end_time - shift_end).total_seconds() / 3600
            # Subtract any break time that occurred during overtime
            overtime_breaks = sum(
                (b.end_time - b.start_time).total_seconds() / 3600
                for b in breaks
                if b.end_time and b.start_time and b.start_time >= shift_end
            )
            self.overtime_hours = round(overtime_duration - overtime_breaks, 2)
        else:
            self.overtime_hours = 0

    def save(self, *args, **kwargs):
        self.calculate_hours()
        super().save(*args, **kwargs)

    @property
    def effective_work_hours(self):
        """Calculate effective work hours (End Time - Start Time - Total Break Duration)"""
        if not self.start_time or not self.end_time:
            return 0
        
        # Calculate total work duration
        total_duration = self.end_time - self.start_time
        total_work_hours = total_duration.total_seconds() / 3600
        
        # Subtract break hours
        effective_hours = total_work_hours - float(self.break_hours or 0)
        
        return round(max(0, effective_hours), 2)

    def calculate_attendance_status(self):
        """Calculate attendance status with half-day logic and 15-minute buffer"""
        if not self.start_time or not self.end_time:
            return 'absent'
        
        effective_hours = self.effective_work_hours
        
        # Half Day Logic: If Total Work < 4 Hours = Half Day
        if effective_hours < 4:
            return 'half_day'
        
        # Full Day requirement with 15-minute buffer
        required_full_day = 8  # hours
        buffer = 15 / 60  # 15 minutes converted to hours
        
        if effective_hours >= (required_full_day - buffer):
            return 'full_day_present'
        else:
            return 'half_day'

    @property
    def calculated_status(self):
        """Get the calculated status (before manual correction)"""
        if self.correction_status == 'manually_corrected':
            return self.final_status
        return self.calculate_attendance_status()

    @property
    def display_status(self):
        """Get the final status to display"""
        if self.correction_status == 'manually_corrected':
            return f"{self.get_final_status_display()} (Corrected)"
        return self.get_calculated_status_display()

    def manual_correction(self, new_status, corrected_by_employee, notes=None):
        """Apply manual correction to attendance status"""
        self.final_status = new_status
        self.correction_status = 'manually_corrected'
        self.corrected_by = corrected_by_employee
        self.corrected_at = timezone.now()
        self.correction_notes = notes
        self.save()


class Break(models.Model):
    """Model to track breaks during attendance"""

    BREAK_TYPES = [
        ('tea_morning', 'Morning Tea Break'),
        ('lunch', 'Lunch Break'),
        ('tea_afternoon', 'Afternoon Tea Break'),
        ('other', 'Other Break'),
    ]

    attendance = models.ForeignKey(
        Attendance,
        on_delete=models.CASCADE,
        related_name='breaks'
    )
    break_type = models.CharField(
        max_length=20,
        choices=BREAK_TYPES,
        default='other'
    )
    start_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Break start time"
    )
    end_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Break end time"
    )
    duration_hours = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=0,
        help_text="Break duration in hours"
    )
    is_auto_break = models.BooleanField(
        default=False,
        help_text="Whether this is an automatic scheduled break"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['start_time']
        verbose_name = 'Break'
        verbose_name_plural = 'Breaks'

    def __str__(self):
        return f"{self.attendance.employee.user.username} - {self.get_break_type_display()}"

    def save(self, *args, **kwargs):
        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time
            self.duration_hours = round(duration.total_seconds() / 3600, 2)
        super().save(*args, **kwargs)

    def get_duration_minutes(self):
        """Get break duration in minutes"""
        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time
            return int(duration.total_seconds() / 60)
        elif self.start_time:
            from django.utils import timezone
            duration = timezone.now() - self.start_time
            return int(duration.total_seconds() / 60)
        return 0

    def get_allowed_duration_minutes(self):
        """Get allowed duration for this break type"""
        allowed_durations = {
            'tea_morning': 15,      # 15 minutes
            'lunch': 30,            # 30 minutes
            'tea_afternoon': 15,    # 15 minutes
            'other': 10,            # 10 minutes for other breaks
        }
        return allowed_durations.get(self.break_type, 10)

    def is_exceeded(self):
        """Check if break duration has exceeded allowed limit"""
        return self.get_duration_minutes() > self.get_allowed_duration_minutes()

    def get_exceeded_minutes(self):
        """Get how many minutes the break has exceeded the limit"""
        if self.is_exceeded():
            return self.get_duration_minutes() - self.get_allowed_duration_minutes()
        return 0

    def get_remaining_minutes(self):
        """Get remaining minutes before break exceeds limit"""
        if not self.start_time or self.is_exceeded():
            return 0
        remaining = self.get_allowed_duration_minutes() - self.get_duration_minutes()
        return max(0, remaining)

    def get_status_display(self):
        """Get break status with duration info"""
        if not self.start_time:
            return "Not Started"
        elif not self.end_time:
            duration = self.get_duration_minutes()
            allowed = self.get_allowed_duration_minutes()
            if duration > allowed:
                return f"⚠️ Exceeded by {duration - allowed} min"
            else:
                return f"⏱️ {duration}/{allowed} min"
        else:
            duration = self.get_duration_minutes()
            allowed = self.get_allowed_duration_minutes()
            if duration > allowed:
                return f"❌ Exceeded ({duration} min)"
            else:
                return f"✅ Completed ({duration} min)"

    def get_clean_break_type(self):
        """Get break type name without time ranges"""
        return self.get_break_type_display().split(' (')[0]


class Violation(models.Model):
    """Model to track attendance violations"""

    VIOLATION_TYPES = [
        ('late_arrival', 'Late Arrival'),
        ('early_departure', 'Early Departure'),
        ('missed_break', 'Missed Scheduled Break'),
        ('extended_break', 'Extended Break'),
        ('no_checkout', 'No Checkout'),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='violations'
    )
    attendance = models.ForeignKey(
        Attendance,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='violations'
    )
    violation_type = models.CharField(
        max_length=20,
        choices=VIOLATION_TYPES
    )
    description = models.TextField(
        help_text="Description of the violation"
    )
    violation_time = models.DateTimeField(
        help_text="When the violation occurred"
    )
    expected_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="What the expected time should have been"
    )
    time_difference_minutes = models.IntegerField(
        default=0,
        help_text="Time difference in minutes (positive = late/over, negative = early/under)"
    )
    resolved = models.BooleanField(
        default=False,
        help_text="Whether the violation has been resolved"
    )
    resolved_by = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_violations'
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-violation_time']
        verbose_name = 'Violation'
        verbose_name_plural = 'Violations'

    def __str__(self):
        return f"{self.employee.user.username} - {self.get_violation_type_display()} - {self.violation_time.date()}"


class Leave(models.Model):
    LEAVE_TYPES = [
        ('annual', 'Annual Leave'),
        ('sick', 'Sick Leave'),
        ('casual', 'Casual Leave'),
        ('maternity', 'Maternity Leave'),
        ('paternity', 'Paternity Leave'),
        ('emergency', 'Emergency Leave'),
        ('other', 'Other'),
    ]

    LEAVE_STATUS = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='leaves'
    )

    leave_type = models.CharField(
        max_length=20,
        choices=LEAVE_TYPES,
        help_text="Type of leave requested"
    )

    start_date = models.DateField(
        help_text="Leave start date"
    )

    end_date = models.DateField(
        help_text="Leave end date"
    )

    reason = models.TextField(
        help_text="Reason for leave"
    )

    additional_notes = models.TextField(
        null=True,
        blank=True,
        help_text="Additional notes or comments"
    )

    status = models.CharField(
        max_length=20,
        choices=LEAVE_STATUS,
        default='pending',
        help_text="Current status of leave application"
    )

    approved_by = models.ForeignKey(
        Employee,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='approved_leaves',
        help_text="Employee who approved this leave"
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the leave was approved/rejected"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Leave Application'
        verbose_name_plural = 'Leave Applications'

    def __str__(self):
        return f"{self.employee.user.username} - {self.get_leave_type_display()} ({self.start_date} to {self.end_date})"

    @property
    def duration_days(self):
        """Calculate the duration of leave in days"""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        return 0

    @property
    def is_pending(self):
        return self.status == 'pending'

    @property
    def is_approved(self):
        return self.status == 'approved'

    @property
    def is_rejected(self):
        return self.status == 'rejected'


class LeaveApproval(models.Model):
    APPROVAL_STATUS = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    leave = models.ForeignKey(
        Leave,
        on_delete=models.CASCADE,
        related_name='approvals'
    )

    approver = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='leave_approvals'
    )

    status = models.CharField(
        max_length=20,
        choices=APPROVAL_STATUS,
        default='pending'
    )

    comments = models.TextField(
        null=True,
        blank=True,
        help_text="Approval/rejection comments"
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Leave Approval'
        verbose_name_plural = 'Leave Approvals'
        unique_together = ['leave', 'approver']


class Ticket(models.Model):
    """Support Ticket Model"""
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    CATEGORY_CHOICES = [
        ('technical', 'Technical'),
        ('hr', 'HR'),
        ('payroll', 'Payroll'),
        ('infrastructure', 'Infrastructure'),
        ('other', 'Other'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    
    ticket_id = models.AutoField(primary_key=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='tickets')
    subject = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='technical')
    description = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='open')
    attachment = models.FileField(upload_to='tickets/attachments/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Support Ticket'
        verbose_name_plural = 'Support Tickets'
    
    def __str__(self):
        return f"#{self.ticket_id} - {self.subject}"
    
    @property
    def ticket_number(self):
        if self.ticket_id:
            return f"TKT-{self.ticket_id:06d}"
        return "TKT-000000"
    
    def get_status_display(self):
        return dict(self.STATUS_CHOICES).get(self.status, self.status)
    
    def get_category_display(self):
        return dict(self.CATEGORY_CHOICES).get(self.category, self.category)
    
    def get_priority_display(self):
        return dict(self.PRIORITY_CHOICES).get(self.priority, self.priority)


class TicketComment(models.Model):
    """Comments for Support Tickets"""
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(Employee, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_admin_reply = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'Ticket Comment'
        verbose_name_plural = 'Ticket Comments'
    
    def __str__(self):
        return f"Comment by {self.author.full_name} on {self.ticket.ticket_number}"


class MISReport(models.Model):
    """Management Information System Report Model"""
    
    APPLICANT_TYPES = [
        ('salaried', 'Salaried'),
        ('self_employed', 'Self Employed'),
        ('business', 'Business'),
        ('pensioner', 'Pensioner'),
    ]
    
    PRODUCTS = [
        ('personal_loan', 'Personal Loan'),
        ('business_loan', 'Business Loan'),
        ('home_loan', 'Home Loan'),
        ('car_loan', 'Car Loan'),
        ('education_loan', 'Education Loan'),
        ('overdraft', 'Overdraft'),
    ]
    
    STATUSES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('disbursed', 'Disbursed'),
        ('not_interested', 'Not Interested'),
    ]
    
    # Basic Information
    manager = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='managed_mis_reports',
        limit_choices_to={'employee__role': 'manager'}
    )
    aro = models.CharField(max_length=100, blank=True, null=True)
    team_leader = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='mis_reports',
        limit_choices_to={'employee__role': 'team_leader'}
    )
    login_date = models.DateField()
    app_id = models.CharField(max_length=50)
    customer_name = models.CharField(max_length=200)
    mobile_number = models.CharField(max_length=20)
    applicant_type = models.CharField(max_length=20, choices=APPLICANT_TYPES)
    dob = models.DateField()
    pan_no = models.CharField(max_length=10)
    salary = models.DecimalField(max_digits=12, decimal_places=2)
    company_name = models.CharField(max_length=200)
    login_amount = models.DecimalField(max_digits=12, decimal_places=2)
    disbursed_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    product = models.CharField(max_length=50, choices=PRODUCTS)
    tanure = models.IntegerField(help_text="Loan tenure in months")
    bank = models.CharField(max_length=100)
    location = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUSES, default='pending')
    current_status = models.CharField(max_length=100, blank=True, null=True)
    banker_name = models.CharField(max_length=100, blank=True, null=True)
    banker_no = models.CharField(max_length=20, blank=True, null=True)
    
    # System Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_mis_reports')
    
    class Meta:
        ordering = ['-login_date']
        verbose_name = 'MIS Report'
        verbose_name_plural = 'MIS Reports'
    
    def __str__(self):
        return f"{self.app_id} - {self.customer_name} ({self.login_date})"
    
    @property
    def age(self):
        """Calculate age from DOB"""
        from datetime import date
        today = date.today()
        return today.year - self.dob.year - ((today.month, today.day) < (self.dob.month, self.dob.day))
    
    def save(self, *args, **kwargs):
        """Auto-assign manager and team leader if not set"""
        if not self.team_leader and hasattr(self, 'created_by') and self.created_by:
            if self.created_by.employee.is_team_leader:
                self.team_leader = self.created_by
                # Auto-assign manager from team leader
                if self.created_by.employee.manager:
                    self.manager = self.created_by.employee.manager.user
            elif self.created_by.employee.is_manager:
                self.manager = self.created_by
        
        super().save(*args, **kwargs)


class Candidate(models.Model):
    """Candidate model for interview management"""
    
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('applied', 'Applied'),
        ('screening', 'Screening'),
        ('interview_scheduled', 'Interview Scheduled'),
        ('interviewed', 'Interviewed'),
        ('shortlisted', 'Shortlisted'),
        ('rejected', 'Rejected'),
        ('hired', 'Hired'),
        ('withdrawn', 'Withdrawn'),
    ]
    
    EXPERIENCE_CHOICES = [
        ('fresher', 'Fresher'),
        ('0-1', '0-1 Year'),
        ('1-3', '1-3 Years'),
        ('3-5', '3-5 Years'),
        ('5-10', '5-10 Years'),
        ('10+', '10+ Years'),
    ]
    
    # Personal Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    
    # Professional Information
    position_applied = models.CharField(max_length=200)
    department = models.CharField(max_length=100, choices=Employee.DEPARTMENTS, blank=True)
    experience = models.CharField(max_length=10, choices=EXPERIENCE_CHOICES, default='fresher')
    current_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    expected_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    notice_period = models.IntegerField(help_text="Notice period in days", null=True, blank=True)
    
    # Skills and Qualification
    skills = models.TextField(help_text="Comma separated skills")
    qualification = models.CharField(max_length=200)
    university = models.CharField(max_length=200, blank=True)
    year_of_passing = models.IntegerField(null=True, blank=True)
    
    # Resume and Documents
    resume = models.FileField(upload_to='candidates/resumes/', null=True, blank=True)
    portfolio_link = models.URLField(blank=True)
    linkedin_profile = models.URLField(blank=True)
    
    # Status and Tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='applied')
    source = models.CharField(max_length=100, help_text="Source of candidate (e.g., LinkedIn, Referral, Website)", blank=True)
    notes = models.TextField(blank=True)
    
    # System Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_candidates')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Candidate"
        verbose_name_plural = "Candidates"
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.position_applied}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self):
        if self.date_of_birth:
            return timezone.now().date().year - self.date_of_birth.year
        return None


class Interview(models.Model):
    """Interview model for scheduling and tracking interviews"""
    
    INTERVIEW_TYPES = [
        ('phone', 'Phone Interview'),
        ('video', 'Video Interview'),
        ('onsite', 'On-site Interview'),
        ('technical', 'Technical Interview'),
        ('hr', 'HR Interview'),
        ('final', 'Final Interview'),
    ]
    
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('rescheduled', 'Rescheduled'),
        ('no_show', 'No Show'),
    ]
    
    # Interview Details
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='interviews')
    interview_type = models.CharField(max_length=20, choices=INTERVIEW_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Scheduling
    scheduled_date = models.DateTimeField()
    duration = models.IntegerField(help_text="Duration in minutes", default=60)
    location = models.CharField(max_length=200, help_text="Meeting link or office location")
    
    # Interviewers
    interviewers = models.ManyToManyField(Employee, related_name='interviews_conducted', blank=True)
    primary_interviewer = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, 
                                      related_name='primary_interviews', help_text="Main interviewer")
    
    # Status and Feedback
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    feedback = models.TextField(blank=True)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True,
                            help_text="Rating from 1-5")
    recommendation = models.CharField(max_length=20, choices=[
        ('hire', 'Hire'),
        ('consider', 'Consider'),
        ('reject', 'Reject'),
    ], blank=True)
    
    # Communication
    interview_link = models.URLField(blank=True, help_text="Video call link for online interviews")
    reminder_sent = models.BooleanField(default=False, help_text="Whether reminder has been sent")
    reminder_sent_at = models.DateTimeField(null=True, blank=True)
    
    # System Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_interviews')
    
    class Meta:
        ordering = ['scheduled_date']
        verbose_name = "Interview"
        verbose_name_plural = "Interviews"
    
    def __str__(self):
        return f"{self.candidate.full_name} - {self.title} ({self.scheduled_date.strftime('%Y-%m-%d %H:%M')})"
    
    @property
    def is_upcoming(self):
        return self.scheduled_date > timezone.now() and self.status == 'scheduled'
    
    @property
    def is_today(self):
        return self.scheduled_date.date() == timezone.now().date()
    
    @property
    def needs_reminder(self):
        """Check if interview needs reminder (24 hours before)"""
        if self.reminder_sent or self.status != 'scheduled':
            return False
        
        time_until = self.scheduled_date - timezone.now()
        return time_until.total_seconds() <= 24 * 60 * 60  # 24 hours in seconds
    
    def send_reminder(self):
        """Mark reminder as sent"""
        self.reminder_sent = True
        self.reminder_sent_at = timezone.now()
        self.save(update_fields=['reminder_sent', 'reminder_sent_at'])


class InterviewReminder(models.Model):
    """Model to track interview reminders sent"""
    
    interview = models.ForeignKey(Interview, on_delete=models.CASCADE, related_name='reminders')
    reminder_type = models.CharField(max_length=20, choices=[
        ('24h', '24 Hours Before'),
        ('2h', '2 Hours Before'),
        ('30m', '30 Minutes Before'),
    ])
    sent_at = models.DateTimeField(auto_now_add=True)
    sent_to = models.ManyToManyField(Employee, related_name='received_reminders')
    
    class Meta:
        verbose_name = "Interview Reminder"
        verbose_name_plural = "Interview Reminders"
    
    def __str__(self):
        return f"{self.interview} - {self.reminder_type} ({self.sent_at.strftime('%Y-%m-%d %H:%M')})"


class PasswordChangeRequest(models.Model):
    """Model to track password change requests from users"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_requests')
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requested_password_changes')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reason = models.TextField(help_text="Reason for password change request")
    admin_notes = models.TextField(blank=True, null=True, help_text="Admin notes about this request")
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_password_requests')
    processed_at = models.DateTimeField(null=True, blank=True)
    
    # System Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Password Change Request"
        verbose_name_plural = "Password Change Requests"
    
    def __str__(self):
        return f"{self.user.username} - {self.status} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"
    
    @property
    def is_pending(self):
        return self.status == 'pending'
    
    def approve(self, admin_user, notes=None):
        """Approve the password change request"""
        self.status = 'approved'
        self.processed_by = admin_user
        self.processed_at = timezone.now()
        if notes:
            self.admin_notes = notes
        self.save()
    
    def reject(self, admin_user, notes=None):
        """Reject the password change request"""
        self.status = 'rejected'
        self.processed_by = admin_user
        self.processed_at = timezone.now()
        if notes:
            self.admin_notes = notes
        self.save()
    
    def complete(self, admin_user, notes=None):
        """Mark the password change as completed"""
        self.status = 'completed'
        self.processed_by = admin_user
        self.processed_at = timezone.now()
        if notes:
            self.admin_notes = notes
        self.save()


class GeolocationLoginAttempt(models.Model):
    """Track geolocation-based login attempts for security monitoring"""
    
    ATTEMPT_TYPES = [
        ('login_success', 'Login Success'),
        ('login_blocked', 'Login Blocked'),
        ('location_invalid', 'Invalid Location'),
        ('coordinates_missing', 'Missing Coordinates'),
        ('permission_denied', 'Permission Denied'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='geolocation_attempts')
    employee = models.ForeignKey('Employee', on_delete=models.CASCADE, related_name='geolocation_attempts', null=True, blank=True)
    
    # Location data
    user_latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    user_longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    distance_from_office = models.FloatField(null=True, blank=True, help_text="Distance in meters from office")
    
    # Attempt details
    attempt_type = models.CharField(max_length=20, choices=ATTEMPT_TYPES)
    success = models.BooleanField(default=False)
    bypass_allowed = models.BooleanField(default=False, help_text="Whether user can bypass geolocation")
    user_role = models.CharField(max_length=20, choices=Employee.ROLES, null=True, blank=True)
    
    # Request information
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    browser_info = models.TextField(null=True, blank=True)
    
    # Error details
    error_message = models.TextField(null=True, blank=True)
    blocked_reason = models.CharField(max_length=100, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Geolocation Login Attempt'
        verbose_name_plural = 'Geolocation Login Attempts'
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user']),
            models.Index(fields=['attempt_type']),
            models.Index(fields=['success']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_attempt_type_display()} - {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
    
    @property
    def employee_name(self):
        """Get employee name if available"""
        if self.employee:
            return self.employee.full_name
        return self.user.get_full_name() or self.user.username
    
    @property
    def formatted_distance(self):
        """Get formatted distance for display"""
        if self.distance_from_office:
            if self.distance_from_office < 1000:
                return f"{self.distance_from_office:.1f}m"
            else:
                return f"{self.distance_from_office/1000:.2f}km"
        return "Unknown"
    
    @property
    def was_within_premises(self):
        """Check if attempt was within office premises"""
        return self.distance_from_office and self.distance_from_office <= 70
    
    @classmethod
    def log_attempt(cls, user, attempt_type, success=False, latitude=None, longitude=None, 
                   distance=None, ip_address=None, user_agent=None, error_message=None, 
                   bypass_allowed=False, user_role=None):
        """Create a new geolocation login attempt record"""
        try:
            employee = user.employee if hasattr(user, 'employee') else None
            return cls.objects.create(
                user=user,
                employee=employee,
                user_latitude=latitude,
                user_longitude=longitude,
                distance_from_office=distance,
                attempt_type=attempt_type,
                success=success,
                bypass_allowed=bypass_allowed,
                user_role=user_role,
                ip_address=ip_address,
                user_agent=user_agent,
                error_message=error_message
            )
        except Exception as e:
            # Log the error but don't break the login process
            print(f"Error logging geolocation attempt: {e}")
            return None
    
    @classmethod
    def get_blocked_attempts(cls, days=30):
        """Get blocked login attempts from last N days"""
        from django.utils import timezone
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        return cls.objects.filter(
            created_at__gte=cutoff_date,
            success=False,
            bypass_allowed=False
        ).order_by('-created_at')
    
    @classmethod
    def get_user_attempts(cls, user, days=30):
        """Get all attempts for a specific user"""
        from django.utils import timezone
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        return cls.objects.filter(
            user=user,
            created_at__gte=cutoff_date
        ).order_by('-created_at')
    
    def get_created_at_ist(self):
        """Get created at time in Indian Standard Time"""
        import pytz
        ist = pytz.timezone('Asia/Kolkata')
        if self.created_at:
            return self.created_at.astimezone(ist).strftime('%Y-%m-%d %H:%M:%S')
        return 'N/A'
