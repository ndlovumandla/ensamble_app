from django import template

register = template.Library()

@register.filter
def unique_by_service(sla_qualifications):
    seen = set()
    result = []
    for qual in sla_qualifications:
        service_id = getattr(qual.service, 'id', None)
        if service_id and service_id not in seen:
            seen.add(service_id)
            result.append(qual)
    return result