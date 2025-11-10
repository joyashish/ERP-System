from django.db import models

# Contact form model
class SalesInquiry(models.Model):
    """
    Model to store sales inquiries from the public contact form.
    """
    # --- Status Choices ---
    STATUS_NEW = 'NEW'
    STATUS_CONTACTED = 'CONTACTED'
    STATUS_CLOSED = 'CLOSED'
    
    STATUS_CHOICES = [
        (STATUS_NEW, 'New'),
        (STATUS_CONTACTED, 'Contacted'),
        (STATUS_CLOSED, 'Closed'),
    ]

    # --- Database Fields ---
    full_name = models.CharField(max_length=100)
    company_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20, blank=True, null=True) # Optional
    team_size = models.CharField(max_length=50) # Stores the string like "1-10 employees"
    message = models.TextField()
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_NEW)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Inquiry from {self.full_name} at {self.company_name}"

    class Meta:
        # These make it look nice in the admin panel
        verbose_name = "Sales Inquiry"
        verbose_name_plural = "Sales Inquiries"
        ordering = ['-created_at'] # Show newest first