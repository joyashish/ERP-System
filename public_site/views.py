from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib import messages
from backend.models import Plan
from public_site.models import *

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
        try:
            # 2. GET data from the form
            # IMPORTANT: These strings (e.g., 'full_name') MUST match
            # the 'name' attribute in your contact.html <input> tags.
            
            full_name = request.POST.get('full_name')
            company_name = request.POST.get('company_name')
            email = request.POST.get('email')
            phone_number = request.POST.get('phone_number')
            team_size = request.POST.get('team_size')
            message_text = request.POST.get('message') # Use a different name to avoid conflict with 'messages' module

            # 3. (Optional but good) Basic Validation
            if not all([full_name, company_name, email, message_text]):
                messages.error(request, "Please fill out all required fields.")
                return redirect('contact') # Stay on the page with an error

            # 4. CREATE and SAVE the new object to the database
            SalesInquiry.objects.create(
                full_name=full_name,
                company_name=company_name,
                email=email,
                phone_number=phone_number,
                team_size=team_size,
                message=message_text,
            )
            
            # 5. Show success message and redirect
            messages.success(request, "Your request has been sent! Our team will contact you shortly.")
            return redirect('contact')

        except Exception as e:
            # Handle any unexpected errors
            messages.error(request, f"An error occurred. Please try again. {e}")
            return redirect('contact')

    context = {
        'initials': get_user_initials(request.user) if request.user.is_authenticated else ''
    }
    return render(request, 'public_site/contact.html', context)


def about_page(request):
    return render(request, 'public_site/about.html')