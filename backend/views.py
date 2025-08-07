from django.shortcuts import render,redirect, get_object_or_404
from backend.models import *
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.db.models import Sum, F
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
from django.db.models import Sum, Q
from decimal import Decimal



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
def Admin_loginVW(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('pass')
        account = authenticate(request, username=email, password=password)
        if account and account.is_active:
            request.session['email'] = account.email
            request.session['account_id'] = account.id
            if account.role != 'superadmin':
                request.session['tenant_id'] = account.tenant.id
            return redirect('/dash')
        messages.error(request, "Invalid Email or Password")
        return redirect('/')
    return render(request, 'Admin_login.html')

# Dashboard View
@tenant_required
def DashVw(request):
    account = Account.objects.filter(email=request.session['email']).first()
    tenant = get_tenant(request) if not account.role == 'superadmin' else None
    return render(request, 'Dash.html', {'add': account, 'tenant': tenant})

# Logout View
def logout(request):
    request.session.flush()
    messages.info(request, "Logout Successfully!!")
    return redirect('/')

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
                party_category=request.POST.get('p_category'), # Corrected from p_type
                billing_address=request.POST.get('billing_address'),
                shipping_address=request.POST.get('shipping_address'),
                credit_period=request.POST.get('credit_period', 0),
                credit_limit=request.POST.get('credit_limit', 0)
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

# Delete Party View
@tenant_required
def Dlt_Party_ListVw(request, id):
    account = Account.objects.filter(email=request.session['email']).first()
    tenant = get_tenant(request) if not account.role == 'superadmin' else None
    
    if account.role == 'superadmin':
        Create_party.objects.filter(id=id).update(is_active=False)
    else:
        Create_party.objects.filter(id=id, tenant=tenant).update(is_active=False)
    messages.info(request, 'Party Deleted !')
    return redirect('/Party_list')

# Update Party View
@tenant_required
def Updt_Party_List(request, id):
    account = Account.objects.filter(email=request.session['email']).first()
    tenant = get_tenant(request) if not account.role == 'superadmin' else None
    
    if account.role == 'superadmin':
        party_list = Create_party.objects.filter(id=id)
    else:
        party_list = Create_party.objects.filter(id=id, tenant=tenant)
    
    if request.method == "POST":
        party_name = request.POST['pname']
        mobile_num = request.POST['pnum']
        email = request.POST['pemail']
        opening_balance = request.POST['op_bal']
        gst_no = request.POST['gst_in']
        pan_no = request.POST['pan_no']
        party_type = request.POST['p_type']
        party_category = request.POST['p_type']
        billing_address = request.POST['billing_address']
        shipping_address = request.POST['shipping_address']
        credit_period = request.POST['credit_period']
        credit_limit = request.POST['credit_limit']
        
        party_list.update(
            party_name=party_name,
            mobile_num=mobile_num,
            email=email,
            opening_balance=opening_balance,
            gst_no=gst_no,
            pan_no=pan_no,
            party_type=party_type,
            party_category=party_category,
            billing_address=billing_address,
            shipping_address=shipping_address,
            credit_period=credit_period,
            credit_limit=credit_limit
        )
        messages.info(request, 'Party Update Successfully.')
        return redirect('/Party_list')
    return render(request, 'Update_party.html', {'add': account, 'party_list': party_list, 'tenant': tenant})

# Item List View
@tenant_required
def item_list_view(request):
    account = Account.objects.filter(email=request.session['email']).first()
    tenant = None
    products = Product.objects.none()
    services = Service.objects.none()

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
    
    items = list(products) + list(services)
    current_date = timezone.now().date()
    thirty_days_from_now = current_date + timedelta(days=30)
    expiring_count = products.filter(
        expiry_date__isnull=False,
        expiry_date__lte=thirty_days_from_now,
        expiry_date__gte=current_date
    ).count()
    
    context = {
        'add': account,
        'items': items,
        'product_count': products.count(),
        'service_count': services.count(),
        'expiring_count': expiring_count,
        'tenant': tenant,
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

# Create Sale View
# @tenant_required
# def Create_saleVw(request):
#     account = Account.objects.filter(email=request.session['email']).first()
#     tenant = get_tenant(request) if not account.role == 'superadmin' else None
#     tenants = Tenant.objects.all() if account.role == 'superadmin' else []
    
#     context = {
#         'items': ItemBase.objects.filter(tenant=tenant, is_active=True).order_by('item_name') if tenant else ItemBase.objects.filter(is_active=True).order_by('item_name'),
#         'parties': Create_party.objects.filter(tenant=tenant, is_active=True).order_by('party_name') if tenant else Create_party.objects.filter(is_active=True).order_by('party_name'),
#         'invoice_no': f"INV-{uuid.uuid4().hex[:8].upper()}",
#         'add': account,
#         'tenant': tenant,
#         'tenants': tenants,
#     }
#     return render(request, 'Create_Sale.html', context)

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

# Delete Sales View
from django.urls import reverse

@tenant_required
def delete_sale(request, sale_id):
    account = get_object_or_404(Account, email=request.session['email'])
    sale_to_delete = get_object_or_404(Sale, id=sale_id)
    
    # Store the tenant ID before deleting the sale
    tenant_id = sale_to_delete.tenant.id

    if account.role != 'superadmin' and sale_to_delete.tenant != request.tenant:
        messages.error(request, "You are not authorized to delete this sale.")
        return redirect('sales_list')

    try:
        with transaction.atomic():
            for item in sale_to_delete.items.all():
                if item.item and item.item.item_type == 'product':
                    product = get_object_or_404(Product, id=item.item.id)
                    product.opening_stock += item.quantity
                    product.save()
            
            invoice_no = sale_to_delete.invoice_no
            sale_to_delete.delete()
            messages.success(request, f"Invoice {invoice_no} has been deleted successfully.")
    
    except Exception as e:
        messages.error(request, f"An error occurred while deleting the sale: {e}")

    # Redirect correctly based on the user's role
    if account.role == 'superadmin':
        # For superadmin, redirect back to the specific tenant's sales list
        redirect_url = f"{reverse('sales_list')}?tenant_id={tenant_id}"
        return redirect(redirect_url)
    else:
        # For regular users, redirect to their own sales list
        return redirect('sales_list')

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

# Edit Sale View
@never_cache
@tenant_required
def edit_sale_view(request, sale_id):
    account = Account.objects.filter(email=request.session['email']).first()
    tenant = get_tenant(request) if not account.role == 'superadmin' else None
    sale = get_object_or_404(Sale, id=sale_id, tenant=tenant) if tenant else get_object_or_404(Sale, id=sale_id)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                for item in sale.items.all():
                    if item.item and item.item.item_type == 'product':
                        product = Product.objects.select_for_update().get(id=item.item.id, tenant=tenant) if tenant else Product.objects.select_for_update().get(id=item.item.id)
                        product.opening_stock += item.quantity
                        product.save()
                
                sale.items.all().delete()
                
                post_data = request.POST
                party = get_object_or_404(Create_party, id=post_data.get('party_id'), tenant=tenant) if tenant else get_object_or_404(Create_party, id=post_data.get('party_id'))
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
                    
                    item_obj = get_object_or_404(ItemBase, id=item_id, tenant=tenant) if tenant else get_object_or_404(ItemBase, id=item_id)
                    unit_price = float(item_obj.sale_price)
                    item_subtotal = quantity * unit_price
                    taxable_item_amount = item_subtotal - item_discount
                    gst_rate = float(re.sub(r'[^0-9.]', '', item_obj.gst_rate or '0'))
                    tax_for_item = taxable_item_amount * (gst_rate / 100)
                    
                    total_item_subtotal += item_subtotal
                    total_tax += tax_for_item
                    
                    if item_obj.item_type == 'product':
                        product = Product.objects.select_for_update().get(id=item_obj.id, tenant=tenant) if tenant else Product.objects.select_for_update().get(id=item_obj.id)
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
                
                SaleItem.objects.bulk_create(new_sale_items)
                
                messages.success(request, f"Sale {sale.invoice_no} updated successfully!")
                return redirect('sales_list')
        
        except (ValidationError, Exception) as e:
            messages.error(request, f"Error updating sale: {e}")
            return redirect('edit_sale', sale_id=sale.id)
    
    context = {
        'sale': sale,
        'all_items': ItemBase.objects.filter(tenant=tenant, is_active=True).order_by('item_name') if tenant else ItemBase.objects.filter(is_active=True).order_by('item_name'),
        'all_parties': Create_party.objects.filter(tenant=tenant, is_active=True).order_by('party_name') if tenant else Create_party.objects.filter(is_active=True).order_by('party_name'),
        'add': account,
        'tenant': tenant,
    }
    return render(request, 'edit_sale.html', context)

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

     # Add this query to fetch the 10 most recent activity logs
    activity_logs = ActivityLog.objects.select_related('actor', 'tenant').order_by('-timestamp')[:10]

    context = {
        'add': account,
        'tenants': tenants,
        'total_accounts': total_accounts,
        'total_parties': total_parties,
        'total_items': total_items,
        'total_sales': total_sales,
        'total_revenue': total_revenue,
        'activity_logs': activity_logs,
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