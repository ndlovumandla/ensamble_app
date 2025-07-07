from .models import LearnerRole

def role_context(request):
    """
    Adds role-related context to all templates.
    """
    context = {
        'current_role': None,
        'has_learner_role': False,
        'admin_roles': [],
        'available_roles': []  # Add this to track all available roles
    }
    
    if request.user.is_authenticated:
        try:
            learner = request.user.learner_profile
            context['has_learner_role'] = bool(learner)
            
            # Get all admin roles for this user
            admin_roles = LearnerRole.objects.filter(
                learner=learner
            ).select_related('role')
            context['admin_roles'] = admin_roles
            
            # Build list of all available roles
            available_roles = ['Learner'] if context['has_learner_role'] else []
            available_roles.extend([r.role.name for r in admin_roles])
            context['available_roles'] = available_roles
            
            # Get current role from session
            current_role = request.session.get('current_role')
            
            # Validate current role
            if current_role not in available_roles:
                # Reset to first available role
                current_role = available_roles[0] if available_roles else None
                request.session['current_role'] = current_role
            
            context['current_role'] = current_role
            
        except AttributeError:
            pass
            
    return context