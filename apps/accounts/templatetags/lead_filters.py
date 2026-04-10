from django import template

register = template.Library()

@register.filter
def filter_status(queryset, status):
    """Filter forwarded leads by status"""
    return queryset.filter(status=status)

@register.filter
def status_color(status):
    """Return Bootstrap color class for lead status"""
    status_colors = {
        'new': 'primary',
        'contacted': 'info',
        'interested': 'success',
        'not_interested': 'secondary',
        'not_eligible': 'warning',
        'converted': 'success',
        'follow_up': 'warning',
        'file_login': 'info',
        'amount_disbursed': 'success',
    }
    return status_colors.get(status, 'secondary')

@register.filter
def action_color(action):
    """Return Bootstrap color class for lead action"""
    action_colors = {
        'created': 'primary',
        'updated': 'info',
        'reassigned': 'warning',
        'status_changed': 'success',
        'contacted': 'info',
        'note_added': 'secondary',
    }
    return action_colors.get(action, 'secondary')

@register.filter
def replace_spaces(value, replacement=' '):
    """Replace spaces in string"""
    if value is None:
        return ''
    return str(value).replace(' ', replacement)
