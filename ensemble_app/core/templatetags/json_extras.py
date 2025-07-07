from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, "")

@register.filter
def is_sequence_or_mapping(value):
    return isinstance(value, (list, dict))