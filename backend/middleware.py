from django.http import Http404
from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.contrib.auth import logout
from backend.models import Tenant, Account

class TenantMiddleware(MiddlewareMixin):
    def process_request(self, request):
        """
        This middleware's only job is to attach the correct tenant to
        an authenticated user's request.
        All redirect logic is now handled by the @tenant_required decorator.
        """
        if not request.user.is_authenticated:
            request.tenant = None
            return

        # Use is_superuser to check for superadmin
        if request.user.is_superuser:
            managed_tenant_id = request.session.get('managed_tenant_id')
            if managed_tenant_id:
                request.tenant = get_object_or_404(Tenant, id=managed_tenant_id)
            else:
                request.tenant = None
        
        # Handle Regular Admin/User
        else:
            request.tenant = request.user.tenant