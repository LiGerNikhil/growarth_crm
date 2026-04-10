from django import template
from ..models import Violation
from datetime import timedelta
from django.utils import timezone

register = template.Library()

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
