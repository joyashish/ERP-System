from django.http import Http404
from backend.models import Tenant, Account

class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if 'email' in request.session:
            account = Account.objects.filter(email=request.session['email']).first()
            if account and account.role == 'superadmin':
                request.tenant = None  # Superadmin has no tenant restriction
                request.is_superadmin = True
            else:
                # Check for tenant_id in query parameters (for testing)
                tenant_id = request.GET.get('tenant_id')
                if tenant_id:
                    try:
                        tenant = Tenant.objects.get(id=tenant_id, is_active=True)
                        request.tenant = tenant
                        request.session['tenant_id'] = tenant.id
                        request.is_superadmin = False
                    except Tenant.DoesNotExist:
                        raise Http404("Tenant not found")
                elif 'tenant_id' in request.session:
                    try:
                        tenant = Tenant.objects.get(id=request.session['tenant_id'], is_active=True)
                        request.tenant = tenant
                        request.is_superadmin = False
                    except Tenant.DoesNotExist:
                        raise Http404("Tenant not found")
                else:
                    # Fallback to subdomain (optional for production)
                    host = request.get_host().split(':')[0]
                    subdomain = host.split('.')[0]
                    try:
                        tenant = Tenant.objects.get(subdomain=subdomain, is_active=True)
                        request.tenant = tenant
                        request.session['tenant_id'] = tenant.id
                        request.is_superadmin = False
                    except Tenant.DoesNotExist:
                        raise Http404("Tenant not found")
        else:
            # Allow access to login page without tenant
            if request.path == '/':
                request.tenant = None
                request.is_superadmin = False
            else:
                raise Http404("User not authenticated")
        
        response = self.get_response(request)
        return response