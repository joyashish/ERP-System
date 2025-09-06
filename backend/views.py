from django.shortcuts import render,redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from backend.models import *
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate, login, logout
from django.db.models import Sum, F
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import datetime
from datetime import timedelta
from django.db import transaction
import uuid
import re
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate, login
from django.db.models import OuterRef, Subquery
from django.db import IntegrityError
from django.db.models import Sum, Count, Q
import json
from decimal import Decimal
from django.db.models.functions import TruncMonth
from dateutil.relativedelta import relativedelta
from django.urls import reverse
from django.template.loader import get_template
from xhtml2pdf import pisa




# Permission Decorators
def superadmin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('email') or not Account.objects.filter(email=request.session['email'], role='superadmin').exists():
            messages.error(request, "Access denied. Superadmin privileges required.")
            return redirect('/')
        return view_func(request, *args, **kwargs)
    return wrapper

def tenant_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('email'):
            return redirect('/')
        account = Account.objects.filter(email=request.session['email']).first()
        if account.role == 'superadmin':
            return view_func(request, *args, **kwargs)
        if not request.session.get('tenant_id'):
            return redirect('/')
        return view_func(request, *args, **kwargs)
    return wrapper

# Helper to get tenant
def get_tenant(request):
    if request.is_superadmin:
        tenant_id = request.GET.get('tenant_id') or request.POST.get('tenant_id')
        if tenant_id:
            return get_object_or_404(Tenant, id=tenant_id)
    return getattr(request, 'tenant', None)

# Print View
def printVw(request):
    return render(request, 'print.html')

# Add Unit
@tenant_required
def add_unit(request):
    tenant = get_tenant(request)
    account = Account.objects.filter(email=request.session['email']).first()
    
    if request.method == 'POST':
        unit_name = request.POST.get('unit_name')
        if unit_name:
            Unit.objects.create(name=unit_name, tenant=tenant)
    return redirect('/Create_item')

# Add Category
@tenant_required
def add_category(request):
    tenant = get_tenant(request)
    account = Account.objects.filter(email=request.session['email']).first()
    
    if request.method == 'POST':
        cat_name = request.POST.get('cat_name')
        if cat_name:
            Category.objects.create(cname=cat_name, tenant=tenant)
    return redirect('/Create_item')

# Admin Login View
# def Admin_loginVW(request):
#     if request.method == "POST":
#         email = request.POST.get('email')
#         password = request.POST.get('pass')
#         account = authenticate(request, username=email, password=password)
#         if account and account.is_active:
#             request.session['email'] = account.email
#             request.session['account_id'] = account.id
#             if account.role != 'superadmin':
#                 request.session['tenant_id'] = account.tenant.id
#             return redirect('/dash')
#         messages.error(request, "Invalid Email or Password")
#         return redirect('/')
#     return render(request, 'Admin_login.html')


