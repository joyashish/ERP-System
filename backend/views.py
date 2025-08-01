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
    return render(request, '/')

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
        tenant = get_tenant(request)
        party_list = Create_party.objects.filter(is_active=True) if not tenant else Create_party.objects.filter(tenant=tenant, is_active=True)
    else:
        tenant = get_object_or_404(Tenant, id=request.session['tenant_id'])
        party_list = Create_party.objects.filter(tenant=tenant, is_active=True, user=account)

    total_balance = party_list.aggregate(total=Sum('opening_balance'))['total'] or 0.00
    total_credit = party_list.aggregate(total=Sum('credit_limit'))['total'] or 0.00
    
    context = {
        'party_list': party_list,
        'total_parties': party_list.count(),
        'total_balance': total_balance,
        'total_credit': total_credit,
        'add': account,
        'tenant': tenant,
    }
    return render(request, 'Party_list.html', context)

# Create Party View
@tenant_required
def Create_partyVw(request):
    account = Account.objects.filter(email=request.session['email']).first()
    tenant = get_tenant(request) if not account.role == 'superadmin' else None
    tenants = Tenant.objects.all() if account.role == 'superadmin' else []
    
    if request.method == "POST":
        if account.role == 'superadmin' and not tenant:
            messages.error(request, "Please select a tenant.")
            return redirect('Create_partyVw')

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
        
        if Create_party.objects.filter(party_name=party_name, mobile_num=mobile_num, email=email, tenant=tenant).exists():
            messages.info(request, f"{party_name} Already Exist...")
        else:
            Create_party.objects.create(
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
                credit_limit=credit_limit,
                tenant=tenant,
                user=account
            )
            messages.info(request, 'Party Added Successfully...')
            return redirect('/Party_list')
    return render(request, 'Create_party.html', {'add': account, 'tenant': tenant,'tenants': tenants})

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
    tenant = get_tenant(request) if not account.role == 'superadmin' else None

    if account.role == 'superadmin':
        products = Product.objects.all() if not tenant else Product.objects.filter(tenant=tenant)
        services = Service.objects.all() if not tenant else Service.objects.filter(tenant=tenant)
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
    account = Account.objects.filter(email=request.session['email']).first()
    tenant = get_tenant(request) if not account.role == 'superadmin' else None
    tenants = Tenant.objects.all() if account.role == 'superadmin' else []
    
    units = Unit.objects.filter(tenant=tenant, is_active=True) if tenant else Unit.objects.all()
    categories = Category.objects.filter(tenant=tenant, is_active=True) if tenant else Category.objects.all()
    
    if request.method == "POST":
        if account.role == 'superadmin' and not tenant:
            messages.error(request, "Please select a tenant.")
            return redirect('Create_item')

        try:
            item_type = request.POST.get('item_type', '').strip()
            if item_type not in ['product', 'service']:
                messages.error(request, "Invalid item type")
                return redirect('Create_item')
            
            item_name = request.POST.get('item_name', '').strip()
            if not item_name:
                messages.error(request, "Item name is required")
                return redirect('Create_item')
            
            if Product.objects.filter(item_name=item_name, tenant=tenant).exists() or Service.objects.filter(item_name=item_name, tenant=tenant).exists():
                messages.warning(request, f"Item '{item_name}' already exists")
                return redirect('Create_item')
            
            common_data = {
                'item_name': item_name,
                'item_type': item_type,
                'description': request.POST.get('item_des', '') or request.POST.get('service_description', ''),
                'category_id': request.POST.get('category', '') or request.POST.get('service_category', ''),
                'gst_rate': request.POST.get('gst', '') or request.POST.get('gst_service', ''),
                'hsn_sac_code': request.POST.get('hsn', '') or request.POST.get('hsn_service', ''),
                'sale_price': request.POST.get('sale_price', '') or request.POST.get('sale_price_service', ''),
                'tenant': tenant,
            }
            
            if 'product_image' in request.FILES:
                common_data['image'] = request.FILES['product_image']
            elif 'service_image' in request.FILES:
                common_data['image'] = request.FILES['service_image']
            
            if item_type == 'product':
                product_data = {
                    **common_data,
                    'unit_id': request.POST.get('unit', '') or None,
                    'purchase_price': request.POST.get('purchase_price', '') or 0,
                    'opening_stock': request.POST.get('opening_stock', 0) or 0,
                    'stock_date': request.POST.get('stock_date', '') or None,
                    'expiry_date': request.POST.get('expiry_date', '') or None,
                    'batch_number': request.POST.get('batch_number', '') or None,
                }
                if not product_data['purchase_price']:
                    product_data['purchase_price'] = 0
                elif not str(product_data['purchase_price']).replace('.', '', 1).isdigit():
                    raise ValidationError({'purchase_price': 'Purchase price must be a valid number'})
                
                product = Product(**product_data)
                product.full_clean()
                product.save()
                messages.success(request, "Product created successfully!")
            else:
                service_data = {
                    **common_data,
                    'service_unit': request.POST.get('ltype', '') or None,
                }
                if not service_data['sale_price']:
                    raise ValidationError({'sale_price_service': 'Service price is required'})
                elif not str(service_data['sale_price']).replace('.', '', 1).isdigit():
                    raise ValidationError({'sale_price_service': 'Service price must be a valid number'})
                
                service = Service(**service_data)
                service.full_clean()
                service.save()
                messages.success(request, "Service created successfully!")
            
            return redirect('Item_list')
        
        except ValidationError as e:
            if hasattr(e, 'error_dict'):
                for field, errors in e.error_dict.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
            else:
                for error in e.messages:
                    messages.error(request, error)
        except Exception as e:
            messages.error(request, f"Error creating item: {str(e)}")
        
        return redirect('Create_item')
    
    context = {
        'add': account,
        'unit': units,
        'category': categories,
        'tenant': tenant,'tenants': tenants,
    }
    return render(request, 'Create_item.html', context)

