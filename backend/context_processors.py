from .models import Tenant
from public_site.models import SalesInquiry

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

def new_inquiry_context(request):
    """
    Provides the count of new (unread) sales inquiries to all templates.
    """
    if request.user.is_authenticated and request.user.is_superuser:
        try:
            # Count only inquiries with the status 'NEW'
            count = SalesInquiry.objects.filter(status=SalesInquiry.STATUS_NEW).count()
            return {'new_inquiry_count': count}
        except Exception:
            # In case the database/table doesn't exist yet
            return {'new_inquiry_count': 0}

    return {'new_inquiry_count': 0}