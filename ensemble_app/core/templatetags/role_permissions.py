from django import template
from core.models import LearnerRole, RolePermission

register = template.Library()

@register.simple_tag(takes_context=True)
def has_role_permission(context, url_name):
    user = context['request'].user
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    roles = LearnerRole.objects.filter(learner__user=user).values_list('role', flat=True)
    return RolePermission.objects.filter(role__in=roles, url_name=url_name, has_access=True).exists()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, set())