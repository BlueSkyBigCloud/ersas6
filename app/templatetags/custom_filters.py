from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, 0)


@register.filter
def index(lst, i):
    """Returns the item at index i from list lst."""
    try:
        return lst[i]
    except (IndexError, TypeError):
        return 0
    

@register.filter
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0