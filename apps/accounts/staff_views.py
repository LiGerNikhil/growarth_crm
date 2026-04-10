from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q
from django.core.paginator import Paginator
from django.urls import reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from datetime import timedelta

from .models import Employee, Lead, LeadActivityLog, EmployeePhone, Candidate, Interview, InterviewReminder, PasswordChangeRequest
from .forms import StaffForm, CandidateForm, InterviewForm, InterviewFeedbackForm, InterviewFilterForm, CandidateFilterForm, PasswordChangeRequestForm, AdminPasswordChangeForm, PasswordRequestFilterForm
from .permissions import role_required, can_manage_user, UserManagementMixin


class StaffManagementView(LoginRequiredMixin, UserManagementMixin, ListView):
    """Main Staff Management Dashboard"""
    model = Employee
    template_name = 'accounts/staff_management.html'
    context_object_name = 'employees'
    paginate_by = 20
    allowed_roles = ['superadmin', 'admin', 'hr']  # Allow admins, superadmins, and HR to access
    
    def get_queryset(self):
        """Filter queryset based on user role and search"""
        queryset = super().get_queryset()
        
        # Apply search filter
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(employee_id__icontains=search_query) |
                Q(position__icontains=search_query)
            )
        
        # Apply role filter
        role_filter = self.request.GET.get('role', '')
        if role_filter:
            queryset = queryset.filter(role=role_filter)
        
        # Apply status filter
        status_filter = self.request.GET.get('status', '')
        if status_filter:
            queryset = queryset.filter(employment_status=status_filter)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        """Add additional context data"""
        context = super().get_context_data(**kwargs)
        
        try:
            current_employee = self.request.user.employee
            
            # Get statistics
            context.update({
                'total_employees': self.get_queryset().count(),
                'active_employees': self.get_queryset().filter(employment_status='active').count(),
                'managers_count': self.get_queryset().filter(role='manager').count(),
                'team_leaders_count': self.get_queryset().filter(role='team_leader').count(),
                'regular_employees_count': self.get_queryset().filter(role='employee').count(),
                'leadership_count': self.get_queryset().filter(role__in=['manager', 'team_leader']).count(),
                'current_role': current_employee.role,
                'can_create_employee': current_employee.can_manage_user(Employee()),
            })
            
            # Get available managers for assignment (only for admin/superadmin)
            if current_employee.is_superadmin or current_employee.is_admin:
                context['available_managers'] = Employee.objects.filter(
                    role='manager', 
                    employment_status='active'
                )
            elif current_employee.is_manager:
                context['available_managers'] = Employee.objects.filter(
                    id=current_employee.id
                )
            else:
                context['available_managers'] = Employee.objects.none()
            
            # Get available team leaders for assignment
            if current_employee.is_superadmin or current_employee.is_admin:
                context['available_team_leaders'] = Employee.objects.filter(
                    role='team_leader', 
                    employment_status='active'
                )
            elif current_employee.is_manager:
                context['available_team_leaders'] = Employee.objects.filter(
                    reports_to=current_employee,
                    role='team_leader', 
                    employment_status='active'
                )
            else:
                context['available_team_leaders'] = Employee.objects.none()
                
        except Employee.DoesNotExist:
            context.update({
                'total_employees': 0,
                'active_employees': 0,
                'managers_count': 0,
                'team_leaders_count': 0,
                'regular_employees_count': 0,
                'leadership_count': 0,
                'current_role': 'unknown',
                'can_create_employee': False,
                'available_managers': Employee.objects.none(),
                'available_team_leaders': Employee.objects.none(),
            })
        
        # Add filter values
        context.update({
            'search_query': self.request.GET.get('search', ''),
            'role_filter': self.request.GET.get('role', ''),
            'status_filter': self.request.GET.get('status', ''),
            'role_choices': Employee.ROLES,
            'status_choices': Employee.STATUSES,
        })
        
        # Add pagination range for template
        if hasattr(context['page_obj'], 'number'):
            current_page = context['page_obj'].number
            context['page_range_start'] = max(1, current_page - 3)
            context['page_range_end'] = min(context['page_obj'].paginator.num_pages, current_page + 3)
        
        # Add edit permissions for each employee
        employees_with_permissions = []
        for employee in context['employees']:
            try:
                current_employee = self.request.user.employee
                employee_data = {
                    'employee': employee,
                    'can_edit': current_employee.can_manage_user(employee),
                }
                employees_with_permissions.append(employee_data)
            except Employee.DoesNotExist:
                employee_data = {
                    'employee': employee,
                    'can_edit': False,
                }
                employees_with_permissions.append(employee_data)
        
        context['employees_with_permissions'] = employees_with_permissions
        
        return context


@login_required
@role_required(['admin', 'superadmin', 'manager', 'hr'])
def staff_create_view(request):
    """Create new staff member"""
    if not request.user.employee.can_manage_user(Employee()):
        messages.error(request, 'You do not have permission to create staff members.')
        return redirect('accounts:staff_management')
    
    if request.method == 'POST':
        form = StaffForm(request.POST, user=request.user, is_create=True)
        if form.is_valid():
            try:
                employee = form.save()
                messages.success(request, f'Staff member {employee.full_name} created successfully!')
                return redirect('accounts:staff_management')
                
            except Exception as e:
                messages.error(request, f'Error creating staff member: {str(e)}')
    else:
        form = StaffForm(user=request.user, is_create=True)
    
    return render(request, 'accounts/employee_form_professional.html', {
        'form': form,
        'title': 'Create Staff Member',
        'action': 'Create',
    })


@login_required
@can_manage_user
def staff_update_view(request, pk):
    """Update staff member"""
    employee = get_object_or_404(Employee, pk=pk)
    
    if request.method == 'POST':
        form = StaffForm(request.POST, instance=employee, user=request.user, is_create=False)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, f'Staff member {employee.full_name} updated successfully!')
                return redirect('accounts:staff_management')
            except Exception as e:
                messages.error(request, f'Error updating staff member: {str(e)}')
    else:
        form = StaffForm(instance=employee, user=request.user, is_create=False)
    
    return render(request, 'accounts/employee_form_professional.html', {
        'form': form,
        'employee': employee,
        'title': 'Update Staff Member',
        'action': 'Update',
    })


