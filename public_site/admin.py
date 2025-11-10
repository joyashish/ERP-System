from django.contrib import admin

# Register your models here.
from .models import SalesInquiry

@admin.register(SalesInquiry)
class SalesInquiryAdmin(admin.ModelAdmin):
    """
    Customizes how SalesInquiries are shown in the Django admin panel.
    """
    list_display = ('company_name', 'full_name', 'email', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('full_name', 'company_name', 'email', 'message')
    
    # Makes the data read-only in the admin (you shouldn't edit a customer's inquiry)
    readonly_fields = (
        'full_name', 'company_name', 'email', 'phone_number', 
        'team_size', 'message', 'created_at'
    )
    
    # You can still change the 'status'
    fieldsets = (
        ('Inquiry Details', {
            'fields': ('full_name', 'company_name', 'email', 'phone_number', 'team_size', 'message', 'created_at')
        }),
        ('Internal Status', {
            'fields': ('status',)
        }),
    )