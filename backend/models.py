from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.utils import timezone

# Create your models here.

#-------------add_unit---------------------------#
class Unit(models.Model):
    name = models.CharField(max_length=100)
    status = models.BooleanField(default=True)

#-------------add_Category---------------------------#
class Category(models.Model):
    cname = models.CharField(max_length=100)
    status = models.BooleanField(default=True)


#--------////////admin login \\\\\\\\\\--------------#
class Admin_login(models.Model):
    email = models.EmailField()
    password = models.CharField(max_length=50)
    phone = models.IntegerField(default=0)
    role = models.CharField(max_length=20,default='user')
    status = models.BooleanField(default=True)

#........//////......create party..........\\\\\\\\\\#  
class Create_party(models.Model): 
    party_name = models.CharField(max_length=255)  # Party Name
    mobile_num = models.CharField(max_length=15)  # Mobile Number
    email = models.EmailField()  # Email
    opening_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Opening Balance
    gst_no = models.CharField(max_length=20, blank=True, null=True)  # GSTIN
    pan_no = models.CharField(max_length=10, blank=True, null=True)  # PAN Number
    party_type = models.CharField(max_length=100)  # Party Type
    party_category = models.CharField(max_length=100)  # Party Category
    billing_address = models.TextField()  # Billing Address
    shipping_address = models.TextField()  # Shipping Address
    credit_period = models.IntegerField(default=0)  # Credit Period
    credit_limit = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Credit Limit
    user_id=models.ForeignKey(Admin_login, on_delete=models.CASCADE,default=1)
    status = models.BooleanField(default=True)


# Create Item Model 
#ItemBase(common fields) is further divided into model(Product and service) 
class ItemBase(models.Model):
    ITEM_TYPES = (
        ('product', 'Product'),
        ('service', 'Service'),
    )
    
    item_name = models.CharField(max_length=255, unique=True)
    item_type = models.CharField(max_length=10, choices=ITEM_TYPES)
    description = models.TextField(blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    gst_rate = models.CharField(max_length=10, blank=True, null=True)
    hsn_sac_code = models.CharField(max_length=20, blank=True, null=True)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    image = models.ImageField(upload_to='items/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)


    def clean(self):
        if self.item_type == 'product' and not isinstance(self, Product):
            raise ValidationError("Item type must be 'product' for Product model")
        elif self.item_type == 'service' and not isinstance(self, Service):
            raise ValidationError("Item type must be 'service' for Service model")

# ItemBase Product part model
class Product(ItemBase):
    unit = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True, blank=True)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    opening_stock = models.PositiveIntegerField(default=0)
    stock_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    batch_number = models.CharField(max_length=50, blank=True, null=True)
    min_stock_level = models.PositiveIntegerField(default=0)

    def clean(self):
        super().clean()
        if self.item_type != 'product':
            raise ValidationError("Item type must be 'product' for Product model")
        
        if self.purchase_price and self.sale_price and self.purchase_price >= self.sale_price:
            raise ValidationError("Sale price must be greater than purchase price")
        if self.expiry_date and self.expiry_date < timezone.now().date():
            raise ValidationError({'expiry_date': 'Expiry date cannot be in the past'})

# ItemBase Service Part model
class Service(ItemBase):
    service_unit = models.CharField(max_length=10, choices=[
        ('HRS', 'Hours'),
        ('DAY', 'Days'),
        ('PCS', 'Pieces'),
        ('UNT', 'Unit')
    ], blank=True, null=True)
    estimated_duration = models.PositiveIntegerField(blank=True, null=True, help_text="Duration in minutes")

    def clean(self):
        super().clean()
        if self.item_type != 'service':
            raise ValidationError("Item type must be 'service' for Service model")

# Sales Model

class Sale(models.Model):
    invoice_no = models.CharField(max_length=20, unique=True)
    party_name = models.CharField(max_length=255)  # New field
    party_email = models.EmailField(blank=True, null=True)  # New field
    party_phone = models.CharField(max_length=15, blank=True, null=True)  # New field
    party_address = models.TextField(blank=True, null=True)  # New field
    invoice_date = models.DateField(default=timezone.now)
    due_date = models.DateField(null=True, blank=True)
    payment_terms = models.CharField(max_length=100, blank=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_tax = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    additional_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    amount_received = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    balance_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    notes = models.TextField(blank=True, null=True)
    terms_conditions = models.TextField(blank=True, null=True)
    signature = models.ImageField(upload_to='signatures/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey('Admin_login', on_delete=models.CASCADE)

    def clean(self):
        if not self.party_name:
            raise ValidationError("Party name is required")
        if self.total_amount < 0:
            raise ValidationError("Total amount cannot be negative")
        if self.amount_received < 0:
            raise ValidationError("Amount received cannot be negative")
        if self.balance_amount < 0:
            raise ValidationError("Balance amount cannot be negative")

class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey('ItemBase', on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField(default=1)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def clean(self):
        if self.quantity <= 0:
            raise ValidationError("Quantity must be greater than zero")
        if self.discount < 0:
            raise ValidationError("Discount cannot be negative")