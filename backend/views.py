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



# Create your views here.
#-------------printview-------------------------#
def printVw(request):
    return render(request,'print.html')
#---------------add unit------------------------#
def add_unit(request):
    if request.method == 'POST':
        unit_name = request.POST.get('unit_name')
        if unit_name:
            Unit.objects.create(name=unit_name)
    return redirect('/Create_item') 
#---------------add Category------------------------#
def add_category(request):
    if request.method == 'POST':
        cat_name = request.POST.get('cat_name')
        if cat_name:
            Category.objects.create(cname=cat_name)
    return redirect('/Create_item') 


#----------/////admin login\\\\\\\\------------#
def Admin_loginVW(request):
    if request.method=="POST":
        email = request.POST.get('email')
        password = request.POST.get('pass')
       # Admin_login.objects.create(email=email,password=password,phone=phone)
        if Admin_login.objects.filter(email=email,password=password,role='admin').exists():
           data=Admin_login.objects.filter(email=email).first()
           request.session['email']=data.email
           request.session['user_id']=data.id
         
           return redirect('/dash')
        else:
            messages.error(request,"Invalid Email or Password")
            return redirect('/')
    return render(request,'Admin_login.html')

#..../// Dash View \\\ ....#
def DashVw(request):
    if 'email' in request.session:
        email = request.session['email']
        add  = Admin_login.objects.filter(email=email).first()
        return render(request,'Dash.html',{'add':add})
    else:
        return redirect('/')

#...../// Logout \\\ ....# 
def logout(request):
   del request.session['email']
   messages.info(request,"Logout Successfully!!")
   return redirect('/')  


#........///// change password \\\\\ ......#
def ChangePasswordVw(request):
    if ('email' in request.session):
        email = request.session['email']
        data = Admin_login.objects.filter(email=email).first()

        if request.method == 'POST':
            password = request.POST.get('password')
            data.password = password
            data.save()
            messages.info(request,'Password has been changed Successfully!!'+"  "+'Login Again for better experience !!')
        return render(request,'change_pass.html',{'data':data,'add':data})
    else:
      return redirect('/')


#......../////  party list \\\\\ ......#
from django.db.models import Sum

def Party_listVw(request):
    if 'email' in request.session:
        email = request.session['email']
        add  = Admin_login.objects.filter(email=email).first()
        party_list = Create_party.objects.filter(
            status=True,
            user_id_id=request.session['user_id']
        )
        
        # Calculate aggregates
        total_balance = party_list.aggregate(total=Sum('opening_balance'))['total'] or 0.00
        total_credit = party_list.aggregate(total=Sum('credit_limit'))['total'] or 0.00
        
        context = {
            'party_list': party_list,
            'total_parties': party_list.count(),
            'total_balance': total_balance,
            'total_credit': total_credit,
            'add':add,
        }
        return render(request, 'Party_list.html', context)
    else:
        return redirect('/')



#........///// Create party \\\\\ ......#
def Create_partyVw(request):
    if 'email' in request.session:
        email = request.session['email']
        add  = Admin_login.objects.filter(email=email).first()
        if request.method=="POST":
            party_name = request.POST['pname']
            mobile_num  = request.POST['pnum']
            email  = request.POST['pemail']
            opening_balance = request.POST['op_bal']
            gst_no = request.POST['gst_in']
            pan_no = request.POST['pan_no']
            party_type = request.POST['p_type']
            party_category = request.POST['p_type']
            billing_address = request.POST['billing_address']
            shipping_address = request.POST['shipping_address']
            credit_period = request.POST['credit_period']
            credit_limit = request.POST['credit_limit']
            

            if Create_party.objects.filter(party_name=party_name,mobile_num=mobile_num,email=email).exists():
                messages.info(request,company+" "+"Already Exist...!!#")
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
                user_id_id=request.session['user_id']
            )   
                messages.info(request,'Party'+' '+'Added Successfully...!!#')
                return redirect('/Party_list')
        return render(request,'Create_party.html',{'add':add}) 
    else:
        return redirect('/')
