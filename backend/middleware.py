from django.http import Http404
from django.shortcuts import redirect
from backend.models import Tenant, Account

class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        
        # 1. Define public URLs that don't need a tenant or login.
        # Make sure these paths match your urls.py
        public_urls = ['/', '/logout/'] # Add '/admin/' if you use the Django admin
        
        # 2. Check if the current request path is public. If so, do nothing and continue.
        if request.path in public_urls:
            return self.get_response(request)
            
        # 3. For all other private pages, the user must be logged in.
        if 'email' not in request.session:
            # If not logged in, redirect to the login page.
            return redirect('/')

        # 4. Find the account and check if it's a superadmin.
        account = Account.objects.filter(email=request.session['email']).first()
        
        if not account:
            # If account in session doesn't exist in DB, force logout.
            request.session.flush()
            return redirect('/')

        if account.role == 'superadmin':
            request.tenant = None
            request.is_superadmin = True
        else:
            # 5. If it's a regular user, they MUST have a tenant in their session.
            request.is_superadmin = False
            tenant_id = request.session.get('tenant_id')
            
            if not tenant_id:
                # This shouldn't happen for a logged-in user, but as a safeguard:
                raise Http404("User has no assigned tenant. Please contact support.")

            try:
                request.tenant = Tenant.objects.get(id=tenant_id, is_active=True)
            except Tenant.DoesNotExist:
                # Tenant was deleted or deactivated while user was logged in.
                raise Http404("Tenant not found or is inactive.")
                
        # If all checks pass, continue to the view.
        return self.get_response(request)