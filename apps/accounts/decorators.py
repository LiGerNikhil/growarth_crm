from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def team_leader_required(view_func):
    """Decorator to require team leader role"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        
        try:
            employee = request.user.employee
            if not employee.is_team_leader:
                messages.error(request, 'Team Leader access required.')
                return redirect('core:dashboard')
        except AttributeError:
            messages.error(request, 'Employee profile not found.')
            return redirect('core:dashboard')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def manager_required(view_func):
    """Decorator to require manager role"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        
        try:
            employee = request.user.employee
            if not employee.is_manager:
                messages.error(request, 'Manager access required.')
                return redirect('core:dashboard')
        except AttributeError:
            messages.error(request, 'Employee profile not found.')
            return redirect('core:dashboard')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def admin_required(view_func):
    """Decorator to require admin or superadmin role"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        
        try:
            employee = request.user.employee
            if not (employee.is_admin or employee.is_superadmin):
                messages.error(request, 'Admin access required.')
                return redirect('core:dashboard')
        except AttributeError:
            messages.error(request, 'Employee profile not found.')
            return redirect('core:dashboard')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def mis_access_required(view_func):
    """Decorator to check if user has access to MIS module"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        
        try:
            employee = request.user.employee
            if not (employee.is_team_leader or employee.is_manager or employee.is_admin or employee.is_superadmin):
                messages.error(request, 'MIS access not permitted for your role.')
                return redirect('core:dashboard')
        except AttributeError:
            messages.error(request, 'Employee profile not found.')
            return redirect('core:dashboard')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view
