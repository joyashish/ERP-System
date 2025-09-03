from .models import Tenant

def tenant_list_for_superadmin(request):
    """
    Adds a list of all tenants to the context if the logged-in user is a superadmin.
    """
    # First, ensure the user is authenticated and has a role attribute
    if request.user.is_authenticated and hasattr(request.user, 'role'):
        if request.user.role == 'superadmin':
            tenants = Tenant.objects.filter(is_active=True).order_by('name')
            return {'all_tenants_for_superadmin': tenants}
    
    return {}
    
def impersonation_context(request):
    """
    Adds the 'impersonator' object to the context if an impersonation
    session is active.
    """
    return {
        'impersonator': getattr(request, 'impersonator', None)
    }