from django.shortcuts import redirect
from django.urls import resolve
from django.contrib import messages
from .models import LearnerRole, RolePermission

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