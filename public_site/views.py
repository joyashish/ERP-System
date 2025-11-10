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
    """Serves the main landing page, now including pricing."""
    initials = ''
    if request.user.is_authenticated:
        initials = get_user_initials(request.user)
    
    # --- THIS IS THE FIX ---
    # Get the trial plan
    try:
        trial_plan = Plan.objects.get(is_trial=True)
    except Plan.DoesNotExist:
        trial_plan = None # Template will handle this

    # Get all paid plans
    paid_plans = Plan.objects.filter(is_trial=False).order_by('price')
    # ----------------------
    
    context = {
        'initials': initials,
        'trial_plan': trial_plan,
        'paid_plans': paid_plans
    }
    return render(request, 'public_site/home.html', context)


def public_logout_view(request):
    """Logs the user out and redirects to the homepage."""
    logout(request)
    messages.info(request, "You have been logged out successfully!")
    return redirect('home')

def contact_page(request):
    """Serves the contact page for enterprise sales."""
    
    if request.method == 'POST':
        # --- Handle the form data ---
        # (This is where you would add logic to email you the details)
        # For now, we just show a success message.
        messages.success(request, "Your request has been sent! Our team will contact you shortly.")
        return redirect('contact')

    context = {
        'initials': get_user_initials(request.user) if request.user.is_authenticated else ''
    }
    return render(request, 'public_site/contact.html', context)


def about_page(request):
    return render(request, 'public_site/about.html')