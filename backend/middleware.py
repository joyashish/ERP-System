from django.http import Http404
from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.contrib.auth import logout
from backend.models import Tenant, Account

class TenantMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if not request.user.is_authenticated:
            request.tenant = None
            return

        # --- FIX 3: Check is_superuser ---
        if request.user.is_superuser: # <--- CHECK THIS
            managed_tenant_id = request.session.get('managed_tenant_id')
            if managed_tenant_id:
                request.tenant = get_object_or_404(Tenant, id=managed_tenant_id)
            else:
                request.tenant = None
        
        # Handle Regular Admin/User
        else:
            request.tenant = request.user.tenant