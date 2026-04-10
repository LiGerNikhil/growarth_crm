from django import forms
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from .models import Employee, OnboardingTask, Document, ManagerRequest, Team, ExcelBatch, ExcelBatchRow, LoginStatistics, Attendance, Violation, Leave, LeaveApproval, MISReport, Candidate, Interview, PasswordChangeRequest
from django.core.exceptions import ValidationError
import re
from datetime import date


class DocumentForm(forms.ModelForm):
    """Form for uploading and managing employee documents"""
    
    class Meta:
        model = Document
        fields = [
            'document_type', 'title', 'file', 
            'bank_name', 'account_number', 'ifsc_code', 'branch_name'
        ]
        widgets = {
            'document_type': forms.Select(attrs={
                'class': 'mt-1 px-4 text-sm py-3 focus:outline-brand-primary border-border-default',
                'id': 'document_type'
            }),
            'title': forms.TextInput(attrs={
                'class': 'mt-1 px-4 text-sm py-3 focus:outline-brand-primary border-border-default',
                'placeholder': 'Enter document title'
            }),
            'file': forms.FileInput(attrs={
                'class': 'mt-1 px-4 text-sm py-3 focus:outline-brand-primary border-border-default',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png'
            }),
            'bank_name': forms.TextInput(attrs={
                'class': 'mt-1 px-4 text-sm py-3 focus:outline-brand-primary border-border-default',
                'placeholder': 'Enter bank name'
            }),
            'account_number': forms.TextInput(attrs={
                'class': 'mt-1 px-4 text-sm py-3 focus:outline-brand-primary border-border-default',
                'placeholder': 'Enter account number'
            }),
            'ifsc_code': forms.TextInput(attrs={
                'class': 'mt-1 px-4 text-sm py-3 focus:outline-brand-primary border-border-default',
                'placeholder': 'Enter IFSC code'
            }),
            'branch_name': forms.TextInput(attrs={
                'class': 'mt-1 px-4 text-sm py-3 focus:outline-brand-primary border-border-default',
                'placeholder': 'Enter branch name'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make bank details fields not required
        self.fields['bank_name'].required = False
        self.fields['account_number'].required = False
        self.fields['ifsc_code'].required = False
        self.fields['branch_name'].required = False
        
        # Initially hide bank details fields
        for field in ['bank_name', 'account_number', 'ifsc_code', 'branch_name']:
            self.fields[field].widget.attrs.update({
                'style': 'display: none;',
                'class': self.fields[field].widget.attrs.get('class', '') + ' bank-details-field'
            })


class StaffForm(forms.ModelForm):
    """Unified form for creating and updating staff members"""
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'mt-1 px-4 text-sm py-3 focus:outline-brand-primary border-border-default'}),
        help_text="Set initial password for the employee",
        required=False
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'mt-1 px-4 text-sm py-3 focus:outline-brand-primary border-border-default'}),
        label="Confirm Password",
        required=False
    )
    
    # Add team leader field
    team_leader = forms.ModelChoiceField(
        queryset=Employee.objects.filter(role='team_leader', employment_status='active'),
        widget=forms.Select(attrs={'class': 'mt-1 px-4 text-sm py-3 focus:outline-brand-primary border-border-default'}),
        required=False,
        help_text="Assign this employee to a team leader"
    )
    
    class Meta:
        model = Employee
        fields = [
            'first_name', 'last_name', 'email', 'phone',
            'employee_type', 'department', 'position', 'role', 'reports_to', 'team_leader',
            'hire_date', 'start_date', 'probation_end_date',
            'salary', 'bonus_percentage',
            'date_of_birth', 'address', 'city', 'state', 'postal_code', 'country',
            'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship',
            'employment_status',
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'mt-1 px-4 text-sm py-3 focus:outline-brand-primary border-border-default'}),
            'last_name': forms.TextInput(attrs={'class': 'mt-1 px-4 text-sm py-3 focus:outline-brand-primary border-border-default'}),
            'email': forms.EmailInput(attrs={'class': 'mt-1 px-4 text-sm py-3 focus:outline-brand-primary border-border-default'}),
            'phone': forms.TextInput(attrs={'class': 'mt-1 px-4 text-sm py-3 focus:outline-brand-primary border-border-default'}),
            'employee_type': forms.Select(attrs={'class': 'mt-1 px-4 text-sm py-3 focus:outline-brand-primary border-border-default'}),
            'department': forms.Select(attrs={'class': 'mt-1 px-4 text-sm py-3 focus:outline-brand-primary border-border-default'}),
            'position': forms.TextInput(attrs={'class': 'mt-1 px-4 text-sm py-3 focus:outline-brand-primary border-border-default'}),
            'role': forms.Select(attrs={'class': 'mt-1 px-4 text-sm py-3 focus:outline-brand-primary border-border-default'}),
            'reports_to': forms.Select(attrs={'class': 'mt-1 px-4 text-sm py-3 focus:outline-brand-primary border-border-default'}),
            'hire_date': forms.DateInput(attrs={'class': 'mt-1 px-4 text-sm py-3 focus:outline-brand-primary border-border-default', 'type': 'date'}),
            'start_date': forms.DateInput(attrs={'class': 'mt-1 px-4 text-sm py-3 focus:outline-brand-primary border-border-default', 'type': 'date'}),
            'probation_end_date': forms.DateInput(attrs={'class': 'mt-1 px-4 text-sm py-3 focus:outline-brand-primary border-border-default', 'type': 'date'}),
            'salary': forms.NumberInput(attrs={'class': 'mt-1 px-4 text-sm py-3 focus:outline-brand-primary border-border-default', 'step': '0.01'}),
            'bonus_percentage': forms.NumberInput(attrs={'class': 'mt-1 px-4 text-sm py-3 focus:outline-brand-primary border-border-default', 'step': '0.01'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'mt-1 px-4 text-sm py-3 focus:outline-brand-primary border-border-default', 'type': 'date'}),
            'address': forms.Textarea(attrs={'class': 'mt-1 px-4 text-sm py-3 focus:outline-brand-primary border-border-default', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'mt-1 px-4 text-sm py-3 focus:outline-brand-primary border-border-default'}),
            'state': forms.TextInput(attrs={'class': 'mt-1 px-4 text-sm py-3 focus:outline-brand-primary border-border-default'}),
            'postal_code': forms.TextInput(attrs={'class': 'mt-1 px-4 text-sm py-3 focus:outline-brand-primary border-border-default'}),
            'country': forms.TextInput(attrs={'class': 'mt-1 px-4 text-sm py-3 focus:outline-brand-primary border-border-default'}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'mt-1 px-4 text-sm py-3 focus:outline-brand-primary border-border-default'}),
            'emergency_contact_phone': forms.TextInput(attrs={'class': 'mt-1 px-4 text-sm py-3 focus:outline-brand-primary border-border-default'}),
            'emergency_contact_relationship': forms.TextInput(attrs={'class': 'mt-1 px-4 text-sm py-3 focus:outline-brand-primary border-border-default'}),
            'team_leader': forms.Select(attrs={'class': 'mt-1 px-4 text-sm py-3 focus:outline-brand-primary border-border-default'}),
            'employment_status': forms.Select(attrs={'class': 'mt-1 px-4 text-sm py-3 focus:outline-brand-primary border-border-default'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.is_create = kwargs.pop('is_create', False)
        super().__init__(*args, **kwargs)
        
        # Set reports_to options based on current user role
        if self.user and hasattr(self.user, 'employee'):
            current_employee = self.user.employee
            
            if current_employee.is_superadmin:
                # SuperAdmin can assign to any manager or admin
                self.fields['reports_to'].queryset = Employee.objects.filter(
                    role__in=['admin', 'manager'], 
                    employment_status='active'
                )
            elif current_employee.is_admin:
                # Admin can assign to managers
                self.fields['reports_to'].queryset = Employee.objects.filter(
                    role='manager', 
                    employment_status='active'
                )
            elif current_employee.is_hr:
                # HR can assign to managers
                self.fields['reports_to'].queryset = Employee.objects.filter(
                    role='manager', 
                    employment_status='active'
                )
            elif current_employee.is_manager:
                # Manager can assign to themselves (for team leaders)
                self.fields['reports_to'].queryset = Employee.objects.filter(
                    id=current_employee.id
                )
            else:
                # Others can't assign
                self.fields['reports_to'].queryset = Employee.objects.none()
        else:
            self.fields['reports_to'].queryset = Employee.objects.filter(
                role__in=['admin', 'manager'], 
                employment_status='active'
            )
        
        self.fields['reports_to'].empty_label = "Select Reporting To"
        
        # Set team_leader options based on current user role
        if self.user and hasattr(self.user, 'employee'):
            current_employee = self.user.employee
            
            if current_employee.is_superadmin:
                # SuperAdmin can assign to any team leader
                self.fields['team_leader'].queryset = Employee.objects.filter(
                    role='team_leader', 
                    employment_status='active'
                )
            elif current_employee.is_admin:
                # Admin can assign to any team leader
                self.fields['team_leader'].queryset = Employee.objects.filter(
                    role='team_leader', 
                    employment_status='active'
                )
            elif current_employee.is_hr:
                # HR can assign to any team leader
                self.fields['team_leader'].queryset = Employee.objects.filter(
                    role='team_leader', 
                    employment_status='active'
                )
            elif current_employee.is_manager:
                # Manager can only assign to team leaders that report to them
                self.fields['team_leader'].queryset = Employee.objects.filter(
                    role='team_leader', 
                    employment_status='active',
                    reports_to=current_employee
                )
            else:
                # Others can't assign team leaders
                self.fields['team_leader'].queryset = Employee.objects.none()
        else:
            self.fields['team_leader'].queryset = Employee.objects.filter(
                role='team_leader', 
                employment_status='active'
            )
        
        self.fields['team_leader'].empty_label = "Select Team Leader (Optional)"
        
        # Set password fields requirement based on create/update
        if self.is_create:
            self.fields['password'].required = True
            self.fields['confirm_password'].required = True
        else:
            self.fields['password'].required = False
            self.fields['confirm_password'].required = False
        
        # Add required field indicators
        for field_name, field in self.fields.items():
            if field.required and field_name not in ['password', 'confirm_password']:
                field.widget.attrs['required'] = True
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Check if email is being changed and if it already exists
        if email and Employee.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError("A user with this email already exists.")
        return email
    
    def clean_confirm_password(self):
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            raise ValidationError("Passwords do not match.")
        return confirm_password
    
    def clean(self):
        cleaned_data = super().clean()
        hire_date = cleaned_data.get('hire_date')
        start_date = cleaned_data.get('start_date')
        role = cleaned_data.get('role')
        reports_to = cleaned_data.get('reports_to')
        
        if hire_date and start_date and start_date < hire_date:
            raise ValidationError("Start date cannot be before hire date.")
        
        # Validate hierarchy relationships
        if role == 'employee' and self.is_create:
            if not reports_to:
                raise ValidationError("Employee must be assigned to a manager or team leader.")
        elif role == 'team_leader':
            if not reports_to:
                raise ValidationError("Team leader must be assigned to a manager.")
        elif role == 'manager':
            if reports_to:
                raise ValidationError("Manager cannot be assigned to anyone.")
        elif role in ['admin', 'superadmin']:
            if reports_to:
                raise ValidationError("Admin/SuperAdmin cannot be assigned to anyone.")
        
        return cleaned_data
    
    def save(self, commit=True):
        employee = super().save(commit=False)
        
        # Handle user account creation for new staff
        if self.is_create:
            from django.contrib.auth.models import User
            password = self.cleaned_data.get('password')
            
            if password:
                # Create user account
                username = employee.email.split('@')[0]
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{employee.email.split('@')[0]}_{counter}"
                    counter += 1
                
                user = User.objects.create_user(
                    username=username,
                    email=employee.email,
                    password=password,
                    first_name=employee.first_name,
                    last_name=employee.last_name
                )
                
                employee.user = user
        else:
            # For updates, handle password change if provided
            password = self.cleaned_data.get('password')
            if password and employee.user:
                employee.user.set_password(password)
                employee.user.save()
        
        if commit:
            employee.save()
        
        return employee


class EmployeeUpdateForm(forms.ModelForm):
    """Form for updating existing employees"""
    
    class Meta:
        model = Employee
        fields = [
            'first_name', 'last_name', 'phone',
            'employee_type', 'department', 'position', 'role', 'manager', 'team_leader',
            'probation_end_date', 'employment_status',
            'salary', 'bonus_percentage',
            'date_of_birth', 'address', 'city', 'state', 'postal_code', 'country',
            'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship',
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'employee_type': forms.Select(attrs={'class': 'form-select'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'manager': forms.Select(attrs={'class': 'form-select'}),
            'team_leader': forms.Select(attrs={'class': 'form-select'}),
            'probation_end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'employment_status': forms.Select(attrs={'class': 'form-select'}),
            'salary': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'bonus_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_relationship': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set manager options
        self.fields['manager'].queryset = Employee.objects.filter(role='manager', employment_status='active')
        self.fields['manager'].empty_label = "Select Manager"
        
        # Set team leader options
        self.fields['team_leader'].queryset = Employee.objects.filter(role='team_leader', employment_status='active')
        self.fields['team_leader'].empty_label = "Select Team Leader"


class ManagerRequestForm(forms.ModelForm):
    """Form for creating manager promotion requests"""
    
    class Meta:
        model = ManagerRequest
        fields = ['requested_role', 'reason']
        widgets = {
            'requested_role': forms.Select(attrs={'class': 'form-select'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Explain why this employee should be promoted to a manager role...'})
        }
    
    def __init__(self, *args, **kwargs):
        employee = kwargs.pop('employee', None)
        super().__init__(*args, **kwargs)
        
        if employee:
            # Only show roles higher than current role
            current_role_index = [choice[0] for choice in Employee.ROLES].index(employee.role)
            available_roles = Employee.ROLES[current_role_index + 1:]
            self.fields['requested_role'].choices = available_roles


class OnboardingTaskForm(forms.ModelForm):
    """Form for creating onboarding tasks"""
    
    class Meta:
        model = OnboardingTask
        fields = ['title', 'description', 'status', 'due_date']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class DocumentUploadForm(forms.ModelForm):
    """Form for uploading employee documents"""
    
    class Meta:
        model = Document
        fields = ['document_type', 'title', 'file']
        widgets = {
            'document_type': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
        }


class TeamForm(forms.ModelForm):
    """Form for creating and managing teams"""
    
    class Meta:
        model = Team
        fields = ['name', 'description', 'team_leader', 'department']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'team_leader': forms.Select(attrs={'class': 'form-select'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter team leaders to only active ones
        self.fields['team_leader'].queryset = Employee.objects.filter(
            role='team_leader', 
            employment_status='active'
        )
        self.fields['team_leader'].empty_label = "Select Team Leader"
    
    def clean_team_leader(self):
        team_leader = self.cleaned_data.get('team_leader')
        if team_leader:
            # Check if this team leader is already leading another team
            existing_team = Team.objects.filter(team_leader=team_leader).exclude(pk=self.instance.pk)
            if existing_team.exists():
                raise ValidationError(f"{team_leader.full_name} is already leading another team.")
        return team_leader


class EmployeeSearchForm(forms.Form):
    """Form for searching employees"""
    
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by name, email, or employee ID...'
        })
    )
    
    department = forms.ChoiceField(
        choices=[('', 'All Departments')] + Employee.DEPARTMENTS,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + Employee.STATUSES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    employee_type = forms.ChoiceField(
        choices=[('', 'All Types')] + Employee.EMPLOYEE_TYPES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    role = forms.ChoiceField(
        choices=[('', 'All Roles')] + Employee.ROLES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class ExcelUploadForm(forms.ModelForm):
    """Form for uploading Excel files"""
    
    class Meta:
        model = ExcelBatch
        fields = ['batch_name', 'excel_file']
        widgets = {
            'batch_name': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Enter batch name (e.g., "January 2024 Website Leads")'
            }),
            'excel_file': forms.FileInput(attrs={
                'class': 'form-control form-control-lg',
                'accept': '.xlsx,.xls,.csv'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['batch_name'].label = 'Batch Name'
        self.fields['excel_file'].label = 'Excel File'
    
    def clean_excel_file(self):
        """Validate the uploaded Excel file"""
        excel_file = self.cleaned_data.get('excel_file')
        
        if excel_file:
            # Check file extension
            allowed_extensions = ['.xlsx', '.xls', '.csv']
            file_extension = excel_file.name.lower().split('.')[-1]
            
            if f'.{file_extension}' not in allowed_extensions:
                raise forms.ValidationError(
                    'Invalid file format. Please upload an Excel file (.xlsx, .xls) or CSV file (.csv)'
                )
            
            # Check file size (max 10MB)
            if excel_file.size > 10 * 1024 * 1024:
                raise forms.ValidationError(
                    'File size too large. Maximum allowed size is 10MB.'
                )
        
        return excel_file


class ExcelBatchProcessForm(forms.Form):
    """Form for processing Excel batch"""
    
    action = forms.ChoiceField(
        choices=[
            ('process', 'Process All Rows'),
            ('retry_failed', 'Retry Failed Rows Only'),
            ('skip_errors', 'Skip Errors and Process Valid'),
            ('cancel', 'Cancel Batch')
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, batch, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.batch = batch
        
        # Disable certain options based on batch status
        if batch.status == 'completed':
            self.fields['action'].choices = [
                ('process', 'Process All Rows'),
                ('retry_failed', 'Retry Failed Rows Only'),
            ]
        elif batch.status == 'failed':
            self.fields['action'].choices = [
                ('retry_failed', 'Retry Failed Rows Only'),
                ('skip_errors', 'Skip Errors and Process Valid'),
                ('cancel', 'Cancel Batch')
            ]


class LoginStatisticsForm(forms.ModelForm):
    """Form for creating and updating login statistics"""
    
    class Meta:
        model = LoginStatistics
        fields = ['manager', 'team_leader', 'file_count', 'login_count', 'total_count', 'date', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'file_count': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'login_count': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'total_count': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': '3'}),
            'manager': forms.Select(attrs={'class': 'form-select'}),
            'team_leader': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter managers based on user role
        if user and hasattr(user, 'employee'):
            current_employee = user.employee
            if current_employee.is_superadmin:
                self.fields['manager'].queryset = Employee.objects.filter(
                    role__in=['manager', 'admin', 'superadmin'],
                    employment_status='active'
                )
            elif current_employee.is_admin:
                self.fields['manager'].queryset = Employee.objects.filter(
                    role__in=['manager', 'admin'],
                    employment_status='active'
                )
            else:
                # Managers can only see themselves
                self.fields['manager'].queryset = Employee.objects.filter(
                    id=current_employee.id,
                    employment_status='active'
                )
        else:
            self.fields['manager'].queryset = Employee.objects.filter(
                role__in=['manager', 'admin', 'superadmin'],
                employment_status='active'
            )
        
        # Set default date to today
        if not self.instance.pk:
            from django.utils import timezone
            self.fields['date'].initial = timezone.now().date()
    
    def clean(self):
        cleaned_data = super().clean()
        manager = cleaned_data.get('manager')
        team_leader = cleaned_data.get('team_leader')
        
        # Validate team leader belongs to manager
        if manager and team_leader:
            if team_leader.role != 'team_leader':
                raise forms.ValidationError("Selected team leader must have 'team_leader' role.")
            
            # If manager is not superadmin, check hierarchy
            if not manager.is_superadmin and not manager.is_admin:
                if team_leader.reports_to != manager:
                    raise forms.ValidationError("Team leader must report to this manager.")
        
        return cleaned_data


class LoginStatisticsFilterForm(forms.Form):
    """Form for filtering login statistics"""
    
    manager = forms.ModelChoiceField(
        queryset=Employee.objects.filter(role__in=['manager', 'admin', 'superadmin']),
        required=False,
        empty_label="All Managers",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    team_leader = forms.ModelChoiceField(
        queryset=Employee.objects.filter(role='team_leader'),
        required=False,
        empty_label="All Team Leaders",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter based on user role
        if user and hasattr(user, 'employee'):
            current_employee = user.employee
            if current_employee.is_manager and not current_employee.is_admin:
                # Managers can only see their own stats and their team leaders
                self.fields['manager'].queryset = Employee.objects.filter(
                    id=current_employee.id,
                    employment_status='active'
                )
                self.fields['team_leader'].queryset = Employee.objects.filter(
                    reports_to=current_employee,
                    role='team_leader',
                    employment_status='active'
                )


class AttendanceForm(forms.ModelForm):
    """Form for viewing and editing attendance records"""

    class Meta:
        model = Attendance
        fields = ['date', 'status']
        widgets = {
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }


class AttendanceFilterForm(forms.Form):
    """Form for filtering attendance records"""

    employee = forms.ModelChoiceField(
        queryset=Employee.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'All')] + Attendance.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class ViolationForm(forms.ModelForm):
    """Form for managing violations"""

    class Meta:
        model = Violation
        fields = ['violation_type', 'description', 'resolved']
        widgets = {
            'violation_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'resolved': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class AttendanceStatsForm(forms.Form):
    """Form for filtering attendance statistics"""

    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )


class LeaveApplicationForm(forms.ModelForm):
    """Form for employees to apply for leave"""

    class Meta:
        model = Leave
        fields = ['leave_type', 'start_date', 'end_date', 'reason', 'additional_notes']
        widgets = {
            'leave_type': forms.Select(attrs={'class': 'mt-1 px-4 text-sm py-3 focus:outline-brand-primary border-border-default'}),
            'start_date': forms.DateInput(attrs={'class': 'mt-1 px-4 text-sm py-3 focus:outline-brand-primary border-border-default', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'mt-1 px-4 text-sm py-3 focus:outline-brand-primary border-border-default', 'type': 'date'}),
            'reason': forms.Textarea(attrs={'class': 'mt-1 px-4 text-sm py-3 focus:outline-brand-primary border-border-default', 'rows': 4, 'placeholder': 'Please provide the reason for your leave request...'}),
            'additional_notes': forms.Textarea(attrs={'class': 'mt-1 px-4 text-sm py-3 focus:outline-brand-primary border-border-default', 'rows': 3, 'placeholder': 'Any additional notes or information...'}),
        }

    def __init__(self, *args, **kwargs):
        self.employee = kwargs.pop('employee', None)
        super().__init__(*args, **kwargs)

        # Add required field indicators
        for field_name, field in self.fields.items():
            if field.required:
                field.widget.attrs['required'] = True

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date:
            if end_date < start_date:
                raise ValidationError("End date cannot be before start date.")

            # Check for overlapping leave requests
            if self.employee:
                overlapping_leaves = Leave.objects.filter(
                    employee=self.employee,
                    start_date__lte=end_date,
                    end_date__gte=start_date,
                    status__in=['pending', 'approved']
                ).exclude(pk=self.instance.pk)

                if overlapping_leaves.exists():
                    raise ValidationError("You already have a leave request for this period.")

        return cleaned_data


class LeaveApprovalForm(forms.ModelForm):
    """Form for approving or rejecting leave requests"""

    action = forms.ChoiceField(
        choices=[
            ('approve', 'Approve Leave'),
            ('reject', 'Reject Leave'),
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label="Approval Action"
    )

    class Meta:
        model = LeaveApproval
        fields = ['comments']
        widgets = {
            'comments': forms.Textarea(attrs={
                'class': 'mt-1 px-4 text-sm py-3 focus:outline-brand-primary border-border-default',
                'rows': 4,
                'placeholder': 'Add approval/rejection comments...'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.action = kwargs.pop('action', None)  # Get the action (approve/reject)
        super().__init__(*args, **kwargs)

        # Make comments required for rejections
        if self.action == 'reject':
            self.fields['comments'].required = True
            self.fields['comments'].label = "Rejection Reason (Required)"
            self.fields['comments'].widget.attrs.update({
                'placeholder': 'Please provide a detailed reason for rejecting this leave application...',
                'rows': 4
            })
        else:
            self.fields['comments'].required = False
            self.fields['comments'].label = "Approval Comments (Optional)"
            self.fields['comments'].widget.attrs.update({
                'placeholder': 'Add any comments about this approval...',
                'rows': 3
            })


class LeaveFilterForm(forms.Form):
    """Form for filtering leave requests"""

    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + Leave.LEAVE_STATUS,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    leave_type = forms.ChoiceField(
        choices=[('', 'All Types')] + Leave.LEAVE_TYPES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    employee = forms.ModelChoiceField(
        queryset=Employee.objects.all(),
        required=False,
        empty_label="All Employees",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )

    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Filter employees based on user role
        if user and hasattr(user, 'employee'):
            current_employee = user.employee
            if current_employee.is_manager and not current_employee.is_admin:
                # Managers can only see their team members and team leaders
                self.fields['employee'].queryset = Employee.objects.filter(
                    models.Q(reports_to=current_employee) |
                    models.Q(team_leader__reports_to=current_employee) |
                    models.Q(id=current_employee.id),
                    employment_status='active'
                )
            elif current_employee.is_team_leader:
                # Team leaders can only see their team members
                self.fields['employee'].queryset = Employee.objects.filter(
                    team_leader=current_employee,
                    employment_status='active'
                )
            elif current_employee.is_employee:
                # Regular employees can only see themselves
                self.fields['employee'].queryset = Employee.objects.filter(
                    id=current_employee.id
                )
        else:
            # Default queryset for non-employee users
            self.fields['employee'].queryset = Employee.objects.filter(
                employment_status='active'
            )


class MISReportForm(forms.ModelForm):
    """Form for creating and editing MIS Reports"""
    
    class Meta:
        model = MISReport
        fields = [
            'aro', 'login_date', 'app_id', 'customer_name', 
            'mobile_number', 'applicant_type', 'dob', 'pan_no', 
            'salary', 'company_name', 'login_amount', 'disbursed_amount', 
            'product', 'tanure', 'bank', 'location', 'status', 
            'current_status', 'banker_name', 'banker_no'
        ]
        widgets = {
            'login_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'dob': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'login_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'disbursed_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'salary': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tanure': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'applicant_type': forms.Select(attrs={'class': 'form-select'}),
            'product': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set form field classes
        for field_name, field in self.fields.items():
            if field_name not in ['login_date', 'dob', 'login_amount', 'disbursed_amount', 
                                'salary', 'tanure', 'status', 'applicant_type', 'product']:
                field.widget.attrs.update({'class': 'form-control'})
    
    def clean_mobile_number(self):
        mobile = self.cleaned_data.get('mobile_number')
        if mobile:
            # Remove any non-digit characters
            mobile_digits = re.sub(r'\D', '', mobile)
            
            # Check if it's 10 digits (for Indian mobile numbers)
            if len(mobile_digits) != 10:
                raise ValidationError('Mobile number must be exactly 10 digits.')
            
            return mobile_digits
        return mobile
    
    def clean_pan_no(self):
        pan = self.cleaned_data.get('pan_no')
        if pan:
            # Remove any whitespace and convert to uppercase
            pan_clean = pan.strip().upper()
            
            # Validate PAN format (5 letters, 4 digits, 1 letter)
            if not re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', pan_clean):
                raise ValidationError('Invalid PAN number format. It should be in format: ABCDE1234F')
            
            return pan_clean
        return pan
    
    def clean_dob(self):
        dob = self.cleaned_data.get('dob')
        if dob:
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            
            # Check if age is reasonable (18 to 100 years)
            if age < 18:
                raise ValidationError('Applicant must be at least 18 years old.')
            elif age > 100:
                raise ValidationError('Invalid date of birth.')
            
            return dob
        return dob
    
    def clean_login_amount(self):
        amount = self.cleaned_data.get('login_amount')
        if amount and amount <= 0:
            raise ValidationError('Login amount must be greater than 0.')
        return amount
    
    def clean_disbursed_amount(self):
        amount = self.cleaned_data.get('disbursed_amount')
        if amount and amount <= 0:
            raise ValidationError('Disbursed amount must be greater than 0.')
        return amount
    
    def clean_salary(self):
        salary = self.cleaned_data.get('salary')
        if salary and salary <= 0:
            raise ValidationError('Salary must be greater than 0.')
        return salary
    
    def clean_tanure(self):
        tanure = self.cleaned_data.get('tanure')
        if tanure and tanure <= 0:
            raise ValidationError('Loan tenure must be greater than 0 months.')
        if tanure and tanure > 360:  # Max 30 years
            raise ValidationError('Loan tenure cannot exceed 360 months (30 years).')
        return tanure
    
    def clean(self):
        cleaned_data = super().clean()
        login_amount = cleaned_data.get('login_amount')
        disbursed_amount = cleaned_data.get('disbursed_amount')
        
        # If status is disbursed, disbursed amount should be provided
        if cleaned_data.get('status') == 'disbursed' and not disbursed_amount:
            raise ValidationError('Disbursed amount is required when status is "Disbursed".')
        
        # Disbursed amount should not exceed login amount
        if login_amount and disbursed_amount and disbursed_amount > login_amount:
            raise ValidationError('Disbursed amount cannot exceed login amount.')
        
        return cleaned_data


class MISFilterForm(forms.Form):
    """Form for filtering MIS Reports"""
    
    from_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    to_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    team_leader = forms.ModelChoiceField(
        queryset=User.objects.none(),
        required=False,
        empty_label="All Team Leaders",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + MISReport.STATUSES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user and hasattr(user, 'employee'):
            if user.employee.is_admin or user.employee.is_superadmin:
                # Admin can see all team leaders
                self.fields['team_leader'].queryset = User.objects.filter(
                    employee__role='team_leader'
                ).order_by('first_name', 'last_name')
            elif user.employee.is_manager:
                # Manager can see their team leaders
                self.fields['team_leader'].queryset = User.objects.filter(
                    employee__role='team_leader',
                    employee__reports_to=user.employee
                ).order_by('first_name', 'last_name')


class CandidateForm(forms.ModelForm):
    """Form for adding and editing candidates"""
    
    class Meta:
        model = Candidate
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'gender', 'date_of_birth',
            'position_applied', 'department', 'experience', 'current_salary', 
            'expected_salary', 'notice_period', 'skills', 'qualification', 
            'university', 'year_of_passing', 'resume', 'portfolio_link', 
            'linkedin_profile', 'source', 'notes'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'skills': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'current_salary': forms.NumberInput(attrs={'step': '0.01'}),
            'expected_salary': forms.NumberInput(attrs={'step': '0.01'}),
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Check if email already exists (excluding current instance)
            queryset = Candidate.objects.filter(email=email)
            if self.instance and self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise ValidationError("A candidate with this email already exists.")
        return email
    
    def clean_year_of_passing(self):
        year = self.cleaned_data.get('year_of_passing')
        if year:
            current_year = timezone.now().year
            if year > current_year:
                raise ValidationError("Year of passing cannot be in the future.")
            if year < 1950:
                raise ValidationError("Year of passing seems too early.")
        return year


class InterviewForm(forms.ModelForm):
    """Form for scheduling interviews"""
    
    class Meta:
        model = Interview
        fields = [
            'candidate', 'interview_type', 'title', 'description', 
            'scheduled_date', 'duration', 'location', 'primary_interviewer',
            'interviewers', 'interview_link'
        ]
        widgets = {
            'scheduled_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={'rows': 3}),
            'candidate': forms.Select(attrs={'class': 'form-control'}),
            'interview_type': forms.Select(attrs={'class': 'form-control'}),
            'primary_interviewer': forms.Select(attrs={'class': 'form-control'}),
            'interviewers': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        candidate = kwargs.pop('candidate', None)
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter candidate choices based on status
        if candidate:
            self.fields['candidate'].queryset = Candidate.objects.filter(pk=candidate.pk)
        else:
            self.fields['candidate'].queryset = Candidate.objects.filter(
                status__in=['applied', 'screening', 'interview_scheduled']
            )
        
        # Filter interviewer choices based on user role
        if user:
            if user.is_admin or user.is_superadmin or user.is_hr:
                self.fields['primary_interviewer'].queryset = Employee.objects.filter(
                    employment_status='active'
                )
                self.fields['interviewers'].queryset = Employee.objects.filter(
                    employment_status='active'
                )
            elif user.is_manager:
                # Managers can select from their team
                team_members = Employee.objects.filter(
                    reports_to=user
                ).filter(employment_status='active')
                self.fields['primary_interviewer'].queryset = team_members
                self.fields['interviewers'].queryset = team_members
            else:
                # Regular users can only select themselves
                self.fields['primary_interviewer'].queryset = Employee.objects.filter(
                    pk=user.pk
                )
                self.fields['interviewers'].queryset = Employee.objects.filter(
                    pk=user.pk
                )
    
    def clean_scheduled_date(self):
        scheduled_date = self.cleaned_data.get('scheduled_date')
        if scheduled_date:
            if scheduled_date <= timezone.now():
                raise ValidationError("Interview date must be in the future.")
        return scheduled_date


class InterviewFeedbackForm(forms.ModelForm):
    """Form for providing interview feedback"""
    
    class Meta:
        model = Interview
        fields = ['status', 'feedback', 'rating', 'recommendation']
        widgets = {
            'feedback': forms.Textarea(attrs={'rows': 5}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'rating': forms.Select(attrs={'class': 'form-control'}),
            'recommendation': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        status = self.cleaned_data.get('status')
        
        if status == 'completed' and not rating:
            raise ValidationError("Rating is required when interview is completed.")
        
        return rating
    
    def clean_recommendation(self):
        recommendation = self.cleaned_data.get('recommendation')
        status = self.cleaned_data.get('status')
        
        if status == 'completed' and not recommendation:
            raise ValidationError("Recommendation is required when interview is completed.")
        
        return recommendation


class InterviewFilterForm(forms.Form):
    """Form for filtering interviews"""
    
    INTERVIEW_TYPE_CHOICES = [('', 'All Types')] + Interview.INTERVIEW_TYPES
    STATUS_CHOICES = [('', 'All Status')] + Interview.STATUS_CHOICES
    
    interview_type = forms.ChoiceField(
        choices=INTERVIEW_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by candidate name or title...'
        })
    )


class CandidateFilterForm(forms.Form):
    """Form for filtering candidates"""
    
    STATUS_CHOICES = [('', 'All Status')] + Candidate.STATUS_CHOICES
    DEPARTMENT_CHOICES = [('', 'All Departments')] + Employee.DEPARTMENTS
    EXPERIENCE_CHOICES = [('', 'All Experience')] + Candidate.EXPERIENCE_CHOICES
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    department = forms.ChoiceField(
        choices=DEPARTMENT_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    experience = forms.ChoiceField(
        choices=EXPERIENCE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search candidates...'
        })
    )


class PasswordChangeRequestForm(forms.ModelForm):
    """Form for users to request password change"""
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address',
            'autocomplete': 'email'
        })
    )
    
    reason = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Please explain why you need a password change...'
        })
    )
    
    class Meta:
        model = PasswordChangeRequest
        fields = ['reason']
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        try:
            user = User.objects.get(email=email)
            return user
        except User.DoesNotExist:
            raise forms.ValidationError('No user account found with this email address.')


class AdminPasswordChangeForm(forms.Form):
    """Form for admin to change user password"""
    
    new_password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new password'
        })
    )
    
    confirm_password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if new_password and confirm_password:
            if new_password != confirm_password:
                raise forms.ValidationError('Passwords do not match.')
            
            if len(new_password) < 8:
                raise forms.ValidationError('Password must be at least 8 characters long.')
        
        return cleaned_data


class PasswordRequestFilterForm(forms.Form):
    """Form for filtering password change requests"""
    
    STATUS_CHOICES = [('', 'All Status')] + PasswordChangeRequest.STATUS_CHOICES
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by username or email...'
        })
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
