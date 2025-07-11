from django.shortcuts import render,redirect
from backend.models import *
from django.core.exceptions import ValidationError
from django.db.models import Sum, F
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages



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
        if Admin_login.objects.filter(email=email,password=password).exists():
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
                return redirect('/Create_party')
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
            return redirect('Create_item')

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

import uuid

import re

def create_sale_view(request):
    if 'email' not in request.session:
        return redirect('/')

    email = request.session['email']
    admin_user = Admin_login.objects.filter(email=email).first()
    items = ItemBase.objects.filter(is_active=True)

    if request.method == "POST":
        try:
            action = request.POST.get('action')
            party_name = request.POST.get('party_name')
            party_email = request.POST.get('party_email', '')
            party_phone = request.POST.get('party_phone', '')
            party_address = request.POST.get('party_address', '')
            invoice_date = request.POST.get('invoice_date')
            due_date = request.POST.get('due_date', None)
            payment_terms = request.POST.get('payment_terms', '')
            discount = request.POST.get('discount', '0')
            additional_charges = request.POST.get('additional_charges', '0')
            amount_received = request.POST.get('amount_received', '0')
            notes = request.POST.get('notes', '')
            terms_conditions = request.POST.get('terms_conditions', '')
            signature = request.FILES.get('signature')

            if not party_name or not invoice_date:
                messages.error(request, "Party name and invoice date are required")
                return redirect('create_sale')

            invoice_no = f"INV-{uuid.uuid4().hex[:8].upper()}"

            subtotal = 0
            total_tax = 0
            items_data = []
            for key, value in request.POST.items():
                if key.startswith('items['):
                    index = key.split('[')[1].split(']')[0]
                    field = key.split(']')[1][1:]
                    if not any(d['index'] == index for d in items_data):
                        items_data.append({'index': index})
                    for d in items_data:
                        if d['index'] == index:
                            d[field] = value

            for item_data in items_data:
                item = ItemBase.objects.get(id=item_data['item_id'])
                quantity = int(item_data['quantity'])
                discount = float(item_data.get('discount', 0))
                # Clean gst_rate by removing non-numeric characters (e.g., "%")
                gst_rate = float(re.sub(r'[^0-9.]', '', item.gst_rate)) if item.gst_rate else 0
                amount = (quantity * float(item.sale_price) - discount) * (1 + gst_rate / 100)
                tax_amount = (quantity * float(item.sale_price) - discount) * (gst_rate / 100)
                subtotal += quantity * float(item.sale_price) - discount
                total_tax += tax_amount
                item_data['amount'] = amount
                item_data['tax_amount'] = tax_amount

                # Stock deduction for Product items
                if item.item_type == 'product':
                    product = Product.objects.get(id=item.id)
                    if product.opening_stock < quantity:
                        raise ValidationError(f"Insufficient stock for {item.item_name}")
                    product.opening_stock -= quantity
                    product.save()

            total_amount = subtotal - float(discount) + float(additional_charges) + total_tax
            balance_amount = total_amount - float(amount_received)

            sale = Sale(
                invoice_no=invoice_no,
                party_name=party_name,
                party_email=party_email or None,
                party_phone=party_phone or None,
                party_address=party_address or None,
                invoice_date=invoice_date,
                due_date=due_date or None,
                payment_terms=payment_terms,
                subtotal=subtotal,
                total_tax=total_tax,
                discount=discount,
                additional_charges=additional_charges,
                total_amount=total_amount,
                amount_received=amount_received,
                balance_amount=balance_amount,
                notes=notes,
                terms_conditions=terms_conditions,
                signature=signature,
                user=admin_user
            )
            sale.full_clean()
            sale.save()

            for item_data in items_data:
                sale_item = SaleItem(
                    sale=sale,
                    item_id=item_data['item_id'],
                    quantity=item_data['quantity'],
                    discount=item_data['discount'],
                    tax_amount=item_data['tax_amount'],
                    amount=item_data['amount']
                )
                sale_item.full_clean()
                sale_item.save()

            messages.success(request, "Sale created successfully!")
            if action == "save_new":
                return redirect('create_sale')
            return redirect('sale_list')

        except ValidationError as e:
            # Handle both error_dict and messages
            if hasattr(e, 'error_dict'):
                for field, errors in e.error_dict.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
            else:
                messages.error(request, str(e))
            return redirect('create_sale')
        except Exception as e:
            messages.error(request, f"Error creating sale: {str(e)}")
            return redirect('create_sale')

    context = {
        'add': admin_user,
        'items': items,
        'invoice_no': f"INV-{uuid.uuid4().hex[:8].upper()}"
    }
    return render(request, 'create_sale.html', context)
#........///// Sales \\\\\ ......#
def SalesVw(request):
    return render(request,'Sales.html')
    
    