# Create Sale View
@tenant_required
def Create_saleVw(request):
    account = Account.objects.filter(email=request.session['email']).first()
    tenant = get_tenant(request) if not account.role == 'superadmin' else None
    tenants = Tenant.objects.all() if account.role == 'superadmin' else []
    
    context = {
        'items': ItemBase.objects.filter(tenant=tenant, is_active=True).order_by('item_name') if tenant else ItemBase.objects.filter(is_active=True).order_by('item_name'),
        'parties': Create_party.objects.filter(tenant=tenant, is_active=True).order_by('party_name') if tenant else Create_party.objects.filter(is_active=True).order_by('party_name'),
        'invoice_no': f"INV-{uuid.uuid4().hex[:8].upper()}",
        'add': account,
        'tenant': tenant,
        'tenants': tenants,
    }
    return render(request, 'Create_Sale.html', context)

# Create Sale View (Detailed)
@tenant_required
def create_sale_view(request):
    account = get_object_or_404(Account, email=request.session['email'])
    tenant = get_tenant(request) if not account.role == 'superadmin' else None
    tenants = Tenant.objects.all() if account.role == 'superadmin' else []
    
    if request.method == "POST":
        if account.role == 'superadmin' and not tenant:
            messages.error(request, "Please select a tenant.")
            return redirect('Create_Sale')
            
        try:
            with transaction.atomic():
                post_data = request.POST
                party = get_object_or_404(Create_party, id=post_data.get('party_id'), tenant=tenant) if tenant else get_object_or_404(Create_party, id=post_data.get('party_id'))
                
                invoice_date_str = post_data.get('invoice_date')
                due_date_str = post_data.get('due_date')
                if not invoice_date_str:
                    raise ValidationError("Invoice Date is required.")
                
                invoice_date_obj = datetime.strptime(invoice_date_str, '%Y-%m-%d').date()
                due_date_obj = datetime.strptime(due_date_str, '%Y-%m-%d').date() if due_date_str else None
                
                items_data = []
                total_item_subtotal = 0
                total_tax = 0
                item_indices = sorted(list(set(re.findall(r'items\[(\d+)\]', ' '.join(post_data.keys())))))
                
                for index in item_indices:
                    item_id = post_data.get(f'items[{index}][item_id]')
                    quantity = int(post_data.get(f'items[{index}][quantity]', 0))
                    if not item_id or quantity <= 0:
                        continue
                    item = get_object_or_404(ItemBase, id=item_id, tenant=tenant) if tenant else get_object_or_404(ItemBase, id=item_id)
                    unit_price = float(item.sale_price)
                    item_discount = float(post_data.get(f'items[{index}][discount]', 0))
                    item_subtotal = quantity * unit_price
                    taxable_amount_item = item_subtotal - item_discount
                    gst_rate = float(re.sub(r'[^0-9.]', '', item.gst_rate or '0'))
                    tax_amount_item = taxable_amount_item * (gst_rate / 100)
                    total_item_subtotal += item_subtotal
                    total_tax += tax_amount_item
                    if item.item_type == 'product':
                        product = Product.objects.select_for_update().get(id=item.id, tenant=tenant) if tenant else Product.objects.select_for_update().get(id=item.id)
                        if product.opening_stock < quantity:
                            raise ValidationError(f"Insufficient stock for {item.item_name}.")
                        product.opening_stock -= quantity
                        product.save()
                    items_data.append({
                        'item_instance': item, 'quantity': quantity, 'discount': item_discount,
                        'tax_amount': tax_amount_item, 'amount': taxable_amount_item + tax_amount_item
                    })
                
                if not items_data:
                    raise ValidationError("At least one valid item must be added.")
                
                discount_overall = float(post_data.get('discount', 0))
                additional_charges = float(post_data.get('additional_charges', 0))
                taxable_amount_total = total_item_subtotal - discount_overall
                total_amount = taxable_amount_total + total_tax + additional_charges
                amount_received = float(post_data.get('amount_received', 0))
                
                sale = Sale.objects.create(
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
                    user=account,
                    tenant=tenant
                )
                
                for data in items_data:
                    SaleItem.objects.create(sale=sale, item=data['item_instance'], **{k: v for k, v in data.items() if k != 'item_instance'})
                
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Sale created successfully!',
                        'sale_data': {
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
                            'items': [{
                                'name': item.item.item_name, 'qty': item.quantity, 'rate': f'{item.item.sale_price:.2f}',
                                'tax_rate': f'{float(re.sub(r"[^0-9.]", "", item.item.gst_rate or "0")):.0f}%',
                                'amount': f'{item.amount:.2f}'
                            } for item in sale.items.all()],
                        }
                    })
                else:
                    messages.success(request, "Sale created successfully!")
                    return redirect('Create_Sale')
        
        except (ValidationError, Exception) as e:
            error_message = str(e.message if hasattr(e, 'message') else e)
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': error_message}, status=400)
            else:
                messages.error(request, error_message)
                return redirect('Create_Sale')
    
    context = {
        'items': ItemBase.objects.filter(tenant=tenant, is_active=True).order_by('item_name') if tenant else ItemBase.objects.filter(is_active=True).order_by('item_name'),
        'parties': Create_party.objects.filter(tenant=tenant, is_active=True).order_by('party_name') if tenant else Create_party.objects.filter(is_active=True).order_by('party_name'),
        'invoice_no': f"INV-{uuid.uuid4().hex[:8].upper()}",
        'add': account,
        'tenant': tenant,'tenants': tenants,
    }
    return render(request, 'create_sale.html', context)

