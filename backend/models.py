from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.db.models import Sum
from datetime import timedelta
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
    last_login = models.DateTimeField(blank=True, null=True)
    @property
    def is_authenticated(self):
        """
        Always return True for an active user instance.
        This is a required property for Django's auth system.
        """
        return True

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

    # NEW: Add these properties for vendor performance
    @property
    def total_purchase_volume(self):
        """Calculates the total value of all purchases from this vendor."""
        return self.purchase_set.aggregate(total=Sum('total_amount'))['total'] or 0

    @property
    def successful_deliveries(self):
        """Counts how many purchases have been fully received."""
        return self.purchase_set.filter(status='RECEIVED').count()

    @property
    def pending_orders(self):
        """Counts purchases that are ordered but not yet received or cancelled."""
        return self.purchase_set.filter(status__in=['ORDERED', 'PARTIALLY_RECEIVED']).count()

    @property
    def return_rate(self):
        """Calculates the percentage of items returned against items received."""
        # Get total purchased items
        total_purchased_items = PurchaseItem.objects.filter(
            purchase__vendor=self
        ).aggregate(total=Sum('quantity'))['total'] or 0
        
        # Get total returned items
        total_returned_items = PurchaseReturnItem.objects.filter(
            purchase_item__purchase__vendor=self
        ).aggregate(total=Sum('quantity'))['total'] or 0
        
        if total_purchased_items == 0:
            return 0
        return (total_returned_items / total_purchased_items) * 100

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
    service_start_date = models.DateField(null=True, blank=True, help_text="The date the service validity begins.")

    @property
    def is_in_service_period(self):
        """Checks if the service period has started."""
        if not self.service_start_date:
            return False # Not in service if no start date is set
        
        today = timezone.now().date()
        return today >= self.service_start_date

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

# Payment Represents payment made on sale
class Payment(models.Model):
    """Represents a single payment made towards a sale."""
    PAYMENT_MODES = (
        ('CASH', 'Cash'),
        ('BANK', 'Bank Transfer'),
        ('UPI', 'UPI'),
        ('CARD', 'Card'),
        ('OTHER', 'Other'),
    )

    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='payments')
    payment_date = models.DateField(default=timezone.now)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_mode = models.CharField(max_length=10, choices=PAYMENT_MODES, default='CASH')
    notes = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True)

