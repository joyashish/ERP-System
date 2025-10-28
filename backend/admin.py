from django.contrib import admin
from backend.models import *

# Register your models here so they appear in the admin panel
admin.site.register(Account)
admin.site.register(Tenant)
# --- Create a custom ModelAdmin for Plan to bypass logging ---
@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    
    def log_addition(self, request, object, message):
        """
        This is called when an object is added. We pass (do nothing)
        to prevent the history log from being created.
        """
        pass

    def log_change(self, request, object, message):
        """Disables logging for changes."""
        pass

    def log_deletion(self, request, object, object_repr):
        """Disables logging for deletions."""
        pass