@login_required
@can_manage_user
def staff_detail_view(request, pk):
    """View staff member details"""
    employee = get_object_or_404(Employee, pk=pk)
    
    # Get hierarchy information
    direct_reports = Employee.objects.filter(reports_to=employee, employment_status='active')
    
    # Get onboarding tasks and documents
    onboarding_tasks = employee.onboarding_tasks.all()
    documents = employee.documents.all()
    
    # Calculate onboarding progress
    total_tasks = onboarding_tasks.count()
    completed_tasks = onboarding_tasks.filter(status='completed').count()
    onboarding_progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    context = {
        'employee': employee,
        'direct_reports': direct_reports,
        'onboarding_tasks': onboarding_tasks,
        'documents': documents,
        'onboarding_progress': onboarding_progress,
        'can_edit': request.user.employee.can_manage_user(employee),
    }
    
    return render(request, 'accounts/staff_detail.html', context)


@login_required
@require_POST
@role_required(['admin', 'superadmin', 'manager', 'hr'])
def bulk_assign_employees(request):
    """Bulk assign employees to team leaders"""
    try:
        employee_ids = request.POST.getlist('employee_ids')
        team_leader_id = request.POST.get('team_leader_id')
        
        if not employee_ids:
            return JsonResponse({'success': False, 'message': 'No employees selected'})
        
        if not team_leader_id:
            return JsonResponse({'success': False, 'message': 'No team leader selected'})
        
        team_leader = get_object_or_404(Employee, pk=team_leader_id, role='team_leader')
        
        # Check permissions
        current_employee = request.user.employee
        if not current_employee.can_manage_user(team_leader):
            return JsonResponse({'success': False, 'message': 'Permission denied'})
        
        # Update employees
        employees = Employee.objects.filter(pk__in=employee_ids)
        updated_count = 0
        
        for employee in employees:
            if current_employee.can_manage_user(employee):
                employee.reports_to = team_leader
                employee.save()
                updated_count += 1
        
        return JsonResponse({
            'success': True, 
            'message': f'Successfully assigned {updated_count} employees to {team_leader.full_name}'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@require_POST
@can_manage_user
def toggle_employee_status(request, pk):
    """Toggle employee status (active/inactive)"""
    try:
        employee = get_object_or_404(Employee, pk=pk)
        
        if employee.employment_status == 'active':
            employee.employment_status = 'inactive'
            status_text = 'deactivated'
        else:
            employee.employment_status = 'active'
            status_text = 'activated'
        
        employee.save()
        
        return JsonResponse({
            'success': True, 
            'message': f'Employee {employee.full_name} {status_text} successfully'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
def staff_hierarchy_view(request):
    """View organization hierarchy"""
    try:
        current_employee = request.user.employee
        
        if current_employee.is_superadmin:
            # Show full hierarchy
            managers = Employee.objects.filter(role='manager', employment_status='active')
            team_leaders = Employee.objects.filter(role='team_leader', employment_status='active')
            employees = Employee.objects.filter(role='employee', employment_status='active')
            
            # Pre-calculate team leaders under each manager
            manager_team_leaders = {}
            for manager in managers:
                manager_team_leaders[manager.id] = team_leaders.filter(reports_to=manager)
            
            # Pre-calculate employees under each team leader
            team_leader_employees = {}
            for tl in team_leaders:
                team_leader_employees[tl.id] = employees.filter(reports_to=tl)
                
        elif current_employee.is_manager:
            # Managers see their team
            managers = Employee.objects.filter(id=current_employee.id)
            team_leaders = Employee.objects.filter(reports_to=current_employee, role='team_leader', employment_status='active')
            employees = Employee.objects.filter(reports_to__in=team_leaders, role='employee', employment_status='active')
            
            # Pre-calculate employees under each team leader
            team_leader_employees = {}
            for tl in team_leaders:
                team_leader_employees[tl.id] = employees.filter(reports_to=tl)
                
        elif current_employee.is_team_leader:
            # Team leaders see their team members
            managers = Employee.objects.none()
            team_leaders = Employee.objects.filter(id=current_employee.id)
            employees = current_employee.get_team_members()
            
            team_leader_employees = {current_employee.id: employees}
        else:
            # Employees see limited view
            managers = Employee.objects.none()
            team_leaders = Employee.objects.none()
            employees = Employee.objects.none()
            team_leader_employees = {}
            manager_team_leaders = {}
        
        context = {
            'managers': managers,
            'team_leaders': team_leaders,
            'employees': employees,
            'current_role': current_employee.role,
            'total_staff': managers.count() + team_leaders.count() + employees.count(),
            'manager_team_leaders': manager_team_leaders if 'manager_team_leaders' in locals() else {},
            'team_leader_employees': team_leader_employees,
        }
        
        return render(request, 'accounts/staff_hierarchy.html', context)
        
    except Employee.DoesNotExist:
        return render(request, 'accounts/staff_hierarchy.html', {
            'managers': Employee.objects.none(),
            'team_leaders': Employee.objects.none(),
            'employees': Employee.objects.none(),
            'current_role': 'unknown',
            'total_staff': 0,
            'manager_team_leaders': {},
            'team_leader_employees': {},
        })


# Phone Number Management Views
@login_required
@role_required(['admin', 'superadmin', 'hr'])
def phone_assignment_list(request):
    """View all phone number assignments"""
    search_query = request.GET.get('search', '')
    search_type = request.GET.get('search_type', 'all')  # all, employee, phone
    
    phone_assignments = EmployeePhone.objects.select_related('employee', 'assigned_by').all()
    
    if search_query:
        if search_type == 'employee':
            # Search by employee name or username
            phone_assignments = phone_assignments.filter(
                Q(employee__first_name__icontains=search_query) |
                Q(employee__last_name__icontains=search_query) |
                Q(employee__user__username__icontains=search_query)
            )
        elif search_type == 'phone':
            # Search by phone number
            phone_assignments = phone_assignments.filter(
                phone_number__icontains=search_query
            )
        else:
            # Search all fields
            phone_assignments = phone_assignments.filter(
                Q(phone_number__icontains=search_query) |
                Q(employee__first_name__icontains=search_query) |
                Q(employee__last_name__icontains=search_query) |
                Q(employee__user__username__icontains=search_query)
            )
    
    from django.core.paginator import Paginator
    
    # Group by employee to show latest phone number
    if search_type == 'employee':
        # Get unique employees with their latest phone number
        employees = Employee.objects.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(user__username__icontains=search_query)
        ).distinct()
        
        phone_assignments_list = []
        for employee in employees:
            latest_phone = employee.get_latest_phone_number()
            phone_assignments_list.append({
                'employee': employee,
                'phone_number': latest_phone or 'No phone assigned',
                'phone_type': 'Latest' if latest_phone else 'None',
                'is_active': bool(latest_phone and employee.phone_numbers.filter(is_active=True).exists()),
                'assigned_date': employee.phone_numbers.filter(is_active=True).order_by('-assigned_date').first().assigned_date if employee.phone_numbers.filter(is_active=True).exists() else None,
                'assigned_by': employee.phone_numbers.filter(is_active=True).order_by('-assigned_date').first().assigned_by if employee.phone_numbers.filter(is_active=True).exists() else None,
                'notes': 'Latest assigned phone number' if latest_phone else 'No phone assignment yet',
            })
        
        # Create a mock paginator for employee-wise search
        paginator = Paginator(phone_assignments_list, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'page_obj': page_obj,
            'search_query': search_query,
            'search_type': search_type,
            'is_employee_search': True,
        }
    else:
        # Normal phone assignment list
        paginator = Paginator(phone_assignments, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'page_obj': page_obj,
            'search_query': search_query,
            'search_type': search_type,
            'is_employee_search': False,
        }
    
    return render(request, 'accounts/phone_assignment_list.html', context)


@login_required
@role_required(['admin', 'superadmin', 'hr'])
def assign_phone_number(request, employee_id):
    """Assign phone number to employee"""
    # Validate employee_id
    if not employee_id or employee_id <= 0:
        messages.error(request, 'Invalid employee selected. Please select a valid employee from staff management.')
        return redirect('accounts:staff_management')
    
    try:
        employee = Employee.objects.get(id=employee_id)
    except Employee.DoesNotExist:
        messages.error(request, f'Employee with ID {employee_id} not found.')
        return redirect('accounts:staff_management')
    
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number', '').strip()
        phone_type = request.POST.get('phone_type', 'primary')
        notes = request.POST.get('notes', '')
        
        if phone_number:
            # Check if phone number already exists
            if EmployeePhone.objects.filter(phone_number=phone_number).exists():
                messages.error(request, 'This phone number is already assigned.')
            else:
                EmployeePhone.objects.create(
                    employee=employee,
                    phone_number=phone_number,
                    phone_type=phone_type,
                    notes=notes,
                    assigned_by=request.user
                )
                messages.success(request, f'Phone number {phone_number} assigned to {employee.get_full_name()}.')
        else:
            messages.error(request, 'Phone number is required.')
        
        return redirect('accounts:phone_assignment_list')
    
    context = {
        'employee': employee,
        'phone_types': EmployeePhone.PHONE_TYPES,
    }
    return render(request, 'accounts/assign_phone_form.html', context)


@login_required
@role_required(['admin', 'superadmin', 'hr'])
def assign_phone_simple(request):
    """Simplified phone assignment - select employee and assign phone in one step"""

    if request.method == 'POST':
        employee_id = request.POST.get('employee')
        phone_number = request.POST.get('phone_number', '').strip()
        phone_type = request.POST.get('phone_type', 'primary')
        notes = request.POST.get('notes', '')

        if not employee_id:
            messages.error(request, 'Please select an employee.')
            return redirect('accounts:assign_phone_simple')

        try:
            employee = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            messages.error(request, 'Selected employee not found.')
            return redirect('accounts:assign_phone_simple')

        if not phone_number:
            messages.error(request, 'Phone number is required.')
            return redirect('accounts:assign_phone_simple')

        # Check if phone number already exists
        if EmployeePhone.objects.filter(phone_number=phone_number).exists():
            messages.error(request, 'This phone number is already assigned to another employee.')
            return redirect('accounts:assign_phone_simple')

        # Create the phone assignment
        EmployeePhone.objects.create(
            employee=employee,
            phone_number=phone_number,
            phone_type=phone_type,
            notes=notes,
            assigned_by=request.user
        )

        messages.success(request, f'Phone number {phone_number} successfully assigned to {employee.get_full_name()}.')
        return redirect('accounts:phone_assignment_list')

    # GET request - show the form
    employees = Employee.objects.all().order_by('first_name', 'last_name')

    context = {
        'employees': employees,
        'phone_types': EmployeePhone.PHONE_TYPES,
    }

    return render(request, 'accounts/assign_phone_simple.html', context)


@login_required
@role_required(['admin', 'superadmin', 'hr'])
def update_phone_assignment(request, phone_id):
    """Update phone number assignment"""
    phone_assignment = get_object_or_404(EmployeePhone, id=phone_id)
    
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number', '').strip()
        phone_type = request.POST.get('phone_type', 'primary')
        notes = request.POST.get('notes', '')
        is_active = request.POST.get('is_active') == 'on'
        
        if phone_number:
            # Check if phone number already exists (excluding current)
            if EmployeePhone.objects.filter(phone_number=phone_number).exclude(id=phone_id).exists():
                messages.error(request, 'This phone number is already assigned.')
            else:
                phone_assignment.phone_number = phone_number
                phone_assignment.phone_type = phone_type
                phone_assignment.notes = notes
                phone_assignment.is_active = is_active
                phone_assignment.save()
                messages.success(request, f'Phone number assignment updated successfully.')
        else:
            messages.error(request, 'Phone number is required.')
        
        return redirect('accounts:phone_assignment_list')
    
    context = {
        'phone_assignment': phone_assignment,
        'phone_types': EmployeePhone.PHONE_TYPES,
    }
    return render(request, 'accounts/update_phone.html', context)


@login_required
@role_required(['admin', 'superadmin', 'hr'])
def delete_phone_assignment(request, phone_id):
    """Delete phone number assignment"""
    phone_assignment = get_object_or_404(EmployeePhone, id=phone_id)
    
    if request.method == 'POST':
        employee_name = phone_assignment.employee.get_full_name()
        phone_number = phone_assignment.phone_number
        phone_assignment.delete()
        messages.success(request, f'Phone number {phone_number} removed from {employee_name}.')
        return redirect('accounts:phone_assignment_list')
    
    context = {
        'phone_assignment': phone_assignment,
    }
    return render(request, 'accounts/delete_phone.html', context)


@login_required
@role_required(['admin', 'superadmin', 'hr'])
def break_management_dashboard(request):
    """Admin dashboard for monitoring all employee breaks"""
    
    # Get all active breaks (employees currently on break)
    from .models import Break, Attendance
    
    active_breaks = Break.objects.filter(
        start_time__isnull=False,
        end_time__isnull=True
    ).select_related('attendance__employee').order_by('-start_time')
    
    # Get today's breaks with exceeded duration
    today = timezone.now().date()
    today_breaks = Break.objects.filter(
        start_time__date=today
    ).select_related('attendance__employee').order_by('-start_time')
    
    exceeded_breaks = [break_record for break_record in today_breaks if break_record.is_exceeded()]
    
    # Get break statistics
    total_active_breaks = active_breaks.count()
    total_exceeded_breaks = len(exceeded_breaks)
    
    # Break type statistics
    break_stats = {}
    for break_type in ['tea_morning', 'lunch', 'tea_afternoon', 'other']:
        break_stats[break_type] = {
            'active': active_breaks.filter(break_type=break_type).count(),
            'exceeded': len([b for b in exceeded_breaks if b.break_type == break_type])
        }
    
    # Employees with most exceeded breaks this week
    week_start = today - timedelta(days=today.weekday())
    weekly_exceeded = Break.objects.filter(
        start_time__date__gte=week_start,
        start_time__isnull=False,
        end_time__isnull=False
    ).select_related('attendance__employee')
    
    weekly_exceeded = [b for b in weekly_exceeded if b.is_exceeded()]
    
    employee_violations = {}
    for break_record in weekly_exceeded:
        employee = break_record.attendance.employee
        if employee not in employee_violations:
            employee_violations[employee] = {
                'violations': 0,
                'total_exceeded_minutes': 0,
                'breaks': []
            }
        employee_violations[employee]['violations'] += 1
        employee_violations[employee]['total_exceeded_minutes'] += break_record.get_exceeded_minutes()
        employee_violations[employee]['breaks'].append(break_record)
    
    # Sort by most violations
    top_violators = sorted(
        employee_violations.items(), 
        key=lambda x: x[1]['violations'], 
        reverse=True
    )[:10]
    
    context = {
        'active_breaks': active_breaks,
        'exceeded_breaks': exceeded_breaks,
        'total_active_breaks': total_active_breaks,
        'total_exceeded_breaks': total_exceeded_breaks,
        'break_stats': break_stats,
        'top_violators': top_violators,
        'today': today,
    }
    
    return render(request, 'accounts/break_management_dashboard.html', context)


@login_required
def my_break_status(request):
    """Employee view for their own break status and warnings"""
    
    from .models import Break, Attendance
    
    employee = request.user.employee
    
    # Get today's attendance and breaks
    today = timezone.now().date()
    today_attendance = Attendance.objects.filter(
        employee=employee,
        date=today
    ).first()
    
    current_break = None
    today_breaks = []
    
    if today_attendance:
        # Get current active break
        current_break = Break.objects.filter(
            attendance=today_attendance,
            start_time__isnull=False,
            end_time__isnull=True
        ).first()
        
        # Get all today's breaks
        today_breaks = Break.objects.filter(
            attendance=today_attendance
        ).order_by('-start_time')
    
    # Check for warnings
    warning_break = None
    if current_break and current_break.is_exceeded():
        warning_break = current_break
    
    context = {
        'current_break': current_break,
        'today_breaks': today_breaks,
        'warning_break': warning_break,
        'today_attendance': today_attendance,
        'employee': employee,
    }
    
    return render(request, 'accounts/break_management_detail.html', context)


# Lead Assignment Management Views

@login_required
@role_required(['admin', 'superadmin', 'manager', 'team_leader'])
def lead_assignment_dashboard(request):
    """Lead Assignment Dashboard for different roles"""
    employee = request.user.employee
    leads = Lead.objects.all()
    
    # Filter leads based on role
    if employee.is_admin or employee.is_superadmin:
        # Admins can see all leads
        pass
    elif employee.is_manager:
        # Managers can see leads assigned to their team members AND team leaders' assigned leads
        # Get all team members (direct reports + team leaders + team leaders' reports)
        team_members = Employee.objects.filter(
            Q(reports_to=employee) | Q(reports_to__reports_to=employee),
            employment_status='active'
        )
        leads = leads.filter(assigned_to__in=team_members)
    elif employee.is_team_leader:
        # Team leaders can see leads assigned to their team members AND their own assigned leads
        team_members = Employee.objects.filter(
            reports_to=employee,
            employment_status='active'
        )
        # Include team leader's own leads and their team members' leads
        leads = leads.filter(
            Q(assigned_to__in=team_members) | Q(assigned_to=employee)
        )
    
    # Get team members for assignment dropdown
    if employee.is_admin or employee.is_superadmin:
        # Admins can see all active employees for assignment
        team_members = Employee.objects.filter(
            employment_status='active'
        ).order_by('user__first_name', 'user__last_name')
    elif employee.is_manager:
        # Managers can see their team members (direct reports + team leaders + team leaders' reports)
        team_members = Employee.objects.filter(
            Q(reports_to=employee) | Q(reports_to__reports_to=employee),
            employment_status='active'
        ).order_by('user__first_name', 'user__last_name')
    elif employee.is_team_leader:
        # Team leaders can see their team members AND employees who have leads assigned to them
        # Get direct reports
        direct_reports_ids = Employee.objects.filter(
            reports_to=employee,
            employment_status='active'
        ).values_list('id', flat=True)
        
        # Get employees who have leads assigned BY this team leader (leads where team leader is the assigner)
        employees_with_assigned_leads_ids = Lead.objects.filter(
            assigned_by=employee,
            assigned_to__employment_status='active'
        ).values_list('assigned_to_id', flat=True).distinct()
        
        # Combine all IDs and get unique employees
        all_member_ids = set(direct_reports_ids) | set(employees_with_assigned_leads_ids) | {employee.id}
        team_members = Employee.objects.filter(
            id__in=all_member_ids,
            employment_status='active'
        ).order_by('user__first_name', 'user__last_name')
        
        # Debug: Print what we found
        print(f"Team Leader: {employee.user.get_full_name()}")
        print(f"Direct reports: {len(direct_reports_ids)}")
        print(f"Employees with assigned leads: {len(employees_with_assigned_leads_ids)}")
        print(f"Total team members: {team_members.count()}")
        for member in team_members:
            print(f"  - {member.user.get_full_name()} (reports_to: {member.reports_to.user.get_full_name() if member.reports_to else 'None'})")
    else:
        team_members = Employee.objects.none()
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        leads = leads.filter(status=status_filter)
    
    # Filter by assigned employee
    assigned_to_filter = request.GET.get('assigned_to')
    if assigned_to_filter:
        leads = leads.filter(assigned_to_id=assigned_to_filter)
    
    # Pagination
    paginator = Paginator(leads, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    total_leads = leads.count()
    assigned_leads = leads.filter(assigned_to__isnull=False).count()
    unassigned_leads = leads.filter(assigned_to__isnull=True).count()
    
    context = {
        'page_obj': page_obj,
        'team_members': team_members,
        'total_leads': total_leads,
        'assigned_leads': assigned_leads,
        'unassigned_leads': unassigned_leads,
        'employee': employee,
        'status_filter': status_filter,
        'assigned_to_filter': assigned_to_filter,
    }
    
    return render(request, 'accounts/lead_assignment/dashboard.html', context)


@login_required
@role_required(['admin', 'superadmin', 'manager', 'team_leader'])
def lead_assignment_detail(request, pk):
    """Lead detail with assignment history"""
    employee = request.user.employee
    lead = get_object_or_404(Lead, pk=pk)
    
    # Check permissions
    if employee.is_manager:
        team_members = Employee.objects.filter(
            Q(reports_to=employee) | Q(reports_to__reports_to=employee),
            employment_status='active'
        )
        if lead.assigned_to and lead.assigned_to not in team_members:
            messages.error(request, 'You do not have permission to view this lead.')
            return redirect('accounts:lead_assignment_dashboard')
    elif employee.is_team_leader:
        team_members = Employee.objects.filter(
            Q(team_leader=employee) | Q(id=employee.id),
            employment_status='active'
        )
        # Team leaders can view their own leads and their team members' leads
        if lead.assigned_to and lead.assigned_to not in team_members:
            messages.error(request, 'You do not have permission to view this lead.')
            return redirect('accounts:lead_assignment_dashboard')
    
    # Get team members for reassignment
    team_members = []
    if employee.is_manager:
        team_members = Employee.objects.filter( 
            Q(reports_to=employee) | Q(reports_to__reports_to=employee),
            employment_status='active'
        ).order_by('user__first_name', 'user__last_name')
    elif employee.is_team_leader:
        # Team leaders can see their team members AND employees who have leads assigned to them
        # Get direct reports
        direct_reports_ids = Employee.objects.filter(
            reports_to=employee,
            employment_status='active'
        ).values_list('id', flat=True)
        
        # Get employees who have leads assigned BY this team leader (leads where team leader is the assigner)
        employees_with_assigned_leads_ids = Lead.objects.filter(
            assigned_by=employee,
            assigned_to__employment_status='active'
        ).values_list('assigned_to_id', flat=True).distinct()
        
        # Combine all IDs and get unique employees
        all_member_ids = set(direct_reports_ids) | set(employees_with_assigned_leads_ids) | {employee.id}
        team_members = Employee.objects.filter(
            id__in=all_member_ids,
            employment_status='active'
        ).order_by('user__first_name', 'user__last_name')
        
        # Debug: Print what we found
        print(f"Lead Detail - Team Leader: {employee.user.get_full_name()}")
        print(f"Lead Detail - Direct reports: {len(direct_reports_ids)}")
        print(f"Lead Detail - Employees with assigned leads: {len(employees_with_assigned_leads_ids)}")
        print(f"Lead Detail - Total team members: {team_members.count()}")
        for member in team_members:
            print(f"  - {member.user.get_full_name()} (reports_to: {member.reports_to.user.get_full_name() if member.reports_to else 'None'})")
    
    # Get activity logs
    activity_logs = LeadActivityLog.objects.filter(lead=lead).order_by('-created_at')
    
    context = {
        'lead': lead,
        'team_members': team_members,
        'activity_logs': activity_logs,
        'employee': employee,
    }
    
    return render(request, 'accounts/lead_assignment/detail.html', context)


@login_required
@role_required(['admin', 'superadmin', 'manager', 'team_leader'])
@require_POST
def reassign_lead(request, pk):
    """Reassign lead to different employee"""
    employee = request.user.employee
    lead = get_object_or_404(Lead, pk=pk)
    
    # Check permissions
    if employee.is_manager:
        team_members = Employee.objects.filter(
            Q(reports_to=employee) | Q(reports_to__reports_to=employee),
            employment_status='active'
        )
        if lead.assigned_to and lead.assigned_to not in team_members:
            return JsonResponse({'success': False, 'message': 'You do not have permission to reassign this lead.'})
    elif employee.is_team_leader:
        team_members = Employee.objects.filter(
            Q(team_leader=employee) | Q(id=employee.id),
            employment_status='active'
        )
        if lead.assigned_to and lead.assigned_to not in team_members:
            return JsonResponse({'success': False, 'message': 'You do not have permission to reassign this lead.'})
    
    new_employee_id = request.POST.get('assigned_to')
    if new_employee_id:
        new_employee = get_object_or_404(Employee, pk=new_employee_id)
        
        # Log reassignment details
        old_assignment = f"{lead.assigned_to.user.get_full_name()}" if lead.assigned_to else "Unassigned"
        new_assignment = f"{new_employee.user.get_full_name()}"
        reassignment_notes = request.POST.get('reassignment_notes', '')
        
        # Store old data for activity log
        old_data = {
            'assigned_to': old_assignment,
            'assigned_to_id': lead.assigned_to.id if lead.assigned_to else None,
            'status': lead.status,
            'notes': lead.notes
        }
        
        # Update lead assignment
        lead.assigned_to = new_employee
        lead.assigned_at = timezone.now()
        lead.assigned_by = employee
        lead.updated_by = employee
        if reassignment_notes:
            lead.notes = f"{lead.notes}\n\n[Reassignment Note - {timezone.now().strftime('%Y-%m-%d %H:%M')}]: {reassignment_notes}"
        lead.save()
        
        # Auto-update reporting structure if assigned to team leader
        if new_employee.is_team_leader:
            # Update all employees who have leads assigned to this team leader
            # to report to the team leader's manager
            if new_employee.reports_to:
                employees_with_leads = Lead.objects.filter(
                    assigned_to__is_staff=True,
                    assigned_to__employment_status='active'
                ).values_list('assigned_to', flat=True).distinct()
                
                Employee.objects.filter(
                    id__in=employees_with_leads,
                    reports_to__isnull=False
                ).update(reports_to=new_employee.reports_to)
        
        # If reassigning an employee's lead to a team leader, update that employee's reporting
        if lead.assigned_to and lead.assigned_to.is_team_leader:
            # Find the manager this team leader reports to
            team_leader_manager = lead.assigned_to.reports_to
            if team_leader_manager:
                # Update all employees who have leads assigned to this team leader
                # to report to the team leader's manager
                Employee.objects.filter(
                    id=lead.assigned_to.id
                ).update(reports_to=team_leader_manager)
        
        # Create comprehensive activity log
        LeadActivityLog.objects.create(
            lead=lead,
            employee=employee,
            action='reassigned',
            description=f"Lead reassigned from {old_assignment} to {new_assignment}",
            old_data=old_data,
            new_data={
                'assigned_to': new_assignment,
                'assigned_to_id': new_employee.id,
                'status': lead.status,
                'notes': lead.notes,
                'reassignment_notes': reassignment_notes
            }
        )
        
        # Create additional log for notes if provided
        if reassignment_notes:
            LeadActivityLog.objects.create(
                lead=lead,
                employee=employee,
                action='note_added',
                description=f"Reassignment note added: {reassignment_notes}",
                old_data={},
                new_data={'note': reassignment_notes}
            )
        
        return JsonResponse({
            'success': True, 
            'message': f'Lead successfully reassigned to {new_assignment}',
            'old_assignment': old_assignment,
            'new_assignment': new_assignment
        })
    
    return JsonResponse({'success': False, 'message': 'Please select an employee to assign the lead to.'})


@login_required
@role_required(['admin', 'superadmin', 'manager', 'team_leader'])
def employee_leads_view(request, employee_id):
    """View leads assigned to a specific employee"""
    current_employee = request.user.employee
    target_employee = get_object_or_404(Employee, pk=employee_id)
    
    # Check permissions
    if current_employee.is_manager:
        team_members = Employee.objects.filter(
            Q(reports_to=current_employee) | Q(reports_to__reports_to=current_employee),
            employment_status='active'
        )
        if target_employee not in team_members:
            messages.error(request, 'You do not have permission to view this employee\'s leads.')
            return redirect('accounts:lead_assignment_dashboard')
    elif current_employee.is_team_leader:
        # Team leaders can view their own leads AND their team members' leads
        team_members = Employee.objects.filter(
            Q(team_leader=current_employee) | Q(id=current_employee.id),
            employment_status='active'
        )
        
        if target_employee == current_employee:
            # Viewing own leads - always allowed
            pass
        elif target_employee not in team_members:
            messages.error(request, 'You do not have permission to view this employee\'s leads.')
            return redirect('accounts:lead_assignment_dashboard')
        
        # Get leads for team leader (own + team members)
        leads = Lead.objects.filter(
            Q(assigned_to=current_employee) | Q(assigned_to__in=team_members)
        )
    elif current_employee.is_admin or current_employee.is_superadmin:
        # Admins can view anyone's leads
        pass
    else:
        messages.error(request, 'You do not have permission to view employee leads.')
        return redirect('accounts:lead_assignment_dashboard')
    
    # Get leads for the employee
    leads = Lead.objects.filter(assigned_to=target_employee).order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        leads = leads.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(leads, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics - show counts for filtered leads
    total_leads = leads.count()
    status_counts = {}
    for status, label in Lead.LEAD_STATUS_CHOICES:
        status_counts[status] = leads.filter(status=status).count()
    
    context = {
        'page_obj': page_obj,
        'target_employee': target_employee,
        'total_leads': total_leads,
        'status_counts': status_counts,
        'status_filter': status_filter,
        'current_employee': current_employee,
    }
    
    return render(request, 'accounts/lead_assignment/employee_leads_responsive_new.html', context)


@login_required
@role_required(['admin', 'superadmin', 'manager', 'team_leader'])
@require_POST
def update_lead_status(request, pk):
    """Update lead status and notes with comprehensive logging"""
    employee = request.user.employee
    lead = get_object_or_404(Lead, pk=pk)
    
    # Check permissions - same logic as reassign_lead
    if employee.is_manager:
        team_members = Employee.objects.filter(
            Q(reports_to=employee) | Q(reports_to__reports_to=employee),
            employment_status='active'
        )
        if lead.assigned_to and lead.assigned_to not in team_members:
            return JsonResponse({'success': False, 'message': 'You do not have permission to update this lead.'})
    elif employee.is_team_leader:
        team_members = Employee.objects.filter(
            Q(team_leader=employee) | Q(id=employee.id),
            employment_status='active'
        )
        if lead.assigned_to and lead.assigned_to not in team_members:
            return JsonResponse({'success': False, 'message': 'You do not have permission to update this lead.'})
    
    # Get form data
    new_status = request.POST.get('status')
    new_notes = request.POST.get('notes', '')
    update_reason = request.POST.get('update_reason', '')
    
    # Store old data for activity log
    old_data = {
        'status': lead.status,
        'notes': lead.notes,
        'last_contacted': lead.last_contacted.isoformat() if lead.last_contacted else None
    }
    
    # Update lead fields
    updated = False
    changes = []
    
    if new_status and new_status != lead.status:
        lead.status = new_status
        changes.append(f"Status changed from {lead.get_status_display()} to {dict(Lead.LEAD_STATUS_CHOICES).get(new_status, new_status)}")
        updated = True
    
    if new_notes and new_notes != lead.notes:
        lead.notes = new_notes
        changes.append("Notes updated")
        updated = True
    
    if update_reason:
        lead.notes = f"{lead.notes}\n\n[Update Reason - {timezone.now().strftime('%Y-%m-%d %H:%M')}]: {update_reason}"
        changes.append(f"Update reason: {update_reason}")
        updated = True
    
    # Update last contacted if status indicates contact
    if new_status in ['contacted', 'interested', 'not_interested', 'follow_up']:
        lead.last_contacted = timezone.now()
        changes.append("Last contacted updated")
        updated = True
    
    if updated:
        lead.updated_by = employee
        lead.save()
        
        # Create comprehensive activity log
        LeadActivityLog.objects.create(
            lead=lead,
            employee=employee,
            action='status_changed',
            description=f"Lead updated: {', '.join(changes)}",
            old_data=old_data,
            new_data={
                'status': lead.status,
                'notes': lead.notes,
                'last_contacted': lead.last_contacted.isoformat() if lead.last_contacted else None,
                'update_reason': update_reason
            }
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Lead updated successfully',
            'changes': changes
        })
    else:
        return JsonResponse({
            'success': False,
            'message': 'No changes detected'
        })


@login_required
@role_required(['admin', 'superadmin', 'manager', 'team_leader'])
def lead_activity_logs(request, pk):
    """View detailed activity logs for a specific lead"""
    employee = request.user.employee
    lead = get_object_or_404(Lead, pk=pk)
    
    # Check permissions
    if employee.is_manager:
        team_members = Employee.objects.filter(
            Q(reports_to=employee) | Q(reports_to__reports_to=employee),
            employment_status='active'
        )
        if lead.assigned_to and lead.assigned_to not in team_members:
            messages.error(request, 'You do not have permission to view this lead\'s activity logs.')
            return redirect('accounts:lead_assignment_dashboard')
    elif employee.is_team_leader:
        team_members = Employee.objects.filter(
            Q(team_leader=employee) | Q(id=employee.id),
            employment_status='active'
        )
        if lead.assigned_to and lead.assigned_to not in team_members and lead.assigned_to != employee:
            messages.error(request, 'You do not have permission to view this lead\'s activity logs.')
            return redirect('accounts:lead_assignment_dashboard')
    
    # Get activity logs
    activity_logs = LeadActivityLog.objects.filter(lead=lead).order_by('-created_at')
    
    context = {
        'lead': lead,
        'activity_logs': activity_logs,
        'employee': employee,
    }
    
    return render(request, 'accounts/lead_assignment/activity_logs.html', context)
    
    return render(request, 'accounts/my_break_status.html', context)


# Interview Management Views
@login_required
@role_required(['admin', 'superadmin', 'hr', 'manager'])
def interview_dashboard(request):
    """Dashboard showing upcoming interviews and reminders"""
    current_employee = request.user.employee
    
    # Get upcoming interviews for next 7 days
    now = timezone.now()
    week_from_now = now + timezone.timedelta(days=7)
    
    # Interviews where current user is involved
    user_interviews = Interview.objects.filter(
        Q(primary_interviewer=current_employee) | 
        Q(interviewers=current_employee)
    ).filter(
        scheduled_date__gte=now,
        scheduled_date__lte=week_from_now,
        status='scheduled'
    ).order_by('scheduled_date')
    
    # All upcoming interviews for HR/Admin
    if current_employee.is_admin or current_employee.is_superadmin or current_employee.is_hr:
        all_interviews = Interview.objects.filter(
            scheduled_date__gte=now,
            scheduled_date__lte=week_from_now,
            status='scheduled'
        ).order_by('scheduled_date')
    else:
        all_interviews = user_interviews
    
    # Interviews needing reminders
    interviews_needing_reminders = Interview.objects.filter(
        scheduled_date__gte=now,
        scheduled_date__lte=now + timezone.timedelta(hours=24),
        status='scheduled',
        reminder_sent=False
    ).order_by('scheduled_date')
    
    # Today's interviews
    today_interviews = Interview.objects.filter(
        scheduled_date__date=now.date(),
        status='scheduled'
    ).order_by('scheduled_date')
    
    context = {
        'user_interviews': user_interviews,
        'all_interviews': all_interviews,
        'interviews_needing_reminders': interviews_needing_reminders,
        'today_interviews': today_interviews,
        'current_employee': current_employee,
    }
    
    return render(request, 'accounts/interview_dashboard.html', context)


@login_required
@role_required(['admin', 'superadmin', 'hr', 'manager'])
def candidate_list(request):
    """List all candidates"""
    current_employee = request.user.employee
    
    candidates = Candidate.objects.all()
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        candidates = candidates.filter(status=status_filter)
    
    # Filter by department
    dept_filter = request.GET.get('department')
    if dept_filter:
        candidates = candidates.filter(department=dept_filter)
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        candidates = candidates.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(position_applied__icontains=search_query) |
            Q(skills__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(candidates, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'dept_filter': dept_filter,
        'search_query': search_query,
        'current_employee': current_employee,
    }
    
    return render(request, 'accounts/candidate_list.html', context)


@login_required
@role_required(['admin', 'superadmin', 'hr', 'manager'])
def schedule_interview(request, candidate_id=None):
    """Schedule interview for a candidate"""
    current_employee = request.user.employee
    candidate = None
    
    if candidate_id:
        candidate = get_object_or_404(Candidate, pk=candidate_id)
    
    if request.method == 'POST':
        form = InterviewForm(request.POST, candidate=candidate, user=current_employee)
        if form.is_valid():
            interview = form.save(commit=False)
            interview.created_by = request.user
            interview.save()
            
            # Add interviewers
            if form.cleaned_data.get('interviewers'):
                interview.interviewers.set(form.cleaned_data['interviewers'])
            
            # Update candidate status
            if candidate:
                candidate.status = 'interview_scheduled'
                candidate.save()
            
            messages.success(request, f'Interview scheduled successfully for {candidate.full_name if candidate else "candidate"}')
            return redirect('accounts:interview_dashboard')
    else:
        form = InterviewForm(candidate=candidate, user=current_employee)
    
    context = {
        'form': form,
        'candidate': candidate,
        'current_employee': current_employee,
    }
    
    return render(request, 'accounts/schedule_interview.html', context)


@login_required
@role_required(['admin', 'superadmin', 'hr', 'manager'])
def interview_detail(request, interview_id):
    """View interview details and provide feedback"""
    current_employee = request.user.employee
    interview = get_object_or_404(Interview, pk=interview_id)
    
    # Check permissions
    if not (current_employee.is_admin or current_employee.is_superadmin or current_employee.is_hr or
              interview.primary_interviewer == current_employee or 
              current_employee in interview.interviewers.all()):
        messages.error(request, 'You do not have permission to view this interview.')
        return redirect('accounts:interview_dashboard')
    
    if request.method == 'POST':
        form = InterviewFeedbackForm(request.POST, instance=interview)
        if form.is_valid():
            form.save()
            messages.success(request, 'Interview feedback updated successfully.')
            return redirect('accounts:interview_detail', interview_id=interview_id)
    else:
        form = InterviewFeedbackForm(instance=interview)
    
    context = {
        'interview': interview,
        'form': form,
        'current_employee': current_employee,
    }
    
    return render(request, 'accounts/interview_detail.html', context)


@login_required
@role_required(['admin', 'superadmin', 'hr'])
def send_interview_reminders(request):
    """Send reminders for upcoming interviews"""
    current_employee = request.user.employee
    
    # Get interviews needing reminders
    interviews_to_remind = Interview.objects.filter(
        scheduled_date__gte=timezone.now(),
        scheduled_date__lte=timezone.now() + timezone.timedelta(hours=24),
        status='scheduled',
        reminder_sent=False
    )
    
    reminders_sent = 0
    for interview in interviews_to_remind:
        # Create reminder record
        reminder = InterviewReminder.objects.create(
            interview=interview,
            reminder_type='24h'
        )
        
        # Add all interviewers to reminder
        if interview.primary_interviewer:
            reminder.sent_to.add(interview.primary_interviewer)
        for interviewer in interview.interviewers.all():
            reminder.sent_to.add(interviewer)
        
        # Mark interview as reminder sent
        interview.send_reminder()
        reminders_sent += 1
    
    messages.success(request, f'Sent {reminders_sent} interview reminders successfully.')
    return redirect('accounts:interview_dashboard')


@login_required
@role_required(['admin', 'superadmin', 'hr', 'manager'])
def add_candidate(request):
    """Add new candidate"""
    current_employee = request.user.employee
    
    if request.method == 'POST':
        form = CandidateForm(request.POST, request.FILES)
        if form.is_valid():
            candidate = form.save(commit=False)
            candidate.created_by = request.user
            candidate.save()
            messages.success(request, f'Candidate {candidate.full_name} added successfully.')
            return redirect('accounts:candidate_list')
    else:
        form = CandidateForm()
    
    context = {
        'form': form,
        'current_employee': current_employee,
    }
    
    return render(request, 'accounts/add_candidate.html', context)


@login_required
@role_required(['admin', 'superadmin', 'hr', 'manager'])
def edit_candidate(request, candidate_id):
    """Edit candidate details"""
    current_employee = request.user.employee
    candidate = get_object_or_404(Candidate, pk=candidate_id)
    
    if request.method == 'POST':
        form = CandidateForm(request.POST, request.FILES, instance=candidate)
        if form.is_valid():
            form.save()
            messages.success(request, f'Candidate {candidate.full_name} updated successfully.')
            return redirect('accounts:candidate_list')
    else:
        form = CandidateForm(instance=candidate)
    
    context = {
        'form': form,
        'candidate': candidate,
        'current_employee': current_employee,
    }
    
    return render(request, 'accounts/edit_candidate.html', context)


# Password Change Request Views

def password_change_request(request):
    """View for users to request password change"""
    if request.method == 'POST':
        form = PasswordChangeRequestForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['email']
            reason = form.cleaned_data['reason']
            
            # Check if there's already a pending request
            existing_request = PasswordChangeRequest.objects.filter(
                user=user, 
                status='pending'
            ).first()
            
            if existing_request:
                messages.warning(request, 'You already have a pending password change request.')
                return redirect('accounts:login')
            
            # Create new password change request
            password_request = PasswordChangeRequest.objects.create(
                user=user,
                requested_by=user,
                reason=reason
            )
            
            messages.success(request, 'Your password change request has been submitted. An admin will review it shortly.')
            return redirect('accounts:login')
    else:
        form = PasswordChangeRequestForm()
    
    return render(request, 'accounts/password_change_request.html', {'form': form})


@login_required
@role_required(['admin', 'superadmin'])
def password_request_list(request):
    """View for admins to see password change requests"""
    current_employee = request.user.employee
    
    # Get filter parameters
    status_filter = request.GET.get('status')
    search_query = request.GET.get('search')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    # Start with all requests
    requests = PasswordChangeRequest.objects.all()
    
    # Apply filters
    if status_filter:
        requests = requests.filter(status=status_filter)
    
    if search_query:
        requests = requests.filter(
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query)
        )
    
    if date_from:
        requests = requests.filter(created_at__date__gte=date_from)
    
    if date_to:
        requests = requests.filter(created_at__date__lte=date_to)
    
    # Order by creation date
    requests = requests.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(requests, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Filter form
    filter_form = PasswordRequestFilterForm(request.GET)
    
    context = {
        'page_obj': page_obj,
        'filter_form': filter_form,
        'current_employee': current_employee,
        'requests_count': requests.count(),
        'pending_count': PasswordChangeRequest.objects.filter(status='pending').count(),
    }
    
    return render(request, 'accounts/password_request_list.html', context)


@login_required
@role_required(['admin', 'superadmin'])
def change_user_password(request, request_id):
    """View for admins to change user password"""
    current_employee = request.user.employee
    password_request = get_object_or_404(PasswordChangeRequest, pk=request_id)
    
    if request.method == 'POST':
        form = AdminPasswordChangeForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password']
            
            # Change the user's password
            password_request.user.set_password(new_password)
            password_request.user.save()
            
            # Mark the request as completed
            password_request.complete(request.user, 'Password changed successfully')
            
            messages.success(request, f'Password for {password_request.user.username} has been changed successfully.')
            return redirect('accounts:password_request_list')
    else:
        form = AdminPasswordChangeForm()
    
    context = {
        'form': form,
        'password_request': password_request,
        'current_employee': current_employee,
    }
    
    return render(request, 'accounts/change_user_password.html', context)


@login_required
@role_required(['admin', 'superadmin'])
def approve_password_request(request, request_id):
    """Approve a password change request"""
    password_request = get_object_or_404(PasswordChangeRequest, pk=request_id)
    
    if password_request.status == 'pending':
        password_request.approve(request.user, 'Request approved')
        messages.success(request, f'Password change request for {password_request.user.username} has been approved.')
    else:
        messages.warning(request, 'This request has already been processed.')
    
    return redirect('accounts:password_request_list')


@login_required
@role_required(['admin', 'superadmin'])
def reject_password_request(request, request_id):
    """Reject a password change request"""
    password_request = get_object_or_404(PasswordChangeRequest, pk=request_id)
    
    if request.method == 'POST':
        notes = request.POST.get('admin_notes', '')
        if password_request.status == 'pending':
            password_request.reject(request.user, notes)
            messages.success(request, f'Password change request for {password_request.user.username} has been rejected.')
        else:
            messages.warning(request, 'This request has already been processed.')
        
        return redirect('accounts:password_request_list')
    
    return render(request, 'accounts/reject_password_request.html', {'password_request': password_request})


@login_required
@role_required(['team_leader'])
def team_members(request):
    """Display all employees assigned to the team leader"""
    current_employee = request.user.employee
    
    # Get all employees who are assigned to this team leader
    team_members = Employee.objects.filter(
        team_leader=current_employee
    ).select_related('user', 'team_leader').order_by('first_name', 'last_name')
    
    # Calculate status counts
    status_counts = {
        'active': team_members.filter(employment_status='active').count(),
        'on_leave': team_members.filter(employment_status='on_leave').count(),
        'inactive': team_members.filter(employment_status='inactive').count(),
    }
    
    # Apply search filter
    search_query = request.GET.get('search', '')
    if search_query:
        team_members = team_members.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(employee_id__icontains=search_query) |
            Q(position__icontains=search_query)
        )
    
    # Apply status filter
    status_filter = request.GET.get('status', '')
    if status_filter:
        team_members = team_members.filter(employment_status=status_filter)
    
    # Pagination
    paginator = Paginator(team_members, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'team_members': page_obj,
        'current_employee': current_employee,
        'search_query': search_query,
        'status_filter': status_filter,
        'total_members': team_members.count(),
        'status_counts': status_counts,
    }
    
    return render(request, 'accounts/team_members.html', context)