# Activity Log 
class ActivityLog(models.Model):
    """Stores a record of user activities across the platform."""

    class ActionTypes(models.TextChoices):
        # User Management
        USER_LOGGED_IN = 'LOGIN', 'User Logged In'
        TENANT_CREATED = 'TENANT_ADD', 'Tenant Created'
        ACCOUNT_CREATED = 'ACC_ADD', 'Account Created'
        ACCOUNT_EDITED = 'ACC_EDIT', 'Account Edited'

        # Impersonat start and stop
        IMPERSONATE_START = 'IMP_START', 'Impersonation Started'
        IMPERSONATE_STOP = 'IMP_STOP', 'Impersonation Stopped'
        
        # Data Management
        PARTY_CREATED = 'PARTY_ADD', 'Party Created'
        PARTY_EDITED = 'PARTY_EDIT', 'Party Edited'
        PARTY_DELETED = 'PARTY_DEL', 'Party Deleted'
        ITEM_CREATED = 'ITEM_ADD', 'Item Created'
        
        # Financial Transactions
        SALE_CREATED = 'SALE_ADD', 'Sale Created'
        SALE_EDITED = 'SALE_EDIT', 'Sale Edited'
        SALE_DELETED = 'SALE_DEL', 'Sale Deleted'
        PAYMENT_RECORDED = 'PAY_ADD', 'Payment Recorded'

    class LogCategories(models.TextChoices):
        GENERAL = 'GENERAL', 'General'
        FINANCIAL = 'FINANCIAL', 'Financial'
        AUTH = 'AUTH', 'Authentication'

    # ... (actor, action_type, details, tenant, timestamp fields remain the same)
    actor = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True)
    action_type = models.CharField(max_length=10, choices=ActionTypes.choices)
    details = models.TextField()
    tenant = models.ForeignKey(Tenant, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # --- ADD THIS NEW FIELD ---
    category = models.CharField(max_length=10, choices=LogCategories.choices, default=LogCategories.GENERAL)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        # ... (__str__ method remains the same)
        pass


# Purchase Model
class Purchase(models.Model):
    class PurchaseStatus(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        ORDERED = 'ORDERED', 'Ordered'
        PARTIALLY_RECEIVED = 'PARTIALLY_RECEIVED', 'Partially Received'
        RECEIVED = 'RECEIVED', 'Received'
        CANCELLED = 'CANCELLED', 'Cancelled'
        PARTIALLY_RETURNED = 'PARTIALLY_RETURNED', 'Partially Returned'
        FULLY_RETURNED = 'FULLY_RETURNED', 'Fully Returned'
    
    vendor = models.ForeignKey(Create_party, on_delete=models.CASCADE, related_name='purchases')
    bill_number = models.CharField(max_length=50, blank=True, null=True)
    purchase_date = models.DateField(default=timezone.now)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    notes = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=PurchaseStatus.choices, default=PurchaseStatus.ORDERED)
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='purchases')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-purchase_date']

    def __str__(self):
        return f"Purchase from {self.vendor.party_name} on {self.purchase_date}"
    
    # --- UPDATED can_change_status ---
    def can_change_status(self, new_status):
        """
        Defines the allowed MANUAL status changes.
        Return statuses are automatic and cannot be set manually.
        """
        # These are statuses that can be set manually by the user
        MANUAL_STATUSES = [
            self.PurchaseStatus.DRAFT,
            self.PurchaseStatus.ORDERED,
            self.PurchaseStatus.PARTIALLY_RECEIVED,
            self.PurchaseStatus.RECEIVED,
            self.PurchaseStatus.CANCELLED,
        ]

        # Prevent setting automatic statuses manually
        if new_status in [self.PurchaseStatus.FULLY_RETURNED, self.PurchaseStatus.PARTIALLY_RETURNED]:
            return False

        # Define the allowed flow between manual statuses
        status_flow = {
            'DRAFT': ['ORDERED', 'CANCELLED'],
            'ORDERED': ['PARTIALLY_RECEIVED', 'RECEIVED', 'CANCELLED'],
            'PARTIALLY_RECEIVED': ['RECEIVED', 'CANCELLED'],
            'RECEIVED': ['CANCELLED'],
            # Once returned, the status is managed automatically by returns, not manually
            'PARTIALLY_RETURNED': ['CANCELLED'], 
            'FULLY_RETURNED': [], # Cannot manually change from Fully Returned
            'CANCELLED': []
        }
        return new_status in status_flow.get(self.status, [])

    # --- UPDATED update_status_after_return ---
    def update_status_after_return(self, changed_by_user):
        """
        Automatically updates the purchase status after a return and
        records this change in the status history.
        """
        total_purchased_qty = self.items.aggregate(total=Sum('quantity'))['total'] or 0
        total_returned_qty = self.returns.aggregate(total=Sum('items__quantity'))['total'] or 0

        if total_returned_qty == 0:
            return # No returns, no status change needed

        old_status = self.status
        new_status = None

        if total_returned_qty >= total_purchased_qty:
            new_status = self.PurchaseStatus.FULLY_RETURNED
        elif total_returned_qty > 0:
            new_status = self.PurchaseStatus.PARTIALLY_RETURNED
        
        # Only save and create history if the status has actually changed
        if new_status and new_status != old_status:
            self.status = new_status
            self.save()
            
            # Create a history record for this automatic change
            PurchaseStatusHistory.objects.create(
                purchase=self,
                old_status=old_status,
                new_status=new_status,
                changed_by=changed_by_user,
                notes="Status automatically updated after processing a return."
            )
    
    def update_stock_on_status_change(self, old_status, new_status):
        """Handle stock changes when status changes"""
        if old_status == 'RECEIVED' and new_status != 'RECEIVED':
            # Reverse stock if moving out of received status
            for item in self.items.all():
                if hasattr(item.item, 'opening_stock'):
                    item.item.opening_stock -= item.quantity
                    item.item.save()
        
        elif new_status == 'RECEIVED' and old_status != 'RECEIVED':
            # Add stock when receiving
            for item in self.items.all():
                if hasattr(item.item, 'opening_stock'):
                    item.item.opening_stock += item.quantity
                    item.item.save()

    # Add this method to your Purchase model
    def update_stock_on_return(self, return_items):
        """Handle stock changes when items are returned"""
        for return_item in return_items:
            if hasattr(return_item.purchase_item.item, 'opening_stock'):
                return_item.purchase_item.item.opening_stock -= return_item.quantity
                return_item.purchase_item.item.save()
    
    @property
    def total_paid(self):
        return self.payments.aggregate(total=Sum('amount'))['total'] or 0

    @property
    def balance_due(self):
        return self.total_amount - self.total_paid

    @property
    def payment_status(self):
        if self.balance_due <= 0:
            return 'PAID'
        elif self.balance_due < self.total_amount:
            return 'PARTIALLY_PAID'
        else:
            return 'UNPAID'

