from django.shortcuts import redirect
from django.urls import resolve, reverse
from django.contrib import messages
from .models import LearnerRole, RolePermission
from core.models import LIF

class PermissionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Always allow access to login, admin, and static files
        path = request.path_info
        if path.startswith('/admin/') or path.startswith('/static/') or \
           path.startswith('/media/') or path == '/login/':
            return self.get_response(request)

        # If user is not authenticated, continue normally
        if not request.user.is_authenticated:
            return self.get_response(request)

        # If user is superuser, allow everything
        if request.user.is_superuser:
            return self.get_response(request)

        # Get current URL name
        try:
            url_name = resolve(path).url_name
        except:
            return self.get_response(request)

        # Check if user has permission through their roles
        try:
            learner_roles = LearnerRole.objects.filter(
                learner__user=request.user
            ).select_related('role')
            
            has_permission = RolePermission.objects.filter(
                role__in=[lr.role for lr in learner_roles],
                url_name=url_name,
                has_access=True
            ).exists()

            if has_permission:
                return self.get_response(request)
            else:
                messages.error(request, 'You do not have permission to access this page.')
                return redirect('home')
        except:
            return self.get_response(request)

        return self.get_response(request)

class LearnerLIFMiddleware:
    """
    Enforce LIF completion ONLY if current role is 'Learner'.
    - If no LIF: force to fill and sign before using the site.
    - If LIF exists but has missing/blank required fields: show warning, but allow access.
    - If user is acting as another role (Facilitator, Project, etc), do NOT enforce.
    - Always allow access to LIF form, logout, and role switcher.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only check for authenticated users with a learner_profile
        if request.user.is_authenticated and hasattr(request.user, 'learner_profile'):
            current_role = request.session.get('current_role')

            # Build allowed paths robustly
            allowed_paths = {
                reverse('lif_form'),
                reverse('logout'),
            }
            # Add role switcher by name if it exists
            try:
                allowed_paths.add(reverse('switch_role'))
            except:
                allowed_paths.add('/switch_role/')
                allowed_paths.add('/switch_role')

            # Allow access to allowed paths (strip trailing slashes for safety)
            req_path = request.path.rstrip('/')
            allowed_paths = {p.rstrip('/') for p in allowed_paths}
            if req_path in allowed_paths:
                return self.get_response(request)

            # Allow non-learner roles to bypass LIF enforcement
            if current_role and current_role.lower() != 'learner':
                return self.get_response(request)

            learner = request.user.learner_profile
            lif = getattr(learner, 'lif_form', None)
            if not lif:
                messages.error(request, "You must complete and sign your Learner Information Form (LIF) before continuing.")
                return redirect(f"{reverse('lif_form')}?learner_id={learner.id}")
            missing_fields = []
            for field in LIF._meta.fields:
                if field.name in ['id', 'learner', 'consent_to_process']:
                    continue
                if not field.blank and not field.null:
                    value = getattr(lif, field.name)
                    if value in [None, '', False]:
                        missing_fields.append(field.verbose_name)
            if missing_fields:
                messages.warning(
                    request,
                    "Your LIF is missing the following required fields: " +
                    ", ".join(missing_fields) +
                    ". Please update your LIF."
                )
            if not lif.consent_to_process:
                messages.error(request, "You must provide consent in your LIF before continuing.")
                return redirect(f"{reverse('lif_form')}?learner_id={learner.id}")
        return self.get_response(request)