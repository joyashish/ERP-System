from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib import messages
from backend.models import Plan

def get_user_initials(user):
    """Helper function to get user initials."""
    if user.full_name:
        parts = user.full_name.split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[-1][0]).upper()
        elif len(parts) == 1 and len(parts[0]) > 0:
            return parts[0][0].upper()
    
    if user.email:
        return user.email[0].upper()
    
    return '?'

def home_page(request):
    """Serves the main landing page."""
    initials = ''
    if request.user.is_authenticated:
        initials = get_user_initials(request.user)
    
    context = {
        'initials': initials
    }
    return render(request, 'public_site/home.html', context)


def public_logout_view(request):
    """Logs the user out and redirects to the homepage."""
    logout(request)
    messages.info(request, "You have been logged out successfully!")
    return redirect('home')


def about_page(request):
    return render(request, 'public_site/about.html')