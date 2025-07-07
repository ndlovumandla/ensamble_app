from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Usage: {{ dict|get_item:key }}"""
    return dictionary.get(key)

@register.filter(name='dict_get')
def dict_get(d, key):
    try:
        return d.get(key, None)
    except AttributeError:
        return None

@register.simple_tag
def url_replace(request, field, value):
    """Usage: {% url_replace request 'field' 'value' %}"""
    dict_ = request.GET.copy()
    dict_[field] = value
    return dict_.urlencode()

@register.filter
def split_by(value, delimiter):
    """Split a string by the given delimiter."""
    return value.split(delimiter)