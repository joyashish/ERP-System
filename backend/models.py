from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
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

#................./////////........Create_ITEM.............\\\\\\\\\\\\\\\\\\\\#
class Create_item(models.Model):
    ITEM_TYPE_CHOICES = [
        ('product', 'Product'),
        ('service', 'Service'),
    ]

    GST_CHOICES = [
        ('', 'None'),
        ('5%', 'GST@5%'),
        ('12%', 'GST@12%'),
        ('18%', 'GST@18%'),
        ('28%', 'GST@28%'),
    ]

    item_type = models.CharField(max_length=10, choices=ITEM_TYPE_CHOICES, default='product')
    item_name = models.CharField(max_length=255, unique=True)
    unit = models.ForeignKey('Unit', on_delete=models.SET_NULL, null=True, blank=True)  # Changed to string reference
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Made nullable
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    gst = models.CharField(max_length=5, choices=GST_CHOICES, blank=True)
    hsn_sac = models.CharField(max_length=50, blank=True, verbose_name="HSN/SAC Code")
    opening_stock = models.PositiveIntegerField(null=True, blank=True)
    stock_date = models.DateField(null=True, blank=True)
    entry_date = models.DateField(default=timezone.now)
    expiry_date = models.DateField(null=True, blank=True)
    batch_number = models.CharField(max_length=50, blank=True)
    product_image = models.ImageField(upload_to='product_images/', blank=True, null=True)
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True, blank=True)  # Changed to string reference
    item_des = models.TextField(blank=True, verbose_name="Description")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.BooleanField(default=True)

def clean(self):
        if self.item_type == 'product' and not self.sale_price:
            raise ValidationError({'sale_price': 'Sales price is required for products'})
        if self.item_type == 'service' and not self.sale_price:
            raise ValidationError({'sale_price': 'Service price is required for services'})


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