#.......//////// Add party list [dlt] \\\\\\\\\.........# 
def Dlt_Party_ListVw(request,id):
    if 'email' in request.session :
        email = request.session['email']
        add = Admin_login.objects.filter(email=email).first()
        Create_party.objects.filter(id=id).update(status=False)
        messages.info(request,'Party Deleted ...!!#')
        return redirect('/Party_list') 
    else:
        return redirect('/')

#.......//////// Add Company list  [Update] \\\\\\\\\.........# 
def Updt_Party_List(request,id):
    if 'email' in request.session :
        email = request.session['email']
        add = Admin_login.objects.filter(email=email).first()
        party_list = Create_party.objects.filter(id=id)
        if request.method=="POST":
            party_name = request.POST['pname']
            mobile_num  = request.POST['pnum']
            email  = request.POST['pemail']
            opening_balance = request.POST['op_bal']
            gst_no = request.POST['gst_in']
            pan_no = request.POST['pan_no']
            party_type = request.POST['p_type']
            party_category = request.POST['p_type']
            billing_address = request.POST['billing_address']
            shipping_address = request.POST['shipping_address']
            credit_period = request.POST['credit_period']
            credit_limit = request.POST['credit_limit']

            Create_party.objects.filter(id=id).update(party_name=party_name,mobile_num=mobile_num,email=email)
            messages.info(request,'Party'+" "+"Update Succesfully...!!#")
            return redirect('/Add_party')
        return render(request,'Update_party.html',{'add':add,"party_list":party_list})
    else:
        return redirect('/')    
#........///// Items List \\\\\ ......#
# def Item_listVw(request):
#     return render(request,'Item_list.html')

# New Item List #
def item_list_view(request):
    if 'email' not in request.session:
        return redirect('/')

    email = request.session['email']
    admin_user = Admin_login.objects.filter(email=email).first()

    # Fetch all items (Products and Services)
    products = Product.objects.all()
    services = Service.objects.all()

    # Combine items for display
    items = list(products) + list(services)

    # Calculate metrics
    # Product Count: Total number of Products
    product_count = products.count()

    # Service Count: Total number of Services
    service_count = services.count()

    # Expiring Items: Count Products with expiry_date within 30 days from July 10, 2025
    current_date = timezone.now().date()
    thirty_days_from_now = current_date + timedelta(days=30)
    expiring_count = products.filter(
        expiry_date__isnull=False,
        expiry_date__lte=thirty_days_from_now,
        expiry_date__gte=current_date
    ).count()

    context = {
        'add': admin_user,
        'items': items,
        'product_count': product_count,
        'service_count': service_count,
        'expiring_count': expiring_count,
    }
    return render(request, 'Item_list.html', context)
    

    
