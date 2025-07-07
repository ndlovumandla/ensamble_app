from django import template
register = template.Library()

@register.filter
def get(d, key):
    if isinstance(d, dict):
        return d.get(key, "")
    return ""

@register.filter
def pluck(qs, attr):
    return [getattr(x, attr) for x in qs]

@register.filter
def get_item(dictionary, key):
    if isinstance(dictionary, dict):
        return dictionary.get(key, "")
    return ""