from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """دسترسی به مقدار دیکشنری با کلید"""
    return dictionary.get(key)