#........///// create Items \\\\\ ......#
def Create_itemVw(request):
    if 'email' not in request.session:
        return redirect('/')

    email = request.session['email']
    add = Admin_login.objects.filter(email=email).first()
    units = Unit.objects.filter(status=True)
    categories = Category.objects.filter(status=True)

    if request.method == "POST":
        try:
            item_name = request.POST.get('item_name')
            if not item_name:
                messages.error(request, "Item name is required")
                return redirect('Create_item')

            if Create_item.objects.filter(item_name=item_name).exists():
                messages.warning(request, f"Item '{item_name}' already exists")
                return redirect('Create_item')

            # Common fields
            item_data = {
                'item_name': item_name,
                'item_des': request.POST.get('item_des') or request.POST.get('service_description', ''),
                'category_id': request.POST.get('category') or request.POST.get('service_category'),
                'gst': request.POST.get('gst') or request.POST.get('gst_service', ''),
                'hsn_sac': request.POST.get('hsn') or request.POST.get('hsn_service', ''),
            }

            # Handle file uploads
            if 'product_image' in request.FILES:
                item_data['product_image'] = request.FILES['product_image']
            elif 'service_image' in request.FILES:
                item_data['product_image'] = request.FILES['service_image']

            if 'sale_price' in request.POST:  # Product
                item_data.update({
                    'item_type': 'product',
                    'unit_id': request.POST.get('unit'),
                    'sale_price': request.POST.get('sale_price'),
                    'purchase_price': request.POST.get('purchase_price'),
                    'opening_stock': request.POST.get('opening_stock', None),
                    'stock_date': request.POST.get('stock_date', None),
                    'entry_date': request.POST.get('entry_date', None),
                    'expiry_date': request.POST.get('expiry_date', None),
                    'batch_number': request.POST.get('batch_number', None),
                })
            else:  # Service
                item_data.update({
                    'item_type': 'service',
                    'unit_id': None,
                    'sale_price': request.POST.get('sale_price_service'),
                    'purchase_price': None,
                })

            # Create and save the item with validation
            new_item = Create_item(**item_data)
            new_item.full_clean()  # This will validate the model
            new_item.save()
            
            messages.success(request, f"{item_data['item_type'].capitalize()} created successfully!")
            return redirect('Item_list/')

        except ValidationError as e:
            # Handle both dictionary-style and list-style ValidationErrors
            if hasattr(e, 'message_dict'):
                for field, errors in e.message_dict.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
            else:
                for error in e.messages:
                    messages.error(request, error)
        except Exception as e:
            messages.error(request, f"Error creating item: {str(e)}")
        
        return redirect('Create_item')

    return render(request, 'Create_item.html', {
        'add': add,
        'unit': units,
        'category': categories,
    })
# New Create Item View #
def create_item_view(request):
    if 'email' not in request.session:
        return redirect('/')

    email = request.session['email']
    admin_user = Admin_login.objects.filter(email=email).first()
    units = Unit.objects.filter(status=True)
    categories = Category.objects.filter(status=True)

    if request.method == "POST":
        try:
            # Get item type from hidden input
            item_type = request.POST.get('item_type', '').strip()
            if item_type not in ['product', 'service']:
                messages.error(request, "Invalid item type")
                return redirect('Create_item')

            item_name = request.POST.get('item_name', '').strip()

            # Basic validation for item name
            if not item_name:
                messages.error(request, "Item name is required")
                return redirect('Create_item')

            # Check for existing item
            if Product.objects.filter(item_name=item_name).exists() or Service.objects.filter(item_name=item_name).exists():
                messages.warning(request, f"Item '{item_name}' already exists")
                return redirect('Create_item')

            # Common data for both product and service
            common_data = {
                'item_name': item_name,
                'item_type': item_type,
                'description': request.POST.get('item_des', '') or request.POST.get('service_description', ''),
                'category_id': request.POST.get('category', '') or request.POST.get('service_category', ''),
                'gst_rate': request.POST.get('gst', '') or request.POST.get('gst_service', ''),
                'hsn_sac_code': request.POST.get('hsn', '') or request.POST.get('hsn_service', ''),
                'sale_price': request.POST.get('sale_price', '') or request.POST.get('sale_price_service', ''),
            }

            # Handle file upload
            if 'product_image' in request.FILES:
                common_data['image'] = request.FILES['product_image']
            elif 'service_image' in request.FILES:
                common_data['image'] = request.FILES['service_image']

            if item_type == 'product':
                # Product-specific data
                product_data = {
                    **common_data,
                    'unit_id': request.POST.get('unit', '') or None,
                    'purchase_price': request.POST.get('purchase_price', '') or 0,
                    'opening_stock': request.POST.get('opening_stock', 0) or 0,
                    'stock_date': request.POST.get('stock_date', '') or None,
                    'expiry_date': request.POST.get('expiry_date', '') or None,
                    'batch_number': request.POST.get('batch_number', '') or None,
                }

                # Validate purchase_price
                if not product_data['purchase_price']:
                    product_data['purchase_price'] = 0
                elif not str(product_data['purchase_price']).replace('.', '', 1).isdigit():
                    raise ValidationError({'purchase_price': 'Purchase price must be a valid number'})

                product = Product(**product_data)
                product.full_clean()
                product.save()
                messages.success(request, "Product created successfully!")
            else:
                # Service-specific data
                service_data = {
                    **common_data,
                    'service_unit': request.POST.get('ltype', '') or None,
                }

                # Validate sale_price_service
                if not service_data['sale_price']:
                    raise ValidationError({'sale_price_service': 'Service price is required'})
                elif not str(service_data['sale_price']).replace('.', '', 1).isdigit():
                    raise ValidationError({'sale_price_service': 'Service price must be a valid number'})

                service = Service(**service_data)
                service.full_clean()
                service.save()
                messages.success(request, "Service created successfully!")

            return redirect('Create_item')

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
        'add': admin_user,
        'unit': units,
        'category': categories,
    }
    return render(request, 'Create_item.html', context)
    
