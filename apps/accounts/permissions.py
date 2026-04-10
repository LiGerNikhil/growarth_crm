from functools import wraps
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from .models import Employee


def role_required(allowed_roles):
    """
    Decorator to check if user has required role
    Usage: @role_required(['manager', 'superadmin'])
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            try:
                employee = request.user.employee
                # Superadmin has access to everything
                if employee.is_superadmin:
                    return view_func(request, *args, **kwargs)
                if employee.role in allowed_roles:
                    return view_func(request, *args, **kwargs)
                else:
                    messages.error(request, 'You do not have permission to access this page.')
                    return redirect('core:dashboard')
            except Employee.DoesNotExist:
                messages.error(request, 'Employee profile not found. Please contact administrator.')
                return redirect('core:dashboard')
        return _wrapped_view
    return decorator


def can_manage_user(view_func):
    """
    Decorator to check if user can manage specific user
    Expects user_id or pk parameter in URL
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, user_id=None, pk=None, *args, **kwargs):
        try:
            current_employee = request.user.employee
            
            # Get target user ID from URL parameters
            target_user_id = user_id or pk
            if not target_user_id:
                messages.error(request, 'User ID not provided.')
                return redirect('accounts:staff_management')
            
            target_user = Employee.objects.get(id=target_user_id)
            
            if current_employee.can_manage_user(target_user):
                return view_func(request, target_user_id, *args, **kwargs)
            else:
                messages.error(request, 'You do not have permission to manage this user.')
                return redirect('accounts:staff_detail', pk=target_user_id)
                
        except Employee.DoesNotExist:
            messages.error(request, 'User not found.')
            return redirect('accounts:staff_management')
    
    return _wrapped_view


def can_view_user(view_func):
    """
    Decorator to check if user can view specific user
    Expects user_id or pk parameter in URL
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, user_id=None, pk=None, *args, **kwargs):
        try:
            current_employee = request.user.employee
            
            # Get target user ID from URL parameters
            target_user_id = user_id or pk
            if not target_user_id:
                messages.error(request, 'User ID not provided.')
                return redirect('accounts:staff_management')
            
            target_user = Employee.objects.get(id=target_user_id)
            
            if current_employee.can_view_user(target_user):
                return view_func(request, target_user_id, *args, **kwargs)
            else:
                messages.error(request, 'You do not have permission to view this user.')
                return redirect('accounts:staff_management')
                
        except Employee.DoesNotExist:
            messages.error(request, 'User not found.')
            return redirect('accounts:staff_management')
    
    return _wrapped_view


class RoleRequiredMixin:
    """
    Mixin for class-based views to check user role
    """
    allowed_roles = []
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        
        try:
            employee = request.user.employee
            # Superadmin has access to everything
            if employee.is_superadmin:
                return super().dispatch(request, *args, **kwargs)
            if employee.role in self.allowed_roles:
                return super().dispatch(request, *args, **kwargs)
            else:
                messages.error(request, 'You do not have permission to access this page.')
                return redirect('core:dashboard')
        except Employee.DoesNotExist:
            messages.error(request, 'Employee profile not found. Please contact administrator.')
            return redirect('accounts:login')


class UserManagementMixin:
    """
    Mixin for views that manage users with hierarchy checks
    """
    
    def get_queryset(self):
        """Filter queryset based on user role"""
        try:
            employee = self.request.user.employee
            
            # Superadmin gets access to ALL users
            if employee.is_superadmin:
                return Employee.objects.all()
                
            return employee.get_accessible_users()
        except Employee.DoesNotExist:
            return Employee.objects.none()
    
    def get_form(self, form_class=None):
        """Customize form based on user role"""
        form = super().get_form(form_class)
        
        try:
            current_employee = self.request.user.employee
            
            # Superadmin gets full control over all form fields
            if current_employee.is_superadmin:
                return form
            
            # Limit role choices based on current user role
            if current_employee.is_manager:
                form.fields['role'].choices = [
                    choice for choice in Employee.ROLES 
                    if choice[0] in ['team_leader', 'employee']
                ]
            elif current_employee.is_team_leader:
                form.fields['role'].choices = [
                    choice for choice in Employee.ROLES 
                    if choice[0] == 'employee'
                ]
            else:
                form.fields['role'].choices = [
                    choice for choice in Employee.ROLES 
                    if choice[0] == 'employee'
                ]
            
            # Filter manager choices
            if current_employee.is_superadmin:
                form.fields['manager'].queryset = Employee.objects.filter(
                    role='manager', employment_status='active'
                )
            else:
                form.fields['manager'].queryset = Employee.objects.none()
            
            # Filter team leader choices
            if current_employee.is_superadmin:
                form.fields['team_leader'].queryset = Employee.objects.filter(
                    role='team_leader', employment_status='active'
                )
            elif current_employee.is_manager:
                form.fields['team_leader'].queryset = Employee.objects.filter(
                    manager=current_employee, role='team_leader', employment_status='active'
                )
            else:
                form.fields['team_leader'].queryset = Employee.objects.none()
                
        except Employee.DoesNotExist:
            pass
        
        return form


def require_permission(permission_func):
    """
    Generic permission decorator that takes a permission function
    Usage: @require_permission(lambda u: u.is_manager)
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            try:
                employee = request.user.employee
                if permission_func(employee):
                    return view_func(request, *args, **kwargs)
                else:
                    messages.error(request, 'You do not have permission to access this page.')
                    return redirect('core:dashboard')
            except Employee.DoesNotExist:
                messages.error(request, 'Employee profile not found. Please contact administrator.')
                return redirect('accounts:login')
        return _wrapped_view
    return decorator
