from django.urls import resolve, reverse
from django.shortcuts import redirect
from django.contrib import messages
from .models import LearnerRole, RolePermission

class RolePermissionRequiredMixin:
    """
    Mixin to check if the user has permission to access the current view.
    """
    def dispatch(self, request, *args, **kwargs):
        # Redirect anonymous users to login
        if not request.user.is_authenticated:
            return redirect('%s?next=%s' % (reverse('login'), request.path))
            
        # Allow superusers
        if request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)

        # Get current role from session
        current_role = request.session.get('current_role')
        
        # Check if user has the current role
        try:
            learner = request.user.learner_profile
            has_role = LearnerRole.objects.filter(
                learner=learner,
                role__name=current_role
            ).exists()
            
            if not has_role and current_role != 'Learner':
                messages.error(request, f"You don't have access to the {current_role} role")
                return redirect('home_redirect')
                
        except AttributeError:
            messages.error(request, "No learner profile found")
            return redirect('home_redirect')

        # Get current url_name
        url_name = resolve(request.path_info).url_name
        
        # For learner views, check if user has a learner profile
        learner_views = {'learner_home', 'learner_assessment_results', 'poe_submission', 'poe_list'}
        if url_name in learner_views:
            if current_role == 'Learner':
                return super().dispatch(request, *args, **kwargs)
            messages.error(request, "Please switch to Learner role to access this page")
            return redirect('home_redirect')
            
        # For other views, check role permissions
        try:
            roles = LearnerRole.objects.filter(
                learner=learner,
                role__name=current_role
            ).values_list('role', flat=True)
            
            if RolePermission.objects.filter(
                role__in=roles, 
                url_name=url_name, 
                has_access=True
            ).exists():
                return super().dispatch(request, *args, **kwargs)
        except AttributeError:
            pass
            
        messages.error(request, "You don't have permission to access this page")
        return redirect('home_redirect')