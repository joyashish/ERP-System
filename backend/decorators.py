# backend/decorators.py

from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from .models import Tenant
from django.contrib.auth import REDIRECT_FIELD_NAME

# --- DECORATOR 1 (You already moved this) ---
def tenant_required(view_func):
    """
    Ensures a user is logged in, has a tenant, and has an active subscription.
    """
    def wrapper(request, *args, **kwargs):
        
        if not request.user.is_authenticated:
            return redirect('login') 
        
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)

        tenant = request.tenant 
        if not tenant:
            tenant = request.user.tenant 
            if not tenant:
                messages.error(request, "Your account is not associated with a company. Please contact support.")
                return redirect('login')
            request.tenant = tenant

        # ... (rest of your subscription check logic) ...
        status = tenant.subscription_status
        
        if status == 'trial':
            if not tenant.trial_ends_at or tenant.trial_ends_at < timezone.now():
                tenant.subscription_status = 'expired'
                tenant.save()
                status = 'expired'
        
        elif status == 'active':
            if not tenant.subscription_ends_at or tenant.subscription_ends_at < timezone.now():
                tenant.subscription_status = 'expired'
                tenant.save()
                status = 'expired'

        if status == 'expired':
            messages.error(request, "Your trial or subscription has expired. Please choose a plan to continue.")
            return redirect('home#pricing')

        return view_func(request, *args, **kwargs)

    return wrapper


# --- DECORATOR 2 (Move this) ---
def superadmin_required(view_func):
    """
    Decorator to ensure a user is a logged-in superadmin.
    """
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            # Not logged in, send to login page
            return redirect('login') 
        
        if request.user.is_superuser:
            # If superuser, allow access
            return view_func(request, *args, **kwargs)
        else:
            # If not superuser, show an error and redirect
            messages.error(request, "Access denied. Superadmin privileges required.")
            return redirect('dash') # Redirect to their own regular dashboard

    return wrapper


# --- DECORATOR 3 (Move this) ---
def allowed_users(allowed_roles=[]):
    """
    Decorator to restrict access based on user roles.
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')

            # Superadmin bypasses role checks
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            # Check if user's role is in the allowed list
            if request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, "You are not authorized to view this page.")
                return redirect('dash') # Redirect to their dashboard

        return wrapper
    return decorator