from django import template
from ..models import Violation
from datetime import timedelta
from django.utils import timezone

register = template.Library()

@register.filter
def lookup(batch_row, key):
    """
    Look up a key in a batch row's JSON data
    """
    if batch_row is None:
        return '-'
    try:
        row_data = batch_row.get_row_data()
        return row_data.get(key, '-')
    except (AttributeError, KeyError):
        return '-'

@register.filter
def get_keys(batch_row):
    """
    Get all keys from a batch row's JSON data
    """
    try:
        row_data = batch_row.get_row_data()
        return row_data.keys()
    except (AttributeError, TypeError):
        return []

@register.filter
def get_recent_violations(employees, hours=24):
    """Get recent violations for a queryset of employees within the specified hours"""
    time_threshold = timezone.now() - timedelta(hours=hours)

    # Get all employee IDs
    employee_ids = employees.values_list('id', flat=True)

    return Violation.objects.filter(
        employee_id__in=employee_ids,
        violation_time__gte=time_threshold,
        resolved=False
    ).select_related('employee').order_by('-violation_time')[:10]

@register.filter
def filter_by_status(queryset, status):
    """Filter queryset by status field"""
    return [item for item in queryset if getattr(item, 'status', None) == status]

@register.filter  
def filter_by_status_count(queryset, status):
    """Count items in queryset by status field"""
    return len([item for item in queryset if getattr(item, 'status', None) == status])