#........///// Create Sale \\\\\ ......#
def Create_saleVw(request):
    return render(request,'Create_Sale.html')



def create_sale_view(request):
    if 'email' not in request.session:
        return redirect('/')

    admin_user = get_object_or_404(Admin_login, email=request.session['email'])

    if request.method == "POST":
        try:
            with transaction.atomic():
                post_data = request.POST
                party = get_object_or_404(Create_party, id=post_data.get('party_id'))

                # --- FIX: Convert date strings to date objects ---
                invoice_date_str = post_data.get('invoice_date')
                due_date_str = post_data.get('due_date')
                
                if not invoice_date_str:
                    raise ValidationError("Invoice Date is required.")

                # Parse the strings into date objects
                invoice_date_obj = datetime.strptime(invoice_date_str, '%Y-%m-%d').date()
                due_date_obj = datetime.strptime(due_date_str, '%Y-%m-%d').date() if due_date_str else None

                # ... (item processing logic remains the same) ...
                items_data = []
                total_item_subtotal = 0
                total_tax = 0
                item_indices = sorted(list(set(re.findall(r'items\[(\d+)\]', ' '.join(post_data.keys())))))

                for index in item_indices:
                    item_id = post_data.get(f'items[{index}][item_id]')
                    quantity = int(post_data.get(f'items[{index}][quantity]', 0))
                    if not item_id or quantity <= 0:
                        continue
                    # ... (rest of the item calculation logic) ...
                    item = get_object_or_404(ItemBase, id=item_id)
                    unit_price = float(item.sale_price)
                    item_discount = float(post_data.get(f'items[{index}][discount]', 0))
                    item_subtotal = quantity * unit_price
                    taxable_amount_item = item_subtotal - item_discount
                    gst_rate = float(re.sub(r'[^0-9.]', '', item.gst_rate or '0'))
                    tax_amount_item = taxable_amount_item * (gst_rate / 100)
                    total_item_subtotal += item_subtotal
                    total_tax += tax_amount_item
                    if item.item_type == 'product':
                        product = Product.objects.select_for_update().get(id=item.id)
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
                
                # Create Sale Object using the new date objects
                sale = Sale.objects.create(
                    invoice_no=post_data.get('invoice_no'),
                    party=party,
                    invoice_date=invoice_date_obj, # Use date object
                    due_date=due_date_obj,       # Use date object
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
                    user=admin_user
                )

                for data in items_data:
                    SaleItem.objects.create(sale=sale, item=data['item_instance'], **{k: v for k, v in data.items() if k != 'item_instance'})

                # AJAX vs. Normal POST Response
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Sale created successfully!',
                        'sale_data': {
                            'invoice_no': sale.invoice_no,
                            'invoice_date': sale.invoice_date.strftime('%d-%m-%Y'), # This will now work
                            'due_date': sale.due_date.strftime('%d-%m-%Y') if sale.due_date else 'N/A', # This will now work
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
        'items': ItemBase.objects.filter(is_active=True).order_by('item_name'),
        'parties': Create_party.objects.filter(status=True).order_by('party_name'),
        'invoice_no': f"INV-{uuid.uuid4().hex[:8].upper()}"
    }
    return render(request, 'create_sale.html', context)