# PurchaseItem Model (unchanged)
class PurchaseItem(models.Model):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(ItemBase, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} of {self.item.item_name} for Purchase {self.purchase.id}"
    
    def clean(self):
        """Validate that quantity and prices are positive"""
        if self.quantity <= 0:
            raise ValidationError("Quantity must be positive.")
        if self.purchase_price <= 0:
            raise ValidationError("Purchase price must be positive.")
        if self.amount <= 0:
            raise ValidationError("Amount must be positive.")
    # these two properties for better return validation
    @property
    def returned_quantity(self):
        """Calculates total quantity of this item returned across all returns for its purchase."""
        return self.purchasereturnitem_set.aggregate(total=Sum('quantity'))['total'] or 0

    @property
    def returnable_quantity(self):
        """Calculates the remaining quantity eligible for return."""
        return self.quantity - self.returned_quantity

# Purchase Status History Model
class PurchaseStatusHistory(models.Model):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='status_history')
    old_status = models.CharField(max_length=20)
    new_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-changed_at']
    
    def __str__(self):
        return f"{self.purchase.bill_number} - {self.old_status} → {self.new_status}"
    
    # FIXED: These methods should be in PurchaseStatusHistory model, not Purchase
    def get_old_status_display(self):
        return dict(Purchase.PurchaseStatus.choices).get(self.old_status, self.old_status)

    def get_new_status_display(self):
        return dict(Purchase.PurchaseStatus.choices).get(self.new_status, self.new_status)

# Purchase Payment Model (unchanged)
class PurchasePayment(models.Model):
    PAYMENT_METHODS = (
        ('CASH', 'Cash'),
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('CHEQUE', 'Cheque'),
        ('UPI', 'UPI'),
        ('CREDIT_CARD', 'Credit Card'),
        ('OTHER', 'Other'),
    )
    
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateField(default=timezone.now)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='CASH')
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"Payment of ₹{self.amount} for {self.purchase.bill_number}"

    def clean(self):
        """Validate that amount is positive"""
        if self.amount <= 0:
            raise ValidationError("Payment amount must be positive.")

# Purchase Return Model
class PurchaseReturn(models.Model):
    RETURN_REASONS = (
        ('DAMAGED', 'Damaged Goods'),
        ('WRONG_ITEM', 'Wrong Item Received'),
        ('QUALITY_ISSUE', 'Quality Issue'),
        ('OVERSTOCKED', 'Overstocked'),
        ('OTHER', 'Other'),
    )
    
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='returns')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='purchase_returns', null=True)
    return_date = models.DateField(default=timezone.now)
    return_reason = models.CharField(max_length=20, choices=RETURN_REASONS)
    total_return_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-return_date']
    
    def __str__(self):
        return f"Return for {self.purchase.bill_number} - {self.return_date}"
    
    def save(self, *args, **kwargs):
        if not self.tenant_id and self.purchase:
            self.tenant = self.purchase.tenant
        super().save(*args, **kwargs)

# Purchase Return Item model
class PurchaseReturnItem(models.Model):
    purchase_return = models.ForeignKey(PurchaseReturn, on_delete=models.CASCADE, related_name='items')
    purchase_item = models.ForeignKey(PurchaseItem, on_delete=models.CASCADE,null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    return_price = models.DecimalField(max_digits=10, decimal_places=2)
    return_amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    def __str__(self):
        return f"{self.quantity} of {self.purchase_item.item.item_name} returned"

    def save(self, *args, **kwargs):
        # Auto-calculate return amount on save
        self.return_amount = self.quantity * self.return_price
        super().save(*args, **kwargs)

    def clean(self):
        # This clean method is now handled more effectively in the view,
        # but it's good practice to keep it for data integrity (e.g., in Django admin).
        if self.quantity <= 0:
            raise ValidationError("Return quantity must be greater than zero.")
        
        # We access returnable_quantity from the related purchase_item
        if self.quantity > self.purchase_item.returnable_quantity:
            raise ValidationError(
                f"Cannot return {self.quantity}. "
                f"Only {self.purchase_item.returnable_quantity} are available to return."
            )

# class Plan(models.Model):
#     name = models.CharField(max_length=100) # e.g., "Trial", "Pro", "Enterprise"
#     price = models.DecimalField(max_digits=10, decimal_places=2)
#     duration_days = models.IntegerField(help_text="Duration of the plan in days. Use 36500 for 'lifetime'.")

# class Subscription(models.Model):
#     tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE)
#     plan = models.ForeignKey(Plan, on_delete=models.PROTECT) # Don't delete a plan if tenants are using it
#     start_date = models.DateField(auto_now_add=True)
#     end_date = models.DateField()
#     is_active = models.BooleanField(default=True)