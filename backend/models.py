from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.contrib.auth.hashers import make_password

# Tenant Model
# A Tenant model to represent each organization/customer
class Tenant(models.Model):
    name = models.CharField(max_length=255, unique=True)
    subdomain = models.CharField(max_length=100, unique=True, help_text="Subdomain for tenant-specific access")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

# Account Model (Replaces Admin_login/User)
# A Account model to represent individual users within a tenant, with roles like 'admin' or 'user' and one 'superadmin'.
class Account(models.Model):
    ROLES = (
        ('admin', 'Admin'),
        ('user', 'User'),
    )
    full_name = models.CharField(max_length=255, blank=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    phone = models.CharField(max_length=15, blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLES, default='user')
    tenant = models.ForeignKey('Tenant', on_delete=models.CASCADE, related_name='accounts', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        # Hashes password on creation or when it's updated.
        if self.password and not self.password.startswith('pbkdf2_'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    # --- __str__ METHOD ---
    def __str__(self):
        # Combines user's name and their tenant for a clear representation.
        user_identifier = self.full_name or self.email
        tenant_name = self.tenant.name if self.tenant else 'System Account'
        return f"{user_identifier} ({tenant_name})"

# Unit Model
class Unit(models.Model):
    name = models.CharField(max_length=100)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='units')
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('tenant', 'name')

    def __str__(self):
        return self.name

# Category Model
class Category(models.Model):
    cname = models.CharField(max_length=100)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='categories')
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('tenant', 'cname')

    def __str__(self):
        return self.cname

# Create Party Model
class Create_party(models.Model):
    party_name = models.CharField(max_length=255)
    mobile_num = models.CharField(max_length=15)
    email = models.EmailField()
    opening_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    gst_no = models.CharField(max_length=20, blank=True, null=True)
    pan_no = models.CharField(max_length=10, blank=True, null=True)
    party_type = models.CharField(max_length=100)
    party_category = models.CharField(max_length=100)
    billing_address = models.TextField()
    shipping_address = models.TextField()
    credit_period = models.IntegerField(default=0)
    credit_limit = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='parties')
    user = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='created_parties')
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('tenant', 'party_name', 'email')

    def __str__(self):
        return self.party_name

# ItemBase Model
class ItemBase(models.Model):
    ITEM_TYPES = (
        ('product', 'Product'),
        ('service', 'Service'),
    )
    item_name = models.CharField(max_length=255)
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
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='items')

    class Meta:
        unique_together = ('tenant', 'item_name')
        indexes = [
            models.Index(fields=['tenant', 'item_name']),
        ]

    def clean(self):
        if self.item_type == 'product' and not isinstance(self, Product):
            raise ValidationError("Item type must be 'product' for Product model")
        elif self.item_type == 'service' and not isinstance(self, Service):
            raise ValidationError("Item type must be 'service' for Service model")

# Product Model
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

# Service Model
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

# Sale Model
class Sale(models.Model):
    invoice_no = models.CharField(max_length=20)
    party = models.ForeignKey(Create_party, on_delete=models.CASCADE)
    invoice_date = models.DateField(default=timezone.now)
    due_date = models.DateField(null=True, blank=True)
    payment_terms = models.IntegerField(default=0)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_tax = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    additional_charges = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    additional_charges_note = models.CharField(max_length=255, blank=True, null=True, help_text="Reason for additional charges, e.g., Shipping")
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    amount_received = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    balance_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    notes = models.TextField(blank=True, null=True)
    terms_conditions = models.TextField(blank=True, null=True)
    signature = models.ImageField(upload_to='signatures/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='sales')
    is_draft = models.BooleanField(default=False)

    class Meta:
        unique_together = ('tenant', 'invoice_no')
        indexes = [
            models.Index(fields=['tenant', 'invoice_no']),
        ]

    @property
    def status(self):
        if self.balance_amount <= 0:
            return "PAID"
        elif self.due_date and self.due_date < timezone.now().date():
            return "OVERDUE"
        else:
            return "UNPAID"

    @property
    def due_in_days(self):
        if self.balance_amount <= 0:
            return "-"
        if self.due_date:
            today = timezone.now().date()
            delta = self.due_date - today
            if delta.days < 0:
                return f"{-delta.days} days ago"
            elif delta.days == 0:
                return "Today"
            else:
                return f"in {delta.days} days"
        return "N/A"

    def clean(self):
        if not self.party:
            raise ValidationError("Party is required")
        if self.total_amount < 0:
            raise ValidationError("Total amount cannot be negative")
        if self.amount_received < 0:
            raise ValidationError("Amount received cannot be negative")

# SaleItem Model
class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(ItemBase, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField(default=1)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def clean(self):
        if self.quantity <= 0:
            raise ValidationError("Quantity must be greater than zero")
        if self.discount < 0:
            raise ValidationError("Discount cannot be negative")