#........///// Sales \\\\\ ......#

def sales_list(request):
    if 'email' not in request.session:
        return redirect('/') # Or your login URL

    # Fetch all sales, pre-loading the related party to prevent extra queries
    sales = Sale.objects.select_related('party').all().order_by('-invoice_date')

    # Calculate totals using aggregation for efficiency
    totals = Sale.objects.aggregate(
        total_sales=Sum('total_amount'),
        total_received=Sum('amount_received'),
        total_balance=Sum('balance_amount')
    )

    context = {
        'sales_list': sales,
        'total_sales': totals['total_sales'] or 0,
        'paid_amount': totals['total_received'] or 0,
        'unpaid_amount': totals['total_balance'] or 0,
    }
    return render(request, 'sales_list.html', context)
@never_cache
def edit_sale_view(request, sale_id):
    if 'email' not in request.session:
        return redirect('/')

    # Get the specific sale object we want to edit
    sale = get_object_or_404(Sale, id=sale_id)

    if request.method == 'POST':
        try:
            with transaction.atomic():
                post_data = request.POST
                
                # --- 1. Revert Stock for Original Items ---
                # Before making any changes, add the old item quantities back to stock.
                for item in sale.items.all():
                    if item.item and item.item.item_type == 'product':
                        product = Product.objects.select_for_update().get(id=item.item.id)
                        product.opening_stock += item.quantity
                        product.save()

                # --- 2. Delete Old Sale Items to prepare for new ones ---
                sale.items.all().delete()

                # --- 3. Process Form Data ---
                party = get_object_or_404(Create_party, id=post_data.get('party_id'))
                invoice_date_obj = datetime.strptime(post_data.get('invoice_date'), '%Y-%m-%d').date()
                due_date_str = post_data.get('due_date')
                due_date_obj = datetime.strptime(due_date_str, '%Y-%m-%d').date() if due_date_str else None
                
                # --- 4. Recalculate Totals & Deduct Stock for New/Updated Items ---
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
                    
                    item_obj = get_object_or_404(ItemBase, id=item_id)
                    unit_price = float(item_obj.sale_price)
                    
                    # Calculations for each item
                    item_subtotal = quantity * unit_price
                    taxable_item_amount = item_subtotal - item_discount
                    gst_rate = float(re.sub(r'[^0-9.]', '', item_obj.gst_rate or '0'))
                    tax_for_item = taxable_item_amount * (gst_rate / 100)
                    
                    total_item_subtotal += item_subtotal
                    total_tax += tax_for_item

                    # Deduct stock for the new/updated items
                    if item_obj.item_type == 'product':
                        product = Product.objects.select_for_update().get(id=item_obj.id)
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

                # Final total calculations
                overall_discount = float(post_data.get('discount', 0))
                additional_charges = float(post_data.get('additional_charges', 0))
                taxable_amount = total_item_subtotal - overall_discount
                total_amount = taxable_amount + total_tax + additional_charges
                amount_received = float(post_data.get('amount_received', 0))

                # --- 5. Update the EXISTING Sale Object ---
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
                sale.save() # This saves the changes to the existing row in the database

                # --- 6. Create the New SaleItem Objects ---
                SaleItem.objects.bulk_create(new_sale_items)

                messages.success(request, f"Sale {sale.invoice_no} updated successfully!")
                return redirect('sales_list')

        except (ValidationError, Exception) as e:
            messages.error(request, f"Error updating sale: {e}")
            return redirect('edit_sale', sale_id=sale.id)

    # For GET request
    context = {
        'sale': sale,
        'all_items': ItemBase.objects.filter(is_active=True).order_by('item_name'),
        'all_parties': Create_party.objects.filter(status=True).order_by('party_name'),
    }
    return render(request, 'edit_sale.html', context)
    
    