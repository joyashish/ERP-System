from django.http import Http404
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth import logout
from backend.models import Tenant, Account

class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Impersonation check remains the same
        impersonator_id = request.session.get('impersonator_id')
        if impersonator_id:
            try:
                request.impersonator = Account.objects.get(id=impersonator_id)
            except Account.DoesNotExist:
                del request.session['impersonator_id']
        else:
            request.impersonator = None

        public_urls = ['/', '/logout/', '/impersonate/stop/']
        
        if request.path in public_urls:
            return self.get_response(request)
            
        # 1. For all private pages, check if a user is authenticated.
        if not request.user.is_authenticated:
            return redirect('/')

        # 2. Get the account directly from request.user.
        account = request.user
        
        # 3. Handle superadmin case.
        if account.role == 'superadmin':
            request.tenant = None
            request.is_superadmin = True
        else:
            # 4. For regular users, get the tenant DIRECTLY from their account.
            request.is_superadmin = False
            tenant = account.tenant
            
            if not tenant:
                # This user has no company assigned, which is an error.
                logout(request)
                messages.error(request, "Your account is not associated with a company. Please contact support.")
                return redirect('/')
            
            if not tenant.is_active:
                # The user's company account has been deactivated.
                logout(request)
                messages.error(request, "Your company's account has been deactivated. Please contact support.")
                return redirect('/')

            request.tenant = tenant
                
        return self.get_response(request)