# Sales List View
@tenant_required
def sales_list(request):
    account = Account.objects.filter(email=request.session['email']).first()
    tenant = get_tenant(request) if not account.role == 'superadmin' else None
    
    if account.role == 'superadmin':
        sales = Sale.objects.select_related('party').all().order_by('-invoice_date') if not tenant else Sale.objects.filter(tenant=tenant).select_related('party').order_by('-invoice_date')
    else:
        tenant = get_object_or_404(Tenant, id=request.session['tenant_id'])
        sales = Sale.objects.filter(tenant=tenant).select_related('party').all().order_by('-invoice_date')
    
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
    }
    return render(request, 'sales_list.html', context)

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
        admin_email=Subquery(first_account.values('email')[:1]),
        admin_role=Subquery(first_account.values('role')[:1])
    ).order_by('-created_at')
    
    account = Account.objects.filter(email=request.session.get('email')).first()
    total_accounts = Account.objects.count()
    total_parties = Create_party.objects.count()
    total_items = ItemBase.objects.count()
    total_sales = Sale.objects.count()
    total_revenue = Sale.objects.aggregate(total=Sum('total_amount'))['total'] or 0.00

    context = {
        'add': account,
        'tenants': tenants,
        'total_accounts': total_accounts,
        'total_parties': total_parties,
        'total_items': total_items,
        'total_sales': total_sales,
        'total_revenue': total_revenue,
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