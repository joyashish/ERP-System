from django import forms
from .models import Tenant
from backend.models import *


class TenantSettingsForm(forms.ModelForm):
    class Meta:
        model = Tenant
        fields = ['name', 'address', 'phone', 'email', 'gst_number', 'logo', 'bank_name', 'account_holder_name', 'account_no', 'ifsc_code', 'upi_id', 'qr_code'
        # Add new fields here:
            ,'fssai_number', 'cin_number', 'website', 'signature_img']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'gst_number': forms.TextInput(attrs={'class': 'form-control'}),
            'logo': forms.FileInput(attrs={'class': 'form-control-file'}),
            'bank_name': forms.TextInput(attrs={'class': 'form-control'}),
            'account_holder_name': forms.TextInput(attrs={'class': 'form-control'}),
            'account_no': forms.TextInput(attrs={'class': 'form-control'}),
            'ifsc_code': forms.TextInput(attrs={'class': 'form-control'}),
            'upi_id': forms.TextInput(attrs={'class': 'form-control'}),
            'qr_code': forms.FileInput(attrs={'class': 'form-control-file'}),
            'fssai_number': forms.TextInput(attrs={'class': 'form-control'}),
            'cin_number': forms.TextInput(attrs={'class': 'form-control'}),
            'website': forms.TextInput(attrs={'class': 'form-control'}),
            'signature_img': forms.FileInput(attrs={'class': 'form-control-file'}),
        }


class ProductUpdateForm(forms.ModelForm):
    class Meta:
        model = Product
        # Include all fields you want to be editable
        fields = [
            'item_name', 'description', 'unit', 'category', 
            'sale_price', 'purchase_price', 'gst_rate', 'hsn_sac_code',
            'opening_stock', 'stock_date', 'expiry_date', 'batch_number', 'min_stock_level',
            'image'
        ]
        widgets = {
            'stock_date': forms.DateInput(attrs={'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
            # MODIFIED: Set the number of rows for the description field
            'description': forms.Textarea(attrs={'rows': 3}), 
        }

    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)

        # The Unit field is now global, so we don't filter it by tenant.
        # We just fetch all active units.
        self.fields['unit'].queryset = Unit.objects.filter(is_active=True).order_by('name')
        
        # MODIFIED: The Category field is now also global
        self.fields['category'].queryset = Category.objects.filter(is_active=True).order_by('cname')

        # MODIFIED: Set a user-friendly empty label for the category dropdown
        self.fields['category'].empty_label = "Select a Category"
        self.fields['unit'].empty_label = "Select a Unit"

        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'


class ServiceUpdateForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = [
            'item_name', 'description', 'category', 'service_unit', 
            'sale_price', 'gst_rate', 'hsn_sac_code', 'service_start_date',
            'image'
        ]
        widgets = {
            'service_start_date': forms.DateInput(attrs={'type': 'date'}),
            # MODIFIED: Set the number of rows for the description field
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # MODIFIED: The Category field is now also global
        self.fields['category'].queryset = Category.objects.filter(is_active=True).order_by('cname')
            
        # Set a user-friendly empty label for the category dropdown (ForeignKey)
        self.fields['category'].empty_label = "Select a Category"

        # For a ChoiceField, we modify the choices list directly
        # 1. Get the existing choices
        service_unit_choices = list(self.fields['service_unit'].choices)
        # 2. Replace the default empty label with our custom one
        service_unit_choices[0] = ('', 'Select a Unit')
        # 3. Assign the modified list back to the field
        self.fields['service_unit'].choices = service_unit_choices
        
        # --- END OF CORRECTION ---
            
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

class PartyUpdateForm(forms.ModelForm):
    class Meta:
        model = Create_party
        # We will render these fields manually, but listing them is good practice
        fields = [
            'party_name', 'mobile_num', 'email', 'opening_balance',
            'gst_no', 'pan_no', 'party_type', 'party_category',
            'billing_address', 'shipping_address',
            'credit_period', 'credit_limit'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply Bootstrap classes to all visible fields
        for field_name, field in self.fields.items():
            if field_name not in ['billing_address', 'shipping_address']:
                field.widget.attrs.update({'class': 'form-control'})