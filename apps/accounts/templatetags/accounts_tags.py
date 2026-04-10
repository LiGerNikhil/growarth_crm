from django import template

register = template.Library()

@register.filter
def split(value, delimiter):
    """Split string by delimiter"""
    return value.split(delimiter)

@register.filter
def first(value):
    """Get first item from list"""
    if isinstance(value, (list, tuple)):
        return value[0] if value else ''
    return value
