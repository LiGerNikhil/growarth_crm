from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.crm.models import Lead
from apps.accounts.models import Employee


@login_required
def dashboard(request):
    """
    Enhanced dashboard view with employee-specific data
    """
    # Get employee
    employee = request.user.employee
    
    # Get counts for sidebar
    loan_leads_count = Lead.objects.filter(lead_type='loan').count()
    quote_leads_count = Lead.objects.filter(lead_type='quote').count()
    total_leads_count = Lead.objects.count()
    
    # HR-specific data
    is_hr = employee.role == 'hr'
    employees_list = []
    attendance_list = []
    leave_list = []
    break_list = []
    
    if is_hr:
        # Get all employees for HR management
        employees_list = Employee.objects.all().order_by('-created_at')
        
        # Get recent attendance records
        from apps.accounts.models import Attendance
        attendance_list = Attendance.objects.all().order_by('-date')[:10]
        
        # Get recent leave requests
        from apps.accounts.models import Leave
        leave_list = Leave.objects.all().order_by('-created_at')[:10]
        
        # Get recent break records
        from apps.accounts.models import Break
        break_list = Break.objects.all().order_by('-created_at')[:10]
    
    # Employee-specific data (for non-HR roles)
    team_members = []
    team_lead = None
    manager = None
    
    # Get team members (people who report to this employee)
    if employee.role in ['manager', 'admin', 'superadmin']:
        team_members = Employee.objects.filter(reports_to=employee).exclude(id=employee.id)
    
    # Get team lead and manager hierarchy
    current = employee
    while current.reports_to:
        if current.reports_to.role == 'team_lead':
            team_lead = current.reports_to
        elif current.reports_to.role in ['manager', 'admin']:
            manager = current.reports_to
            break
        current = current.reports_to
    
    # Dynamic stats
    from apps.accounts.models import Attendance, EmployeePhone, Leave
    from datetime import date, timedelta
    
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)
    
    # Employee attendance stats
    attendance_stats = {
        'today': Attendance.objects.filter(employee=employee, date=today).first(),
        'this_week': Attendance.objects.filter(employee=employee, date__gte=week_start).count(),
        'this_month': Attendance.objects.filter(employee=employee, date__gte=month_start).count(),
        'total_days': Attendance.objects.filter(employee=employee).count(),
    }
    
    # Phone assignment
    assigned_phones = EmployeePhone.objects.filter(employee=employee, is_active=True).count()
    
    # Leave stats
    leave_stats = {
        'pending': Leave.objects.filter(employee=employee, status='pending').count(),
        'approved': Leave.objects.filter(employee=employee, status='approved').count(),
        'rejected': Leave.objects.filter(employee=employee, status='rejected').count(),
        'total': Leave.objects.filter(employee=employee).count(),
    }
    
    context = {
        'page_title': 'Dashboard',
        'loan_leads_count': loan_leads_count,
        'quote_leads_count': quote_leads_count,
        'total_leads_count': total_leads_count,
        'employee': employee,
        'team_members': team_members,
        'team_lead': team_lead,
        'manager': manager,
        'attendance_stats': attendance_stats,
        'assigned_phones': assigned_phones,
        'leave_stats': leave_stats,
        'today': today,
        # HR-specific data
        'is_hr': is_hr,
        'employees_list': employees_list,
        'attendance_list': attendance_list,
        'leave_list': leave_list,
        'break_list': break_list,
    }
    return render(request, 'core/dashboard.html', context)


@login_required
def users(request):
    """
    Users management view
    """
    # Get counts for sidebar
    loan_leads_count = Lead.objects.filter(lead_type='loan').count()
    quote_leads_count = Lead.objects.filter(lead_type='quote').count()
    total_leads_count = Lead.objects.count()
    
    context = {
        'page_title': 'Users',
        'loan_leads_count': loan_leads_count,
        'quote_leads_count': quote_leads_count,
        'total_leads_count': total_leads_count,
    }
    return render(request, 'core/users.html', context)


@login_required
def settings(request):
    """
    Settings view
    """
    # Get counts for sidebar
    loan_leads_count = Lead.objects.filter(lead_type='loan').count()
    quote_leads_count = Lead.objects.filter(lead_type='quote').count()
    total_leads_count = Lead.objects.count()
    
    context = {
        'page_title': 'Settings',
        'loan_leads_count': loan_leads_count,
        'quote_leads_count': quote_leads_count,
        'total_leads_count': total_leads_count,
    }
    return render(request, 'core/settings.html', context)


@login_required
def profile(request):
    """
    User profile view
    """
    # Get counts for sidebar
    loan_leads_count = Lead.objects.filter(lead_type='loan').count()
    quote_leads_count = Lead.objects.filter(lead_type='quote').count()
    total_leads_count = Lead.objects.count()
    
    context = {
        'page_title': 'Profile',
        'loan_leads_count': loan_leads_count,
        'quote_leads_count': quote_leads_count,
        'total_leads_count': total_leads_count,
    }
    return render(request, 'core/profile.html', context)


def page_not_found(request, exception):
    """
    Custom 404 error handler
    """
    return render(request, '404.html', status=404)


def server_error(request):
    """
    Custom 500 error handler
    """
    return render(request, 'errors/500.html', status=500)