def Admin_loginVW(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('pass')
        
        # This uses your auth_backend.py to find the user and check the password
        account = authenticate(request, username=email, password=password)
        
        # Check if authentication was successful
        if account is not None:
            
            # 1. Call login() FIRST. This is crucial for firing the user_logged_in signal
            #    and setting up Django's proper session management.
            login(request, account) 
            
            # 2. THEN, manually set the 'email' session key that your middleware is looking for.
            #    This ensures the middleware will find the user on the next request.
            request.session['email'] = account.email
            
            # 3. Set the tenant_id for regular users, as you did before.
            # Check the account's role and redirect accordingly.
            if account.role == 'superadmin':
                # If the user is a superadmin, go to the superadmin dashboard.
                return redirect('/superadmin_dashboard')
            else:
                # For all other roles (admin, user), go to the regular dashboard.
                request.session['tenant_id'] = account.tenant.id
                return redirect('/dash')
            
        # If authentication fails, the account will be None
        messages.error(request, "Invalid Email or Password")
        return redirect('/')
        
    return render(request, 'Admin_login.html')

def logout_view(request): # Renamed to avoid conflict with the imported logout
    # Use Django's logout function for proper session clearing
    logout(request)
    messages.info(request, "You have been logged out successfully!")
    return redirect('/')

# Dashboard View
@tenant_required
def DashVw(request):
    account = Account.objects.filter(email=request.session['email']).first()
    tenant = get_tenant(request) if not account.role == 'superadmin' else None
    return render(request, 'Dash.html', {'add': account, 'tenant': tenant})

# Logout View
# def logout(request):
#     request.session.flush()
#     messages.info(request, "Logout Successfully!!")
#     return redirect('/')

# Change Password View
@tenant_required
def ChangePasswordVw(request):
    account = Account.objects.filter(email=request.session['email']).first()
    tenant = get_tenant(request) if not account.role == 'superadmin' else None
    
    if request.method == 'POST':
        password = request.POST.get('password')
        account.password = make_password(password)
        account.save()
        messages.info(request, 'Password has been changed Successfully!! Login Again for better experience !!')
        return redirect('/')
    return render(request, 'change_pass.html', {'data': account, 'add': account, 'tenant': tenant})



# Create Party View
@tenant_required
def Create_partyVw(request):
    account = Account.objects.get(email=request.session['email'])
    
    if request.method == "POST":
        target_tenant = None
        # Determine the correct tenant to assign the party to
        if account.role == 'superadmin':
            tenant_id = request.POST.get('tenant_id')
            if not tenant_id:
                messages.error(request, "Superadmin must select a tenant.")
                return redirect('Create_Party')
            target_tenant = get_object_or_404(Tenant, id=tenant_id)
        else:
            # For regular users, the tenant is set by middleware
            target_tenant = request.tenant

        party_name = request.POST.get('pname')
        # Check for duplicates within the correct tenant
        if Create_party.objects.filter(party_name=party_name, tenant=target_tenant).exists():
            messages.warning(request, f"Party '{party_name}' already exists for this tenant.")
        else:
            Create_party.objects.create(
                tenant=target_tenant,  # Use the identified target tenant
                user=account,
                party_name=party_name,
                mobile_num=request.POST.get('pnum'),
                email=request.POST.get('pemail'),
                opening_balance=request.POST.get('op_bal', 0),
                gst_no=request.POST.get('gst_in'),
                pan_no=request.POST.get('pan_no'),
                party_type=request.POST.get('p_type'),
                party_category=request.POST.get('p_category'),
                billing_address=request.POST.get('billing_address'),
                shipping_address=request.POST.get('shipping_address'),
                credit_period=request.POST.get('credit_period', 0),
                credit_limit=request.POST.get('credit_limit', 0),
                is_active=True
            )
            messages.success(request, 'Party Added Successfully.')
        
        # Redirect based on who is logged in
        if account.role == 'superadmin':
             return redirect(f"/Party_list?tenant_id={target_tenant.id}")
        else:
             return redirect('Party_list')
        
    # For GET request, prepare context
    context = {'add': account}
    if account.role == 'superadmin':
        context['tenants'] = Tenant.objects.all()
        # Pre-select tenant if coming from a tenant-specific page
        context['tenant_id_from_url'] = request.GET.get('tenant_id')

    return render(request, 'Create_party.html', context)

# Party List View
@tenant_required
def Party_listVw(request):
    account = Account.objects.filter(email=request.session['email']).first()
    
    if account.role == 'superadmin':
        tenant_id = request.GET.get('tenant_id')
        tenant = None
        party_list = Create_party.objects.none() # Default to an empty list

        if tenant_id:
            try:
                tenant = Tenant.objects.get(id=tenant_id)
                party_list = Create_party.objects.filter(tenant=tenant, is_active=True)
            except Tenant.DoesNotExist:
                # Handle case where an invalid tenant_id is passed
                pass 
    else:
        # This logic for regular users is correct and remains the same
        tenant = get_object_or_404(Tenant, id=request.session['tenant_id'])
        party_list = Create_party.objects.filter(tenant=tenant, is_active=True)

    total_balance = party_list.aggregate(total=Sum('opening_balance'))['total'] or 0.00
    total_credit = party_list.aggregate(total=Sum('credit_limit'))['total'] or 0.00
    
    context = {
        'party_list': party_list,
        'total_parties': party_list.count(),
        'total_balance': total_balance,
        'total_credit': total_credit,
        'add': account,
        'tenant': tenant, # Pass the specific tenant to the template
    }
    return render(request, 'Party_list.html', context)

# Delete Party View
@tenant_required
def Dlt_Party_ListVw(request, id):
    account = Account.objects.filter(email=request.session['email']).first()
    # tenant = get_tenant(request) if not account.role == 'superadmin' else None
    
    # Get the party first to preserve tenant info
    if account.role == 'superadmin':
        party = get_object_or_404(Create_party, id=id)
    else:
        party = get_object_or_404(Create_party, id=id, tenant=request.tenant)
    
    if party:
        party.is_active = False
        party.save()
        messages.info(request, 'Party Deleted!')
        
        # Redirect based on who is logged in
        if account.role == 'superadmin':
            return redirect(f"/Party_list?tenant_id={party.tenant.id}")
        else:
            return redirect('/Party_list')
    else:
        messages.error(request, 'Party not found!')
        return redirect('/Party_list')

# Update Party View
@tenant_required
def Updt_Party_List(request, id):
    account = Account.objects.filter(email=request.session['email']).first()
    # tenant = get_tenant(request) if not account.role == 'superadmin' else None
    
    # Use get_object_or_404 to fetch the single party object we want to update
    party_to_update = get_object_or_404(Create_party, id=id)
    
    # Security check: Ensure user has permission to edit this party
    if account.role != 'superadmin' and party_to_update.tenant != request.tenant:
        messages.error(request, "You are not authorized to edit this party.")
        return redirect('Party_list')
    
    if request.method == "POST":
        # Update the object with data from the form
        party_to_update.party_name = request.POST.get('pname')
        party_to_update.mobile_num = request.POST.get('pnum')
        party_to_update.email = request.POST.get('pemail')
        party_to_update.opening_balance = request.POST.get('op_bal', 0)
        party_to_update.gst_no = request.POST.get('gst_in')
        party_to_update.pan_no = request.POST.get('pan_no')
        party_to_update.party_type = request.POST.get('p_type')
        party_to_update.party_category = request.POST.get('p_category')
        party_to_update.billing_address = request.POST.get('billing_address')
        party_to_update.shipping_address = request.POST.get('shipping_address')
        party_to_update.credit_period = request.POST.get('credit_period', 0)
        party_to_update.credit_limit = request.POST.get('credit_limit', 0)

        party_to_update.save()
        messages.info(request, 'Party Update Successfully.')
        
        # Redirect based on who is logged in
        if account.role == 'superadmin':
            # Get the tenant_id from the party being updated
            return redirect(f"{reverse('Party_list')}?tenant_id={party_to_update.tenant.id}")
        else:
            return redirect('Party_list')
    
    # For GET request, pass tenant_id to template for potential use
    context = {'add': account, 'party': party_to_update, 'tenant': party_to_update.tenant}
    return render(request, 'Update_party.html', context)
    
# Party Details View
@tenant_required
def party_detail_view(request, party_id):
    account = request.user
    party = get_object_or_404(Create_party, id=party_id)

    # Security check: Ensure user has permission
    if account.role != 'superadmin' and party.tenant != request.tenant:
        messages.error(request, "You are not authorized to view this party.")
        return redirect('Party_list')

    # Fetch related sales and calculate financial totals
    sales = Sale.objects.filter(party=party).order_by('-invoice_date')
    financials = sales.aggregate(
        total_sales=Sum('total_amount'),
        total_paid=Sum('amount_received')
    )
    total_sales = financials.get('total_sales') or 0
    total_paid = financials.get('total_paid') or 0
    balance_due = total_sales - total_paid

    context = {
        'add': account,
        'party': party,
        'sales': sales,
        'total_sales': total_sales,
        'total_paid': total_paid,
        'balance_due': balance_due,
    }
    return render(request, 'party_detail.html', context)

# Item List View
@tenant_required
def item_list_view(request):
    account = Account.objects.filter(email=request.session['email']).first()
    tenant = None
    products = Product.objects.none()
    services = Service.objects.none()

    # Determine tenant context
    if account.role == 'superadmin':
        tenant_id = request.GET.get('tenant_id')
        if tenant_id:
            try:
                tenant = Tenant.objects.get(id=tenant_id)
                products = Product.objects.filter(tenant=tenant)
                services = Service.objects.filter(tenant=tenant)
            except Tenant.DoesNotExist:
                pass
    else:
        tenant = get_object_or_404(Tenant, id=request.session['tenant_id'])
        products = Product.objects.filter(tenant=tenant)
        services = Service.objects.filter(tenant=tenant)
    
    # --- NEW: Get and apply the filter from the URL ---
    item_filter = request.GET.get('filter')
    
    products_to_display = products
    services_to_display = services

    filter_display_name = ''
    if item_filter == 'products_only':
        services_to_display = services.none()
        filter_display_name = 'Products Only'
    elif item_filter == 'services_only':
        products_to_display = products.none()
        filter_display_name = 'Services Only'
    elif item_filter == 'expiring_soon':
        today = timezone.now().date()
        thirty_days_from_now = today + timedelta(days=30)
        products_to_display = products.filter(
            expiry_date__isnull=False,
            expiry_date__gte=today,
            expiry_date__lte=thirty_days_from_now
        )
        services_to_display = services.none()
        filter_display_name = 'Expiring Soon'
    # Combine the filtered querysets for display
    items = list(products_to_display) + list(services_to_display)
    
    # --- Calculate counts based on the UNFILTERED base querysets ---
    product_count = products.count()
    service_count = services.count()
    today = timezone.now().date()
    thirty_days_from_now = today + timedelta(days=30)
    expiring_count = products.filter(
        expiry_date__isnull=False,
        expiry_date__gte=today,
        expiry_date__lte=thirty_days_from_now
    ).count()
    
    context = {
        'add': account,
        'items': items,
        'product_count': products.count(),
        'service_count': services.count(),
        'expiring_count': expiring_count,
        'tenant': tenant,
        'active_filter': item_filter,
        'filter_display_name': filter_display_name,
    }
    return render(request, 'Item_list.html', context)

# Create Item View
@tenant_required
def create_item_view(request):
    account = get_object_or_404(Account, email=request.session['email'])
    
    # --- POST Request: Handle Form Submission ---
    if request.method == "POST":
        target_tenant = None
        # Determine the correct tenant for the new item
        if account.role == 'superadmin':
            tenant_id = request.POST.get('tenant_id')
            if not tenant_id:
                messages.error(request, "As a superadmin, you must select a tenant.")
                return redirect('Create_item') # Redirect back to the form
            target_tenant = get_object_or_404(Tenant, id=tenant_id)
        else:
            # For regular users, the tenant is assigned from their session by the middleware
            target_tenant = request.tenant

        try:
            item_type = request.POST.get('item_type', '').strip()
            if item_type not in ['product', 'service']:
                raise ValidationError("Invalid item type submitted.")
            
            item_name = request.POST.get('item_name', '').strip()
            if not item_name:
                raise ValidationError("Item name is required.")
            
            # Check for duplicate item name within the target tenant
            if Product.objects.filter(item_name=item_name, tenant=target_tenant).exists() or \
               Service.objects.filter(item_name=item_name, tenant=target_tenant).exists():
                messages.warning(request, f"An item named '{item_name}' already exists for this tenant.")
                return redirect('Create_item')
            
            # Prepare data common to both Products and Services
            common_data = {
                'item_name': item_name,
                'item_type': item_type,
                'description': request.POST.get('item_des', '') or request.POST.get('service_description', ''),
                'category_id': request.POST.get('category', '') or request.POST.get('service_category', ''),
                'gst_rate': request.POST.get('gst', '') or request.POST.get('gst_service', ''),
                'hsn_sac_code': request.POST.get('hsn', '') or request.POST.get('hsn_service', ''),
                'sale_price': request.POST.get('sale_price', '') or request.POST.get('sale_price_service', ''),
                'tenant': target_tenant, # Assign the correct tenant
            }
            
            # Handle image upload
            if 'product_image' in request.FILES:
                common_data['image'] = request.FILES['product_image']
            elif 'service_image' in request.FILES:
                common_data['image'] = request.FILES['service_image']
            
            # Create either a Product or a Service
            if item_type == 'product':
                product_data = {
                    **common_data,
                    'unit_id': request.POST.get('unit') or None,
                    'purchase_price': request.POST.get('purchase_price', 0) or 0,
                    'opening_stock': request.POST.get('opening_stock', 0) or 0,
                    'stock_date': request.POST.get('stock_date') or None,
                    'expiry_date': request.POST.get('expiry_date') or None,
                    'batch_number': request.POST.get('batch_number') or None,
                }
                product = Product(**product_data)
                product.full_clean()
                product.save()
                messages.success(request, "Product created successfully!")
            else: # item_type == 'service'
                service_data = {
                    **common_data,
                    'service_unit': request.POST.get('ltype') or None,
                    'service_start_date': request.POST.get('service_start_date') or None,
                }
                service = Service(**service_data)
                service.full_clean()
                service.save()
                messages.success(request, "Service created successfully!")
            
            # Redirect appropriately
            if account.role == 'superadmin':
                return redirect(f"/Item_list?tenant_id={target_tenant.id}")
            else:
                return redirect('Item_list')
        
        except ValidationError as e:
            # Handle validation errors gracefully
            error_messages = e.message_dict if hasattr(e, 'message_dict') else {'__all__': e.messages}
            for field, errors in error_messages.items():
                for error in errors:
                    messages.error(request, f"{field.replace('_', ' ').title()}: {error}")
        except Exception as e:
            messages.error(request, f"An unexpected error occurred: {str(e)}")
        
        return redirect('Create_item')

    # --- GET Request: Display the Form ---
    context = {'add': account}
    if account.role == 'superadmin':
        context['tenants'] = Tenant.objects.all().order_by('name')
        # Pre-select tenant if coming from a tenant-specific page
        context['tenant_id_from_url'] = request.GET.get('tenant_id')
        # For superadmin, load all units/categories. A better approach for many tenants
        # would be to use JavaScript to load these dynamically based on tenant selection.
        context['unit'] = Unit.objects.all()
        context['category'] = Category.objects.all()
    else:
        # For regular users, only load data for their tenant
        tenant = request.tenant
        context['tenant'] = tenant
        context['unit'] = Unit.objects.filter(tenant=tenant, is_active=True)
        context['category'] = Category.objects.filter(tenant=tenant, is_active=True)

    return render(request, 'Create_item.html', context)

# Update Item View
@tenant_required
def update_item_view(request, item_id):
    account = get_object_or_404(Account, email=request.session['email'])
    
    # Fetch the base item to check its type and for security
    item_base = get_object_or_404(ItemBase, id=item_id)
    
    # Security Check: Ensure user is a superadmin or belongs to the correct tenant
    if account.role != 'superadmin' and item_base.tenant != request.tenant:
        messages.error(request, "You are not authorized to edit this item.")
        return redirect('Item_list')
        
    # Determine if the item is a Product or Service to fetch the specific instance
    if item_base.item_type == 'product':
        item_instance = get_object_or_404(Product, id=item_id)
    else: # 'service'
        item_instance = get_object_or_404(Service, id=item_id)
        
    if request.method == "POST":
        try:
            # For simplicity, we'll update the fields directly.
            # A Django ModelForm would be a more advanced way to handle this.
            
            # Common fields
            item_instance.item_name = request.POST.get('item_name', '').strip()
            item_instance.description = request.POST.get('item_des', '')
            item_instance.category_id = request.POST.get('category')
            item_instance.gst_rate = request.POST.get('gst')
            item_instance.hsn_sac_code = request.POST.get('hsn')
            item_instance.sale_price = request.POST.get('sale_price')
            
            if 'product_image' in request.FILES:
                item_instance.image = request.FILES['product_image']

            # Product-specific fields
            if item_instance.item_type == 'product':
                item_instance.unit_id = request.POST.get('unit')
                item_instance.purchase_price = request.POST.get('purchase_price')
                item_instance.opening_stock = request.POST.get('opening_stock')
                item_instance.stock_date = request.POST.get('stock_date') or None
                item_instance.expiry_date = request.POST.get('expiry_date') or None
                item_instance.batch_number = request.POST.get('batch_number')
            
            # Service-specific fields (if you add them to the form)
            elif item_instance.item_type == 'service':
                item_instance.sale_price = request.POST.get('sale_price')
            
            item_instance.full_clean()
            item_instance.save()
            messages.success(request, f"Item '{item_instance.item_name}' updated successfully.")

            if account.role == 'superadmin':
                return redirect(f"/Item_list?tenant_id={item_instance.tenant.id}")
            else:
                return redirect('Item_list')
        
        except ValidationError as e:
            error_messages = e.message_dict if hasattr(e, 'message_dict') else {'__all__': e.messages}
            for field, errors in error_messages.items():
                for error in errors:
                    messages.error(request, f"{field.replace('_', ' ').title()}: {error}")
        except Exception as e:
            messages.error(request, f"An unexpected error occurred: {str(e)}")
        
        return redirect('update_item', item_id=item_instance.id)

    # For GET request, prepare the context
    context = {
        'add': account,
        'item': item_instance,
    }
    # Load tenant-specific or all Units/Categories for the dropdowns
    if account.role == 'superadmin':
        context['unit'] = Unit.objects.filter(tenant=item_instance.tenant)
        context['category'] = Category.objects.filter(tenant=item_instance.tenant)
    else:
        context['unit'] = Unit.objects.filter(tenant=request.tenant, is_active=True)
        context['category'] = Category.objects.filter(tenant=request.tenant, is_active=True)

    return render(request, 'update_item.html', context)

# Delete Item View 
@tenant_required
def delete_item_view(request, item_id):
    account = get_object_or_404(Account, email=request.session['email'])
    item_to_delete = get_object_or_404(ItemBase, id=item_id)
    
    # Store the tenant ID for the redirect before changing the item
    tenant_id = item_to_delete.tenant.id

    # Security Check: Ensure the user is a superadmin or belongs to the item's tenant
    if account.role != 'superadmin' and item_to_delete.tenant != request.tenant:
        messages.error(request, "You are not authorized to delete this item.")
        return redirect('Item_list')

    try:
        # Perform a "soft delete" by setting the item to inactive
        item_to_delete.is_active = False
        item_to_delete.save()
        messages.success(request, f"Item '{item_to_delete.item_name}' has been successfully deleted.")
    except Exception as e:
        messages.error(request, f"An error occurred while deleting the item: {e}")

    # Redirect back to the item list, maintaining the tenant context for the superadmin
    if account.role == 'superadmin':
        return redirect(f"{reverse('Item_list')}?tenant_id={tenant_id}")
    else:
        return redirect('Item_list')
# Toggle Item Activate/Deactivate
@tenant_required
def toggle_item_status(request, item_id):
    account = get_object_or_404(Account, email=request.session['email'])
    item_to_toggle = get_object_or_404(ItemBase, id=item_id)

    # Security Check
    if account.role != 'superadmin' and item_to_toggle.tenant != request.tenant:
        messages.error(request, "You are not authorized to modify this item.")
        return redirect('Item_list')

    # Flip the boolean status
    item_to_toggle.is_active = not item_to_toggle.is_active
    item_to_toggle.save()

    status = "activated" if item_to_toggle.is_active else "deactivated"
    messages.success(request, f"Item '{item_to_toggle.item_name}' has been {status}.")

    # Redirect back, preserving the tenant context for the superadmin
    if account.role == 'superadmin':
        tenant_id = item_to_toggle.tenant.id
        return redirect(f"{reverse('Item_list')}?tenant_id={tenant_id}")
    else:
        return redirect('Item_list')

# Create Sale View (Detailed)
@tenant_required
def create_sale_view(request):
    account = get_object_or_404(Account, email=request.session['email'])

    # --- POST Request: Handle Form Submission ---
    if request.method == "POST":
        # Check if the request is an AJAX request (used for "Save & Print")
        is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
        
        try:
            with transaction.atomic():
                target_tenant = None
                # Determine the correct tenant for the new sale
                if account.role == 'superadmin':
                    tenant_id = request.POST.get('tenant_id')
                    if not tenant_id:
                        raise ValidationError("As a superadmin, you must select a tenant.")
                    target_tenant = get_object_or_404(Tenant, id=tenant_id)
                else:
                    target_tenant = request.tenant

                post_data = request.POST
                party = get_object_or_404(Create_party, id=post_data.get('party_id'), tenant=target_tenant)
                
                invoice_date_str = post_data.get('invoice_date')
                if not invoice_date_str:
                    raise ValidationError("Invoice Date is required.")
                
                invoice_date_obj = datetime.strptime(invoice_date_str, '%Y-%m-%d').date()
                due_date_str = post_data.get('due_date')
                due_date_obj = datetime.strptime(due_date_str, '%Y-%m-%d').date() if due_date_str else None
                
                items_data = []
                total_item_subtotal = 0
                total_tax = 0
                # Find all unique item indices from the form data
                item_indices = sorted(list(set(re.findall(r'items\[(\d+)\]', ' '.join(post_data.keys())))))
                
                for index in item_indices:
                    item_id = post_data.get(f'items[{index}][item_id]')
                    quantity = int(post_data.get(f'items[{index}][quantity]', 0))
                    if not item_id or quantity <= 0:
                        continue
                    
                    item = get_object_or_404(ItemBase, id=item_id, tenant=target_tenant)
                    
                    unit_price = float(item.sale_price)
                    item_discount = float(post_data.get(f'items[{index}][discount]', 0))
                    item_subtotal = quantity * unit_price
                    taxable_amount_item = item_subtotal - item_discount
                    gst_rate = float(re.sub(r'[^0-9.]', '', item.gst_rate or '0'))
                    tax_amount_item = taxable_amount_item * (gst_rate / 100)
                    total_item_subtotal += item_subtotal
                    total_tax += tax_amount_item
                    
                    # Stock deduction for products
                    if item.item_type == 'product':
                        product = Product.objects.select_for_update().get(id=item.id, tenant=target_tenant)
                        if product.opening_stock < quantity:
                            raise ValidationError(f"Insufficient stock for {item.item_name}. Available: {product.opening_stock}")
                        product.opening_stock -= quantity
                        product.save()
                    
                    items_data.append({
                        'item_instance': item, 'quantity': quantity, 'discount': item_discount,
                        'tax_amount': tax_amount_item, 'amount': taxable_amount_item + tax_amount_item
                    })
                
                if not items_data:
                    raise ValidationError("At least one valid item must be added to the sale.")
                
                discount_overall = float(post_data.get('discount', 0))
                additional_charges = float(post_data.get('additional_charges', 0))
                taxable_amount_total = total_item_subtotal - discount_overall
                total_amount = taxable_amount_total + total_tax + additional_charges
                amount_received = float(post_data.get('amount_received', 0))
                
                sale = Sale.objects.create(
                    tenant=target_tenant,
                    user=account,
                    invoice_no=post_data.get('invoice_no'),
                    party=party,
                    invoice_date=invoice_date_obj,
                    due_date=due_date_obj,
                    subtotal=total_item_subtotal,
                    total_tax=total_tax,
                    discount=discount_overall,
                    additional_charges=additional_charges,
                    additional_charges_note=post_data.get('additional_charges_note', ''),
                    total_amount=total_amount,
                    amount_received=amount_received,
                    balance_amount=total_amount - amount_received,
                    notes=post_data.get('notes', ''),
                    terms_conditions=post_data.get('terms_conditions', ''),
                )
                
                sale_items_for_json = []
                for data in items_data:
                    sale_item = SaleItem.objects.create(sale=sale, item=data['item_instance'], **{k: v for k, v in data.items() if k != 'item_instance'})
                    sale_items_for_json.append({
                        'name': sale_item.item.item_name,
                        'qty': sale_item.quantity,
                        'rate': f'{sale_item.item.sale_price:.2f}',
                        'tax_rate': f'{float(re.sub(r"[^0-9.]", "", sale_item.item.gst_rate or "0")):.0f}%',
                        'amount': f'{sale_item.amount:.2f}'
                    })

            # --- SUCCESS RESPONSE ---
            if is_ajax:
                # Build the data payload for the successful AJAX response
                sale_data = {
                    'invoice_no': sale.invoice_no,
                    'invoice_date': sale.invoice_date.strftime('%d-%m-%Y'),
                    'due_date': sale.due_date.strftime('%d-%m-%Y') if sale.due_date else 'N/A',
                    'party_name': party.party_name,
                    'party_address': party.billing_address,
                    'party_gst': party.gst_no,
                    'subtotal': f'₹ {sale.subtotal:.2f}',
                    'discount': f'(-) {sale.discount:.2f}',
                    'charges_note': sale.additional_charges_note or 'Charges',
                    'additional_charges': f'(+) {sale.additional_charges:.2f}',
                    'total_amount_str': f'₹ {sale.total_amount:.2f}',
                    'total_amount_val': sale.total_amount,
                    'amount_received': f'₹ {sale.amount_received:.2f}',
                    'balance_amount': f'₹ {sale.balance_amount:.2f}',
                    'notes': sale.notes,
                    'terms': sale.terms_conditions,
                    'items': sale_items_for_json,
                    # Add taxable_amount and total_tax for print summary
                    'taxable_amount': f'₹ {taxable_amount_total:.2f}',
                    'total_tax': f'₹ {total_tax:.2f}',
                }
                return JsonResponse({'status': 'success', 'sale_data': sale_data})
            
            messages.success(request, "Sale created successfully!")
            if account.role == 'superadmin':
                return redirect(f"/sales_list?tenant_id={target_tenant.id}")
            else:
                return redirect('sales_list')

        except (ValidationError, Exception) as e:
            # --- THIS IS THE CORRECTED ERROR HANDLING BLOCK ---
            # Extract the main error message, however it's formatted
            error_message = getattr(e, 'message', str(e))
            if hasattr(e, 'message_dict'):
                 error_message = next(iter(e.message_dict.values()))[0]

            if is_ajax:
                # For AJAX requests, ALWAYS return a JSON response, even for errors.
                return JsonResponse({'status': 'error', 'message': error_message}, status=400)
            else:
                # For regular form submissions, use Django messages and redirect.
                messages.error(request, error_message)
                return redirect('Create_Sale')

    # --- GET Request: Display the Form (no changes needed here) ---
    context = {'add': account}
    if account.role == 'superadmin':
        context['tenants'] = Tenant.objects.all().order_by('name')
        context['tenant_id_from_url'] = request.GET.get('tenant_id')
        context['items'] = ItemBase.objects.filter(is_active=True).order_by('item_name')
        context['parties'] = Create_party.objects.filter(is_active=True).order_by('party_name')
    else:
        tenant = request.tenant
        context['tenant'] = tenant
        context['items'] = ItemBase.objects.filter(tenant=tenant, is_active=True).order_by('item_name')
        context['parties'] = Create_party.objects.filter(tenant=tenant, is_active=True).order_by('party_name')
    
    context['invoice_no'] = f"INV-{uuid.uuid4().hex[:8].upper()}"
    return render(request, 'create_sale.html', context)


# Sales List View
@tenant_required
def sales_list(request):
    account = get_object_or_404(Account, email=request.session['email'])
    tenant = None
    sales = Sale.objects.none()
    filter_parties = Create_party.objects.none()

    # 1. Determine the base queryset
    if account.role == 'superadmin':
        tenant_id = request.GET.get('tenant_id')
        if tenant_id:
            try:
                tenant = Tenant.objects.get(id=tenant_id)
                sales = Sale.objects.filter(tenant=tenant).select_related('party').order_by('-invoice_date')
                filter_parties = Create_party.objects.filter(tenant=tenant, is_active=True)
            except Tenant.DoesNotExist:
                pass
    else:
        tenant = request.tenant
        sales = Sale.objects.filter(tenant=tenant).select_related('party').order_by('-invoice_date')
        filter_parties = Create_party.objects.filter(tenant=tenant, is_active=True)

    # 2. Get filter parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    party_id = request.GET.get('party')
    status = request.GET.get('status')

    # 3. Apply filters
    if start_date:
        sales = sales.filter(invoice_date__gte=start_date)
    if end_date:
        sales = sales.filter(invoice_date__lte=end_date)
    if party_id:
        sales = sales.filter(party__id=party_id)
    if status:
        today = timezone.now().date()
        if status == 'PAID':
            sales = sales.filter(balance_amount__lte=0)
        
        # --- THIS IS THE CORRECTED LOGIC ---
        elif status == 'UNPAID':
            sales = sales.filter(
                Q(balance_amount__gt=0) & 
                (Q(due_date__gte=today) | Q(due_date__isnull=True))
            )
        # ------------------------------------

        elif status == 'OVERDUE':
            sales = sales.filter(balance_amount__gt=0, due_date__lt=today)
            
    # Calculate totals AFTER filtering
    totals = sales.aggregate(
        total_sales=Sum('total_amount'),
        total_received=Sum('amount_received'),
        total_balance=Sum('balance_amount')
    )
    
    context = {
        'sales_list': sales,
        'total_sales': totals['total_sales'] or 0,
        'paid_amount': totals['total_received'] or 0,
        'unpaid_amount': totals['total_balance'] or 0,
        'add': account,
        'tenant': tenant,
        'filter_parties': filter_parties,
        'current_filters': {
            'start_date': start_date,
            'end_date': end_date,
            'party': party_id,
            'status': status,
        }
    }
    return render(request, 'sales_list.html', context)

# Edit Sale View
@never_cache
@tenant_required
def edit_sale_view(request, sale_id):
    account = get_object_or_404(Account, email=request.session['email'])
    
    # Get the sale object with proper security check
    if account.role == 'superadmin':
        sale = get_object_or_404(Sale, id=sale_id)
    else:
        sale = get_object_or_404(Sale, id=sale_id, tenant=request.tenant)
    
    # Security check: Ensure user has permission to edit this sale
    if account.role != 'superadmin' and sale.tenant != request.tenant:
        messages.error(request, "You are not authorized to edit this sale.")
        return redirect('sales_list')
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                for item in sale.items.all():
                    if item.item and item.item.item_type == 'product':
                        product = get_object_or_404(Product, id=item.item.id, tenant=sale.tenant)
                        product.opening_stock += item.quantity
                        product.save()
                
                # Delete existing sale items
                sale.items.all().delete()
                
                # Process new items
                post_data = request.POST
                party = get_object_or_404(Create_party, id=post_data.get('party_id'), tenant=sale.tenant)
                invoice_date_obj = datetime.strptime(post_data.get('invoice_date'), '%Y-%m-%d').date()
                due_date_str = post_data.get('due_date')
                due_date_obj = datetime.strptime(due_date_str, '%Y-%m-%d').date() if due_date_str else None
                
                new_sale_items = []
                total_item_subtotal = 0
                total_tax = 0
                item_indices = sorted(list(set(re.findall(r'items\[(\d+)\]', ' '.join(post_data.keys())))))
                
                for index in item_indices:
                    item_id = post_data.get(f'items[{index}][item_id]')
                    quantity = int(post_data.get(f'items[{index}][quantity]', 0))
                    item_discount = float(post_data.get(f'items[{index}][discount]', 0))
                    
                    if not item_id or quantity <= 0:
                        continue
                    
                    item_obj = get_object_or_404(ItemBase, id=item_id, tenant=sale.tenant)
                    unit_price = float(item_obj.sale_price)
                    item_subtotal = quantity * unit_price
                    taxable_item_amount = item_subtotal - item_discount
                    gst_rate = float(re.sub(r'[^0-9.]', '', item_obj.gst_rate or '0'))
                    tax_for_item = taxable_item_amount * (gst_rate / 100)
                    
                    total_item_subtotal += item_subtotal
                    total_tax += tax_for_item
                    
                    # Stock deduction for products
                    if item_obj.item_type == 'product':
                        product = get_object_or_404(Product, id=item_obj.id, tenant=sale.tenant)
                        if product.opening_stock < quantity:
                            raise ValidationError(f"Not enough stock for {item_obj.item_name}. Only {product.opening_stock} available.")
                        product.opening_stock -= quantity
                        product.save()
                    
                    new_sale_items.append(
                        SaleItem(
                            sale=sale,
                            item=item_obj,
                            quantity=quantity,
                            discount=item_discount,
                            tax_amount=tax_for_item,
                            amount=taxable_item_amount + tax_for_item
                        )
                    )
                
                if not new_sale_items:
                    raise ValidationError("A sale must have at least one item.")
                
                overall_discount = float(post_data.get('discount', 0))
                additional_charges = float(post_data.get('additional_charges', 0))
                taxable_amount = total_item_subtotal - overall_discount
                total_amount = taxable_amount + total_tax + additional_charges
                amount_received = float(post_data.get('amount_received', 0))
                
                sale.party = party
                sale.invoice_no = post_data.get('invoice_no')
                sale.invoice_date = invoice_date_obj
                sale.due_date = due_date_obj
                sale.subtotal = total_item_subtotal
                sale.total_tax = total_tax
                sale.discount = overall_discount
                sale.additional_charges = additional_charges
                sale.additional_charges_note = post_data.get('additional_charges_note', '')
                sale.total_amount = total_amount
                sale.amount_received = amount_received
                sale.balance_amount = total_amount - amount_received
                sale.save()
                
                # Create new sale items
                SaleItem.objects.bulk_create(new_sale_items)
                
                messages.success(request, f"Sale {sale.invoice_no} updated successfully!")
                
                # Redirect with tenant_id for superadmin
                if account.role == 'superadmin':
                    return redirect(f"{reverse('sales_list')}?tenant_id={sale.tenant.id}")
                else:
                    return redirect('sales_list')
        
        except (ValidationError, Exception) as e:
            messages.error(request, f"Error updating sale: {e}")
            return redirect('edit_sale', sale_id=sale.id)
    
    context = {
        'sale': sale,
        'all_items': ItemBase.objects.filter(tenant=sale.tenant, is_active=True).order_by('item_name'),
        'all_parties': Create_party.objects.filter(tenant=sale.tenant, is_active=True).order_by('party_name'),
        'add': account,
        'tenant': sale.tenant,
    }
    return render(request, 'edit_sale.html', context)

# Delete Sales View
@tenant_required
def delete_sale(request, sale_id):
    account = get_object_or_404(Account, email=request.session['email'])
    
    # Get the sale with proper security check
    if account.role == 'superadmin':
        sale_to_delete = get_object_or_404(Sale, id=sale_id)
    else:
        sale_to_delete = get_object_or_404(Sale, id=sale_id, tenant=request.tenant)
    
    # Security check: Ensure user has permission to delete this sale
    if account.role != 'superadmin' and sale_to_delete.tenant != request.tenant:
        messages.error(request, "You are not authorized to delete this sale.")
        return redirect('sales_list')

    # Store the tenant ID before deleting the sale
    tenant_id = sale_to_delete.tenant.id

    try:
        with transaction.atomic():
            # Restore stock for all items
            for item in sale_to_delete.items.all():
                if item.item and item.item.item_type == 'product':
                    product = get_object_or_404(Product, id=item.item.id, tenant=sale_to_delete.tenant)
                    product.opening_stock += item.quantity
                    product.save()
            
            invoice_no = sale_to_delete.invoice_no
            sale_to_delete.delete()
            messages.success(request, f"Invoice {invoice_no} has been deleted successfully.")
    
    except Exception as e:
        messages.error(request, f"An error occurred while deleting the sale: {e}")

    # Redirect correctly based on the user's role
    if account.role == 'superadmin':
        return redirect(f"{reverse('sales_list')}?tenant_id={tenant_id}")
    else:
        return redirect('sales_list')

# --- VIEW to Get tenant data for sale ---
def get_tenant_data_for_sale_form(request, tenant_id):
    # Ensure only authenticated superadmins can access this
    account = Account.objects.filter(email=request.session.get('email')).first()
    if not account or account.role != 'superadmin':
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    # Fetch parties and items for the requested tenant
    parties = Create_party.objects.filter(tenant_id=tenant_id, is_active=True).values('id', 'party_name')
    items = ItemBase.objects.filter(tenant_id=tenant_id, is_active=True).values('id', 'item_name', 'sale_price', 'gst_rate')

    data = {
        'parties': list(parties),
        'items': list(items),
    }
    return JsonResponse(data)
# Sale Detail View
@tenant_required
def sale_detail_view(request, sale_id):
    account = get_object_or_404(Account, email=request.session['email'])
    sale = get_object_or_404(Sale.objects.prefetch_related('items', 'items__item', 'payments'), id=sale_id)

    # Security check: Ensure the user has permission to view this sale
    if account.role != 'superadmin' and sale.tenant != request.tenant:
        messages.error(request, "You are not authorized to view this sale.")
        return redirect('sales_list')

    context = {
        'add': account,
        'sale': sale,
        'tenant': sale.tenant,
    }
    return render(request, 'sale_detail.html', context)

# Reacord Payment
@tenant_required
def record_payment(request, sale_id):
    sale = get_object_or_404(Sale, id=sale_id)
    account = get_object_or_404(Account, email=request.session['email'])

    # Security check
    if account.role != 'superadmin' and sale.tenant != request.tenant:
        messages.error(request, "You are not authorized to modify this sale.")
        return redirect('sales_list')

    if request.method == 'POST':
        try:
            amount_str = request.POST.get('amount')
            if not amount_str:
                raise ValueError("Amount is required.")
                
            amount = Decimal(amount_str)
            
            if amount <= 0:
                raise ValueError("Payment amount must be positive.")
            if amount > sale.balance_amount:
                raise ValueError("Payment cannot be greater than the balance due.")

            # Use a database transaction to ensure data integrity
            with transaction.atomic():
                # 1. Update the Sale object
                sale.amount_received += amount
                sale.balance_amount -= amount
                sale.save()

                # 2. Create the Payment record
                Payment.objects.create(
                    sale=sale,
                    payment_date=request.POST.get('payment_date'),
                    amount=amount,
                    payment_mode=request.POST.get('payment_mode'),
                    notes=request.POST.get('notes', ''),
                    user=account
                )
            
            messages.success(request, f"Payment of ₹{amount} recorded successfully.")

        except (ValueError, Exception) as e:
            messages.error(request, f"Error recording payment: {e}")

    return redirect('sale_detail', sale_id=sale.id)


# Sale Invoice Pdf
@tenant_required
def sale_invoice_pdf(request, sale_id):
    account = get_object_or_404(Account, email=request.session['email'])
    sale = get_object_or_404(Sale, id=sale_id)

    # Security check
    if account.role != 'superadmin' and sale.tenant != request.tenant:
        messages.error(request, "You are not authorized to view this invoice.")
        return redirect('sales_list')

    context = {
        'sale': sale,
    }
    return render(request, 'sale_invoice_pdf.html', context)


# Superadmin Dashboard
@superadmin_required
def superadmin_dashboard(request):
    # Fetch the first account's details for display purposes
    first_account = Account.objects.filter(tenant=OuterRef('pk')).order_by('created_at')

    # Use prefetch_related to efficiently load all accounts for each tenant.
    # This avoids N+1 queries when accessing tenant.accounts in the template/modal.
    tenants = Tenant.objects.prefetch_related('accounts').annotate(
        admin_name=Subquery(first_account.values('full_name')[:1]),
        admin_email=Subquery(first_account.values('email')[:1]),
        admin_phone=Subquery(first_account.values('phone')[:1]),
        admin_role=Subquery(first_account.values('role')[:1]),
    ).order_by('-created_at')
    
    account = Account.objects.filter(email=request.session.get('email')).first()
    total_accounts = Account.objects.count()
    total_parties = Create_party.objects.count()
    total_items = ItemBase.objects.count()
    total_sales = Sale.objects.count()
    total_revenue = Sale.objects.aggregate(total=Sum('total_amount'))['total'] or 0.00

    # Fetch the 10 most recent logs of ANY type
    activity_logs = ActivityLog.objects.select_related('actor', 'tenant').order_by('-timestamp')[:10]
    
    # Fetch the 10 most recent FINANCIAL logs specifically
    financial_logs = ActivityLog.objects.filter(
        category=ActivityLog.LogCategories.FINANCIAL
    ).select_related('actor', 'tenant').order_by('-timestamp')[:10]

    context = {
        'add': account,
        'tenants': tenants,
        'total_accounts': total_accounts,
        'total_parties': total_parties,
        'total_items': total_items,
        'total_sales': total_sales,
        'total_revenue': total_revenue,
        'activity_logs': activity_logs,
        'financial_logs': financial_logs,
    }
    return render(request, 'superadmin_dashboard.html', context)

# Create Tenant
@superadmin_required
def create_tenant(request):
    if request.method == "POST":
        company_name = request.POST.get('company_name')
        subdomain = request.POST.get('subdomain')
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        phone = request.POST.get('phone')
        role = request.POST.get('role')

        if not all([company_name, subdomain, full_name, email, password, role]):
            messages.error(request, "Please fill all required fields.")
            return redirect('superadmin_dashboard')

        try:
            # Using transaction.atomic would be even better here for production
            tenant = Tenant.objects.create(name=company_name, subdomain=subdomain)
            
            # The Account model's save() method handles password hashing,
            # so we pass the raw password directly.
            Account.objects.create(
                tenant=tenant,
                full_name=full_name,
                email=email,
                password=password, # Corrected: Pass the password from the form
                phone=phone,
                role=role,
                is_active=True
            )
            messages.success(request, f"Tenant '{company_name}' and Admin '{full_name}' created successfully!")
        
        except Exception as e:
            messages.error(request, f"Error creating tenant: {str(e)}")
            
        return redirect('superadmin_dashboard')
    return redirect('superadmin_dashboard')

# --- NEW VIEWS FOR ACCOUNT MANAGEMENT ---
# Add Account
@superadmin_required
def add_account(request, tenant_id):
    if request.method == 'POST':
        tenant = get_object_or_404(Tenant, id=tenant_id)
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role')

        if not all([full_name, email, password, role]):
            messages.error(request, "Please fill all fields to add a new account.")
            return redirect('superadmin_dashboard')

        if Account.objects.filter(email=email).exists():
            messages.error(request, f"An account with the email '{email}' already exists.")
            return redirect('superadmin_dashboard')
        
        try:
            Account.objects.create(
                tenant=tenant,
                full_name=full_name,
                email=email,
                password=password, # Model's save() will hash it
                role=role,
                is_active=True
            )
            messages.success(request, f"Account '{full_name}' created for tenant '{tenant.name}'.")
        except Exception as e:
            messages.error(request, f"Failed to create account. Error: {e}")

    return redirect('superadmin_dashboard')
# Delete Account
@superadmin_required
def delete_account(request, account_id):
    account = get_object_or_404(Account, id=account_id)
    
    # Optional: Add a check to prevent deleting the last admin of a tenant
    tenant = account.tenant
    if account.role == 'admin' and tenant.accounts.filter(role='admin').count() == 1:
        messages.error(request, f"Cannot delete the last admin account for tenant '{tenant.name}'.")
        return redirect('superadmin_dashboard')
        
    try:
        account_name = account.full_name
        account.delete()
        messages.success(request, f"Account '{account_name}' has been deleted successfully.")
    except Exception as e:
        messages.error(request, f"Failed to delete account. Error: {e}")
        
    return redirect('superadmin_dashboard')
# Edit Tenant
@superadmin_required
def edit_tenant(request, tenant_id):
    tenant = get_object_or_404(Tenant, id=tenant_id)
    if request.method == 'POST':
        # Get data from the form
        name = request.POST.get('company_name')
        subdomain = request.POST.get('subdomain')
        # The value from the form for 'is_active' will be "True" or "False" as a string
        is_active = request.POST.get('is_active') == 'True'

        tenant.name = name
        tenant.subdomain = subdomain
        tenant.is_active = is_active
        
        try:
            tenant.save()
            messages.success(request, f"Tenant '{tenant.name}' has been updated successfully.")
            return redirect('superadmin_dashboard')
        except IntegrityError:
            messages.error(request, f"The subdomain '{subdomain}' is already in use. Please choose another.")
            # Stay on the edit page so the user can correct the error
    
    context = {'tenant': tenant}
    return render(request, 'edit_tenant.html', context)
# Edit Account
@superadmin_required
def edit_account(request, account_id):
    account = get_object_or_404(Account, id=account_id)
    if request.method == 'POST':
        account.full_name = request.POST.get('full_name')
        account.role = request.POST.get('role')
        account.phone = request.POST.get('phone', '')
        account.is_active = request.POST.get('is_active') == 'True'
        
        # --- Securely handle password change ---
        # Only change the password if a new one is provided.
        new_password = request.POST.get('password')
        if new_password:
            # The model's save() method will hash it
            account.password = new_password

        try:
            # Prevent changing the email to one that already exists
            new_email = request.POST.get('email')
            if account.email != new_email:
                if Account.objects.filter(email=new_email).exists():
                     raise IntegrityError
                account.email = new_email
            
            account.save()
            messages.success(request, f"Account '{account.full_name}' updated successfully.")
            return redirect('superadmin_dashboard')

        except IntegrityError:
            messages.error(request, f"The email '{new_email}' is already in use by another account.")

    context = {'account': account}
    return render(request, 'edit_account.html', context)








# Delete Tenant
@superadmin_required
def delete_tenant(request, tenant_id):
    tenant = get_object_or_404(Tenant, id=tenant_id)
    tenant_name = tenant.name
    tenant.delete()
    messages.success(request, f"Tenant '{tenant_name}' deleted successfully!")
    return redirect('superadmin_dashboard')

# Manage Accounts
@superadmin_required
def manage_accounts(request, tenant_id):
    tenant = get_object_or_404(Tenant, id=tenant_id)
    accounts = Account.objects.filter(tenant=tenant)
    if request.method == "POST":
        action = request.POST.get('action')
        if action == 'create':
            email = request.POST.get('email')
            password = request.POST.get('password')
            role = request.POST.get('role')
            try:
                Account.objects.create(
                    email=email,
                    password=make_password(password),
                    role=role,
                    tenant=tenant,
                    is_active=True
                )
                messages.success(request, f"Account '{email}' created successfully!")
            except Exception as e:
                messages.error(request, f"Error creating account: {str(e)}")
        elif action == 'edit':
            account_id = request.POST.get('account_id')
            account = get_object_or_404(Account, id=account_id, tenant=tenant)
            email = request.POST.get('email')
            password = request.POST.get('password')
            role = request.POST.get('role')
            is_active = request.POST.get('is_active') == 'on'
            try:
                account.email = email
                if password:
                    account.password = make_password(password)
                account.role = role
                account.is_active = is_active
                account.save()
                messages.success(request, f"Account '{email}' updated successfully!")
            except Exception as e:
                messages.error(request, f"Error updating account: {str(e)}")
        elif action == 'delete':
            account_id = request.POST.get('account_id')
            account = get_object_or_404(Account, id=account_id, tenant=tenant)
            email = account.email
            account.delete()
            messages.success(request, f"Account '{email}' deleted successfully!")
        return redirect('manage_accounts', tenant_id=tenant_id)
    
    context = {
        'add': Account.objects.filter(email=request.session['email']).first(),
        'tenant': tenant,
        'accounts': accounts,
        'roles': Account.ROLES,
    }
    return render(request, 'manage_accounts.html', context)

# Activity Logs View
@superadmin_required
def all_activity_logs_view(request,):
    logs = ActivityLog.objects.select_related('actor', 'tenant').all()
    context = {
        'add': Account.objects.get(email=request.session['email']),
        'logs': logs,
        'log_title': 'All Activities'
    }
    return render(request, 'activity_log_list.html', context)

# Records Finaincial Logs
@superadmin_required
def financial_logs_view(request):
    logs = ActivityLog.objects.filter(
        category=ActivityLog.LogCategories.FINANCIAL
    ).select_related('actor', 'tenant')
    context = {
        'add': Account.objects.get(email=request.session['email']),
        'logs': logs,
        'log_title': 'Financial & Transaction Logs'
    }
    return render(request, 'activity_log_list.html', context)

# Tenanat Status (Activated/Deactivated)
@superadmin_required
def toggle_tenant_status(request, tenant_id):
    tenant = get_object_or_404(Tenant, id=tenant_id)
    # Flip the boolean status
    tenant.is_active = not tenant.is_active
    tenant.save()
    
    status = "activated" if tenant.is_active else "deactivated"
    messages.success(request, f"Tenant '{tenant.name}' has been successfully {status}.")
    return redirect('superadmin_dashboard')

# Create API Endpoints for Chart Data
@superadmin_required
def superadmin_analytics_api(request):
    """
    Provides richer, timezone-aware data for the superadmin analytics dashboard.
    """
    now = timezone.now() # Use Django's timezone.now() to fix the warning

    # 1. Tenant Signup Trend (last 6 months)
    six_months_ago = now - relativedelta(months=5)
    six_months_ago = six_months_ago.replace(day=1)

    tenant_signups = Tenant.objects.filter(created_at__gte=six_months_ago) \
        .annotate(month=TruncMonth('created_at')) \
        .values('month') \
        .annotate(count=Count('id')) \
        .order_by('month')

    # Format data to ensure all 6 months are present, even with zero signups
    signup_counts = {s['month'].strftime('%b %Y'): s['count'] for s in tenant_signups}
    signup_labels = []
    signup_data = []
    for i in range(6):
        current_month = (six_months_ago + relativedelta(months=i))
        month_key = current_month.strftime('%b %Y')
        signup_labels.append(month_key)
        signup_data.append(signup_counts.get(month_key, 0))

    # 2. Top 5 Tenants by Sales Volume (No change needed here, it's a good metric)
    top_tenants = Tenant.objects.annotate(total_sales_volume=Sum('sales__total_amount')) \
        .order_by('-total_sales_volume') \
        .filter(total_sales_volume__gt=0)[:5]

    top_tenants_labels = [t.name for t in top_tenants]
    top_tenants_data = [t.total_sales_volume for t in top_tenants]
    
    # 3. NEW: Tenant Status Distribution (Active vs. Inactive)
    status_distribution = Tenant.objects.values('is_active').annotate(count=Count('id')).order_by('is_active')
    
    status_labels = []
    status_data = []
    for status in status_distribution:
        status_labels.append("Active" if status['is_active'] else "Inactive")
        status_data.append(status['count'])

    data = {
        'tenant_signups': { 'labels': signup_labels, 'data': signup_data },
        'top_tenants': { 'labels': top_tenants_labels, 'data': top_tenants_data },
        'status_distribution': { 'labels': status_labels, 'data': status_data },
    }
    
    return JsonResponse(data)

# Implement Impersonation Mode view 
@superadmin_required
def impersonate_start(request, account_id):
    # 1. Get the superadmin's ID before doing anything else.
    superadmin_account = request.user
    superadmin_id = superadmin_account.id # Store the ID in a variable
    
    # 2. Store the superadmin's ID in the session. This is the "return ticket".
    request.session['impersonator_id'] = superadmin_account.id

    # 3. Find the user account to be impersonated.
    target_account = get_object_or_404(Account, id=account_id)

    # 4. Security check: Prevent a superadmin from impersonating another superadmin.
    if target_account.role == 'superadmin':
        messages.error(request, "Superadmins cannot impersonate other superadmins.")
        return redirect('superadmin_dashboard')

    # 5. Log this important security event.
    ActivityLog.objects.create(
        actor=superadmin_account,
        action_type=ActivityLog.ActionTypes.IMPERSONATE_START,
        details=f"Started impersonating user '{target_account.email}'.",
        tenant=target_account.tenant,
        category=ActivityLog.LogCategories.AUTH
    )
    
    # 6. Log the superadmin out and log the target user in.
    logout(request)
    # Log the target user in using Django's function.
    # 7. Log the target user in. This creates a NEW, clean session.
    login(request, target_account, backend='backend.auth_backend.AccountBackend')

    # 8. NOW, add all necessary keys to the NEW session.
    request.session['impersonator_id'] = superadmin_id # Use the ID we saved earlier
    request.session['email'] = target_account.email
    if target_account.tenant:
        request.session['tenant_id'] = target_account.tenant.id
    
    messages.info(request, f"You are now impersonating {target_account.full_name or target_account.email}.")
    return redirect('dash') # Redirect to the standard user dashboard


def impersonate_stop(request):
    impersonator_id = request.session.get('impersonator_id')

    if not impersonator_id:
        return redirect('/') # Should not happen if accessed via the banner

    impersonated_user = request.user
    superadmin_account = get_object_or_404(Account, id=impersonator_id)
    
    # Log the end of the impersonation.
    ActivityLog.objects.create(
        actor=superadmin_account,
        action_type=ActivityLog.ActionTypes.IMPERSONATE_STOP,
        details=f"Stopped impersonating user '{impersonated_user.email}'.",
        tenant=impersonated_user.tenant,
        category=ActivityLog.LogCategories.AUTH
    )

    # Log the impersonated user out and the superadmin back in.
    logout(request)
    # Specify the backend when logging the superadmin back in.
    login(request, superadmin_account, backend='backend.auth_backend.AccountBackend')
    
    # The session is renewed on login, but we'll remove the key just in case.
    if 'impersonator_id' in request.session:
        del request.session['impersonator_id']

    messages.success(request, "You have returned to your superadmin account. Please log in again.")
    # Instead of redirecting to the dashboard, redirect to the login page.
    return redirect('/')

# Profile View
@tenant_required # Use your existing decorator to ensure user is logged in
def profile_view(request):
    # The logged-in user is already on the request object from your middleware
    account = request.user

    # Fetch the 10 most recent activities performed by this specific user
    user_activity_logs = ActivityLog.objects.filter(actor=account).order_by('-timestamp')[:10]

    context = {
        'add': account, # For your sidebar/navbar
        'profile_user': account,
        'activity_logs': user_activity_logs,
    }
    return render(request, 'profile.html', context)

@tenant_required
def edit_profile_view(request):
    # Get the currently logged-in user
    account_to_edit = request.user

    if request.method == 'POST':
        # Get the submitted data from the form
        full_name = request.POST.get('full_name')
        phone = request.POST.get('phone')

        # Update the account object
        account_to_edit.full_name = full_name
        account_to_edit.phone = phone
        account_to_edit.save()

        messages.success(request, 'Your profile has been updated successfully.')
        return redirect('profile') # Redirect back to the main profile page

    context = {
        'add': account_to_edit,
        'profile_user': account_to_edit,
    }
    return render(request, 'edit_profile.html', context)

# Create Purchase
@tenant_required
def create_purchase_view(request):
    account = request.user
    context = {'add': account}

    # --- Logic for displaying the form (GET request) ---
    if account.role == 'superadmin':
        # For superadmin, let's start with a clear slate. We'll load vendors with JavaScript.
        context['tenants'] = Tenant.objects.all().order_by('name')
        context['tenant_id_from_url'] = request.GET.get('tenant_id')
        # Initialize empty for superadmin (will be loaded via AJAX)
        context['vendors'] = []
        context['items'] = []
    else:
        # For regular users, filter parties that are 'Supplier' or 'Both'
        tenant = request.tenant
        context['tenant'] = tenant
        context['vendors'] = Create_party.objects.filter(
            tenant=tenant, 
            is_active=True,
            party_type__in=['Supplier', 'Both']
        ).order_by('party_name')
        context['items'] = Product.objects.filter(tenant=tenant, is_active=True).values('id', 'item_name', 'purchase_price').order_by('item_name')
    
    # Add the available purchase statuses to the context for the dropdown
    context['purchase_statuses'] = Purchase.PurchaseStatus.choices
    # --- Auto-generate a bill number ---
    context['bill_number'] = f"PUR-{uuid.uuid4().hex[:8].upper()}"

    # --- Logic for saving the form (POST request) ---
    if request.method == 'POST':
        try:
            with transaction.atomic():
                target_tenant = None
                if account.role == 'superadmin':
                    tenant_id = request.POST.get('tenant_id')
                    if not tenant_id:
                        raise ValidationError("Superadmin must select a tenant.")
                    target_tenant = get_object_or_404(Tenant, id=tenant_id)
                else:
                    target_tenant = request.tenant

                post_data = request.POST
                vendor = get_object_or_404(Create_party, id=post_data.get('vendor_id'), tenant=target_tenant)
                
                # Get the selected status from the form
                purchase_status = post_data.get('status', Purchase.PurchaseStatus.ORDERED)

                # Create the main Purchase object
                purchase = Purchase.objects.create(
                    tenant=target_tenant,
                    user=account,
                    vendor=vendor,
                    bill_number=post_data.get('bill_number'),
                    purchase_date=post_data.get('purchase_date'),
                    notes=post_data.get('notes'),
                    status=purchase_status # Save the selected status
                )

                total_amount = 0
                item_indices = sorted(list(set(re.findall(r'items\[(\d+)\]', ' '.join(post_data.keys())))))

                for index in item_indices:
                    item_id = post_data.get(f'items[{index}][item_id]')
                    quantity = int(post_data.get(f'items[{index}][quantity]', 0))
                    price = Decimal(post_data.get(f'items[{index}][price]', 0))
                    
                    if not all([item_id, quantity > 0, price > 0]):
                        continue
                    
                    product = get_object_or_404(Product, id=item_id, tenant=target_tenant)
                    
                    # Create the individual PurchaseItem
                    PurchaseItem.objects.create(
                        purchase=purchase,
                        item=product,
                        quantity=quantity,
                        purchase_price=price,
                        amount=quantity * price
                    )

                    # --- CRITICAL LOGIC: Only update stock if purchase is 'Received' ---
                    if purchase_status == Purchase.PurchaseStatus.RECEIVED:
                        product.opening_stock += quantity
                        product.save()

                    total_amount += (quantity * price)
                
                if total_amount == 0:
                    raise ValidationError("Cannot create a purchase with no valid items.")
                
                # Update the total amount on the main Purchase object
                purchase.total_amount = total_amount
                purchase.save()

                messages.success(request, "Purchase recorded successfully!")
                # --- THIS IS THE CORRECTED REDIRECT LOGIC ---
                if account.role == 'superadmin':
                    return redirect(f"{reverse('purchase_list')}?tenant_id={target_tenant.id}")
                else:
                    return redirect('purchase_list')

        except (ValidationError, Exception) as e:
            messages.error(request, f"Error: {e}")
            return redirect('create_purchase')

    return render(request, 'create_purchase.html', context)
    
# API View - return a JSON list of vendors and products for the selected tenant
def get_purchase_data_for_form(request, tenant_id):
    # Security check to ensure only a superadmin can access this
    if not (request.user.is_authenticated and request.user.role == 'superadmin'):
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    # Fetch vendors (parties marked as 'Supplier' or 'Both') for the tenant
    vendors = Create_party.objects.filter(
        tenant_id=tenant_id, 
        is_active=True,
        party_type__in=['Supplier', 'Both']
    ).values('id', 'party_name')

    # Fetch only Products (since you can't "purchase" a service)
    items = Product.objects.filter(
        tenant_id=tenant_id, 
        is_active=True
    ).values('id', 'item_name', 'purchase_price')

    data = {
        'vendors': list(vendors),
        'items': list(items),
    }
    return JsonResponse(data)

# Purchase List View 
@tenant_required
def purchase_list_view(request):
    account = request.user
    purchases = Purchase.objects.none()
    tenant = None
    filter_vendors = Create_party.objects.none()

    # 1. Determine the base queryset and available filters
    if account.role == 'superadmin':
        tenant_id = request.GET.get('tenant_id')
        if tenant_id:
            tenant = get_object_or_404(Tenant, id=tenant_id)
            purchases = Purchase.objects.filter(tenant=tenant).select_related('vendor').order_by('-purchase_date')
            # Get vendors only for the selected tenant
            filter_vendors = Create_party.objects.filter(
                tenant=tenant, is_active=True, party_type__in=['Supplier', 'Both']
            ).order_by('party_name')
    else:
        tenant = request.tenant
        purchases = Purchase.objects.filter(tenant=tenant).select_related('vendor').order_by('-purchase_date')
        # Get vendors for the current user's tenant
        filter_vendors = Create_party.objects.filter(
            tenant=tenant, is_active=True, party_type__in=['Supplier', 'Both']
        ).order_by('party_name')

    # 2. Get filter parameters from the request
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    vendor_id = request.GET.get('vendor')
    status = request.GET.get('status')

    # 3. Apply filters to the queryset
    if start_date:
        purchases = purchases.filter(purchase_date__gte=start_date)
    if end_date:
        purchases = purchases.filter(purchase_date__lte=end_date)
    if vendor_id:
        purchases = purchases.filter(vendor__id=vendor_id)
    if status:
        purchases = purchases.filter(status=status)
    
    context = {
        'add': account,
        'tenant': tenant,
        'purchases': purchases,
        'filter_vendors': filter_vendors, # For the vendor dropdown
        'purchase_statuses': Purchase.PurchaseStatus.choices, # For the status dropdown
        'current_filters': { # To keep filter values in the form
            'start_date': start_date,
            'end_date': end_date,
            'vendor': vendor_id,
            'status': status,
        }
    }
    return render(request, 'purchase_list.html', context)
# View Purchase details individually 
@tenant_required
def view_purchase(request, purchase_id):
    account = request.user
    tenant = get_tenant(request) if not account.role == 'superadmin' else None
    
    if account.role == 'superadmin':
        purchase = get_object_or_404(Purchase, id=purchase_id)
        # Re-assign tenant from the purchase object for consistency
        tenant = purchase.tenant
    else:
        purchase = get_object_or_404(Purchase, id=purchase_id, tenant=tenant)
    
    # --- NEW LOGIC TO PRE-FILTER STATUSES ---
    # Create a list of the next statuses that are manually allowed
    allowed_next_statuses = []
    for value, label in purchase.PurchaseStatus.choices:
        if purchase.can_change_status(value):
            allowed_next_statuses.append((value, label))
    # --- END OF NEW LOGIC ---

    context = {
        'purchase': purchase,
        'add': account,
        'tenant': tenant,
        'allowed_next_statuses': allowed_next_statuses, # Pass the filtered list to the template
    }
    return render(request, 'view_purchase.html', context)

# Edit Purchase 
@tenant_required
def edit_purchase_view(request, purchase_id):
    account = request.user
    tenant = get_tenant(request) if not account.role == 'superadmin' else None
    
    if account.role == 'superadmin':
        purchase = get_object_or_404(Purchase, id=purchase_id)
    else:
        purchase = get_object_or_404(Purchase, id=purchase_id, tenant=tenant)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Handle purchase editing logic here
                post_data = request.POST
                vendor = get_object_or_404(Create_party, id=post_data.get('vendor_id'), tenant=purchase.tenant)
                purchase_status = post_data.get('status', Purchase.PurchaseStatus.ORDERED)
                
                # Update purchase details
                purchase.vendor = vendor
                purchase.bill_number = post_data.get('bill_number')
                purchase.purchase_date = post_data.get('purchase_date')
                purchase.notes = post_data.get('notes')
                purchase.status = purchase_status
                purchase.save()
                
                messages.success(request, f"Purchase {purchase.bill_number} updated successfully!")
                
                # Redirect with tenant context for superadmin
                if account.role == 'superadmin':
                    return redirect(f"{reverse('purchase_list')}?tenant_id={purchase.tenant.id}")
                else:
                    return redirect('purchase_list')
                    
        except Exception as e:
            messages.error(request, f"Error updating purchase: {e}")
    
    context = {
        'purchase': purchase,
        'add': account,
        'tenant': tenant,
        'vendors': Create_party.objects.filter(tenant=purchase.tenant, is_active=True, party_type__in=['Supplier', 'Both']),
        'purchase_statuses': Purchase.PurchaseStatus.choices,
    }
    return render(request, 'edit_purchase.html', context)
# Delete Purchse 
@tenant_required
def delete_purchase(request, purchase_id):
    account = request.user
    tenant = get_tenant(request) if not account.role == 'superadmin' else None
    
    if account.role == 'superadmin':
        purchase = get_object_or_404(Purchase, id=purchase_id)
    else:
        purchase = get_object_or_404(Purchase, id=purchase_id, tenant=tenant)
    
    # Store tenant ID before deletion for redirect
    tenant_id = purchase.tenant.id
    
    try:
        # Handle stock reversal if purchase was received
        if purchase.status == Purchase.PurchaseStatus.RECEIVED:
            for item in purchase.items.all():
                if hasattr(item.item, 'opening_stock'):
                    item.item.opening_stock -= item.quantity
                    item.item.save()
        
        purchase.delete()
        messages.success(request, f"Purchase {purchase.bill_number} deleted successfully!")
    
    except Exception as e:
        messages.error(request, f"Error deleting purchase: {e}")
    
    # Redirect with tenant context for superadmin
    if account.role == 'superadmin':
        return redirect(f"{reverse('purchase_list')}?tenant_id={tenant_id}")
    else:
        return redirect('purchase_list')

# Purchase pdf view
@tenant_required
def purchase_pdf(request, purchase_id):
    account = request.user
    tenant = get_tenant(request) if not account.role == 'superadmin' else None
    
    if account.role == 'superadmin':
        purchase = get_object_or_404(Purchase, id=purchase_id)
    else:
        purchase = get_object_or_404(Purchase, id=purchase_id, tenant=tenant)
    
    template_path = 'purchase_pdf.html'
    context = {'purchase': purchase}
    
    # Create a Django response object, and specify content_type as pdf
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="purchase_{purchase.bill_number}.pdf"'
    
    # Find the template and render it
    template = get_template(template_path)
    html = template.render(context)
    
    # Create PDF
    pisa_status = pisa.CreatePDF(html, dest=response)
    
    # If error then show some view
    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    
    return response

# Purchase Status Updated View 
@tenant_required
def update_purchase_status(request, purchase_id):
    account = request.user
    tenant = get_tenant(request) if not account.role == 'superadmin' else None
    
    if account.role == 'superadmin':
        purchase = get_object_or_404(Purchase, id=purchase_id)
    else:
        purchase = get_object_or_404(Purchase, id=purchase_id, tenant=tenant)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        old_status = purchase.status
        
        if not purchase.can_change_status(new_status):
            messages.error(request, f"Cannot change status from {purchase.get_status_display()} to {dict(Purchase.PurchaseStatus.choices).get(new_status, new_status)}")
        else:
            try:
                with transaction.atomic():
                    # Handle stock changes
                    purchase.update_stock_on_status_change(old_status, new_status)
                    
                    # Update status
                    purchase.status = new_status
                    purchase.save()
                    
                    # Create status history record
                    PurchaseStatusHistory.objects.create(
                        purchase=purchase,
                        old_status=old_status,
                        new_status=new_status,
                        changed_by=account,
                        notes=request.POST.get('notes', '')
                    )
                    
                    messages.success(request, f"Purchase status updated to {purchase.get_status_display()}")
                    
            except Exception as e:
                messages.error(request, f"Error updating status: {e}")
        
        # Redirect back to view page
        if account.role == 'superadmin':
            return redirect(f"{reverse('view_purchase', args=[purchase.id])}?tenant_id={purchase.tenant.id}")
        else:
            return redirect('view_purchase', purchase_id=purchase.id)
    
    return redirect('view_purchase', purchase_id=purchase.id)

@tenant_required
def add_purchase_payment(request, purchase_id):
    account = request.user
    tenant = get_tenant(request) if not account.role == 'superadmin' else None
    
    if account.role == 'superadmin':
        purchase = get_object_or_404(Purchase, id=purchase_id)
    else:
        purchase = get_object_or_404(Purchase, id=purchase_id, tenant=tenant)
    
    if request.method == 'POST':
        try:
            amount = Decimal(request.POST.get('amount'))
            payment_date = request.POST.get('payment_date')
            payment_method = request.POST.get('payment_method')
            reference_number = request.POST.get('reference_number')
            notes = request.POST.get('notes')
            
            if amount <= 0:
                messages.error(request, "Payment amount must be greater than zero")
            elif amount > purchase.balance_due:
                messages.error(request, f"Payment amount cannot exceed balance due of ₹{purchase.balance_due}")
            else:
                PurchasePayment.objects.create(
                    purchase=purchase,
                    amount=amount,
                    payment_date=payment_date,
                    payment_method=payment_method,
                    reference_number=reference_number,
                    notes=notes,
                    created_by=account
                )
                messages.success(request, f"Payment of ₹{amount} recorded successfully")
                
        except Exception as e:
            messages.error(request, f"Error recording payment: {e}")
    
    if account.role == 'superadmin':
        return redirect(f"{reverse('view_purchase', args=[purchase.id])}?tenant_id={purchase.tenant.id}")
    else:
        return redirect('view_purchase', purchase_id=purchase.id)

@tenant_required
def delete_purchase_payment(request, payment_id):
    account = request.user
    
    if account.role == 'superadmin':
        payment = get_object_or_404(PurchasePayment, id=payment_id)
    else:
        payment = get_object_or_404(PurchasePayment, id=payment_id, purchase__tenant=request.tenant)
    
    purchase_id = payment.purchase.id
    tenant_id = payment.purchase.tenant.id
    
    try:
        payment.delete()
        messages.success(request, "Payment record deleted successfully")
    except Exception as e:
        messages.error(request, f"Error deleting payment: {e}")
    
    if account.role == 'superadmin':
        return redirect(f"{reverse('view_purchase', args=[purchase_id])}?tenant_id={tenant_id}")
    else:
        return redirect('view_purchase', purchase_id=purchase_id)

# Create Purchase Return View 
@tenant_required
def create_purchase_return(request, purchase_id):
    account = request.user
    # Use prefetch_related for efficiency
    purchase_qs = Purchase.objects.prefetch_related('items__item')
    
    if account.role == 'superadmin':
        # tenant is not needed here since purchase_id is unique
        purchase = get_object_or_404(purchase_qs, id=purchase_id)
        tenant = purchase.tenant
    else:
        tenant = request.tenant
        purchase = get_object_or_404(purchase_qs, id=purchase_id, tenant=tenant)
    
    if purchase.status not in ['RECEIVED', 'PARTIALLY_RECEIVED']:
        messages.error(request, 'Only items from fully or partially received purchases can be returned.')
        return redirect('view_purchase', purchase_id=purchase.id)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                return_reason = request.POST.get('return_reason')
                notes = request.POST.get('notes', '')
                
                # Validation: Ensure a reason is selected
                if not return_reason:
                    raise ValidationError("You must select a reason for the return.")

                # Temporary list to hold valid items before creating DB objects
                items_to_process = []
                total_return_value = Decimal('0.0') # Use Decimal for precision

                for item_id_str in request.POST.keys():
                    if item_id_str.startswith('return_quantity_'):
                        item_id = item_id_str.split('_')[-1]
                        quantity = int(request.POST.get(item_id_str, 0))

                        if quantity > 0:
                            purchase_item = get_object_or_404(PurchaseItem, id=item_id, purchase=purchase)
                            
                            # More robust validation against already returned items
                            if quantity > purchase_item.returnable_quantity:
                                raise ValidationError(f"Cannot return {quantity} of {purchase_item.item.item_name}. "
                                                      f"Only {purchase_item.returnable_quantity} are available to return.")
                            
                            items_to_process.append({
                                'purchase_item': purchase_item,
                                'quantity': quantity,
                            })
                            total_return_value += purchase_item.purchase_price * Decimal(quantity)

                # Validation: Ensure at least one item with quantity > 0 is being returned
                if not items_to_process:
                    raise ValidationError("You must specify a return quantity of at least 1 for one or more items.")

                # --- CORRECTED LOGIC ---
                # 1. Create the main PurchaseReturn object FIRST
                purchase_return = PurchaseReturn.objects.create(
                    purchase=purchase, # Corrected field name
                    return_reason=return_reason,
                    notes=notes,
                    total_return_amount=total_return_value, # Set the total amount now
                    created_by=account,
                    tenant=tenant, # Explicitly set the tenant
                )

                # 2. Now that purchase_return has an ID, create the related items
                for item_data in items_to_process:
                    pi = item_data['purchase_item']
                    PurchaseReturnItem.objects.create(
                        purchase_return=purchase_return,
                        purchase_item=pi,
                        quantity=item_data['quantity'],
                        return_price=pi.purchase_price,
                        # The amount will be calculated by the model's save method
                    )
                    
                    # 3. Update stock for each item
                    product = get_object_or_404(Product, id=pi.item.id)
                    product.opening_stock -= item_data['quantity']
                    product.save()
                    # After successfully saving the return, update the original purchase's status
                    # Pass the 'account' object to the updated method
                    purchase.update_status_after_return(changed_by_user=account)

                messages.success(request, f'Return created successfully for purchase {purchase.bill_number}')
                return redirect('view_purchase', purchase_id=purchase.id)
                
        except ValidationError as e:
            # Use e.message to get a cleaner error string
            messages.error(request, e.message)
        except Exception as e:
            messages.error(request, f'An unexpected error occurred: {str(e)}')
            
    context = {
        'purchase': purchase,
        'add': account,
        'tenant': tenant,
        'return_reasons': PurchaseReturn.RETURN_REASONS,
    }
    return render(request, 'create_purchase_return.html', context)

# Vendor Performance View
@tenant_required
def vendor_performance_view(request):
    account = request.user
    tenant = None

    if account.role == 'superadmin':
        tenant_id = request.GET.get('tenant_id')
        if not tenant_id:
            messages.info(request, "From the sidebar, please expand 'Vendor Performance' and select a tenant to view their dashboard.")
            return redirect('superadmin_dashboard')
        tenant = get_object_or_404(Tenant, id=tenant_id)
    else:
        tenant = request.tenant

    # --- OPTIMIZED QUERY WITH ANNOTATIONS (CORRECTED) ---
    vendors = Create_party.objects.filter(
        tenant=tenant,
        party_type__in=['Supplier', 'Both']
    ).annotate(
        # Sum correctly uses a default
        annotated_total_volume=Sum('purchases__total_amount', default=0),
        # Count does not need a default, it will return 0 if none exist
        annotated_successful_deliveries=Count('purchases', filter=Q(purchases__status='RECEIVED')),
        annotated_pending_orders=Count('purchases', filter=Q(purchases__status__in=['ORDERED', 'PARTIALLY_RECEIVED']))
    ).order_by('-annotated_total_volume')

    # --- Prepare Data for the Chart (no changes needed here) ---
    chart_data = []
    for vendor in vendors[:10]:
        chart_data.append({
            'name': vendor.party_name,
            'volume': float(vendor.annotated_total_volume)
        })
    
    chart_labels = json.dumps([item['name'] for item in chart_data])
    chart_values = json.dumps([item['volume'] for item in chart_data])

    context = {
        'add': account,
        'tenant': tenant,
        'vendors': vendors,
        'chart_labels': chart_labels,
        'chart_values': chart_values,
    }
    return render(request, 'vendor_performance.html', context)

# Stock Adjustments list
@tenant_required
def stock_adjustment_list(request):
    account = request.user
    adjustments = StockAdjustment.objects.none()
    tenant = None

    if account.role == 'superadmin':
        tenant_id = request.GET.get('tenant_id')
        if tenant_id:
            tenant = get_object_or_404(Tenant, id=tenant_id)
            adjustments = StockAdjustment.objects.filter(tenant=tenant).select_related('product', 'adjusted_by').order_by('-created_at')
    else:
        tenant = request.tenant
        adjustments = StockAdjustment.objects.filter(tenant=tenant).select_related('product', 'adjusted_by').order_by('-created_at')

    context = {
        'add': account,
        'tenant': tenant,
        'adjustments': adjustments,
    }
    return render(request, 'stock_adjustment_list.html', context)

# Create Stock Adjustments 
@tenant_required
def create_stock_adjustment(request):
    account = request.user
    # --- MODIFIED LOGIC FOR SUPERADMIN GET REQUEST ---
    tenant = None
    if account.role == 'superadmin':
        tenant_id = request.GET.get('tenant_id')
        if tenant_id:
            tenant = get_object_or_404(Tenant, id=tenant_id)
    else:
        tenant = request.tenant
    # --- END OF MODIFICATION ---

    if request.method == 'POST':
        try:
            with transaction.atomic():
                target_tenant = None
                if account.role == 'superadmin':
                    tenant_id = request.POST.get('tenant_id')
                    if not tenant_id:
                        raise ValidationError("Superadmin must select a tenant.")
                    target_tenant = get_object_or_404(Tenant, id=tenant_id)
                else:
                    target_tenant = request.tenant

                product_id = request.POST.get('product')
                adjustment_type = request.POST.get('adjustment_type')
                quantity = int(request.POST.get('quantity'))
                reason = request.POST.get('reason')
                notes = request.POST.get('notes')

                if quantity <= 0:
                    raise ValidationError("Quantity must be a positive number.")

                product = get_object_or_404(Product, id=product_id, tenant=target_tenant)

                # Create the record first for an audit trail
                StockAdjustment.objects.create(
                    product=product,
                    adjustment_type=adjustment_type,
                    quantity=quantity,
                    reason=reason,
                    notes=notes,
                    adjusted_by=account,
                    tenant=target_tenant
                )

                # Now, update the actual stock
                if adjustment_type == 'ADD':
                    product.opening_stock += quantity
                elif adjustment_type == 'REMOVE':
                    if quantity > product.opening_stock:
                        raise ValidationError(f"Cannot remove {quantity} items. Only {product.opening_stock} in stock.")
                    product.opening_stock -= quantity
                
                product.save()

                messages.success(request, f"Stock for '{product.item_name}' adjusted successfully.")
                redirect_url = reverse('stock_adjustment_list')
                if account.role == 'superadmin':
                    return redirect(f"{redirect_url}?tenant_id={target_tenant.id}")
                return redirect(redirect_url)

        except (ValidationError, Exception) as e:
            messages.error(request, str(e))
    
    # For GET request
    products = Product.objects.none()
    if tenant:
        products = Product.objects.filter(tenant=tenant, is_active=True).order_by('item_name')

    context = {
        'add': account,
        'tenant': tenant,
        'products': products,
        'adjustment_types': StockAdjustment.ADJUSTMENT_TYPES,
        'reasons': StockAdjustment.REASONS,
    }
    # For superadmin, they will need to select a tenant on the form first via JS
    if account.role == 'superadmin':
        context['tenants'] = Tenant.objects.filter(is_active=True)

    return render(request, 'create_stock_adjustment.html', context)

@superadmin_required # Use your existing decorator for security
def get_products_for_tenant_api(request, tenant_id):
    """
    An API endpoint that returns a list of products for a given tenant.
    """
    products = Product.objects.filter(tenant_id=tenant_id, is_active=True).values('id', 'item_name', 'opening_stock')
    return JsonResponse(list(products), safe=False)