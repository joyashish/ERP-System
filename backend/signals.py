from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Account, Tenant, Create_party, Sale, ItemBase, Payment, ActivityLog

# --- AUTHENTICATION LOGS ---
@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    ActivityLog.objects.create(
        actor=user,
        action_type=ActivityLog.ActionTypes.USER_LOGGED_IN,
        details=f"User '{user.email}' logged in.",
        tenant=user.tenant,
        category=ActivityLog.LogCategories.AUTH
    )

# --- GENERAL ACTIVITY LOGS ---
@receiver(post_save, sender=Tenant)
def log_tenant_activity(sender, instance, created, **kwargs):
    if created:
        # Note: The first account is created right after, so actor might be tricky to get here.
        # We can leave it blank or find a way to associate it. For now, it's a system action.
        ActivityLog.objects.create(
            action_type=ActivityLog.ActionTypes.TENANT_CREATED,
            details=f"New tenant '{instance.name}' was created.",
            tenant=instance,
            category=ActivityLog.LogCategories.GENERAL
        )

@receiver(post_save, sender=Account)
def log_account_activity(sender, instance, created, **kwargs):
    if instance.role == 'superadmin': return # Don't log superadmin's own creation/edits
    
    if created:
        ActivityLog.objects.create(
            action_type=ActivityLog.ActionTypes.ACCOUNT_CREATED,
            details=f"New account '{instance.email}' ({instance.get_role_display()}) was created.",
            tenant=instance.tenant,
            category=ActivityLog.LogCategories.GENERAL
        )
    else:
        ActivityLog.objects.create(
            action_type=ActivityLog.ActionTypes.ACCOUNT_EDITED,
            details=f"Account '{instance.email}' was updated.",
            tenant=instance.tenant,
            category=ActivityLog.LogCategories.GENERAL
        )

@receiver(post_save, sender=Create_party)
def log_party_activity(sender, instance, created, **kwargs):
    if created:
        ActivityLog.objects.create(
            actor=instance.user,
            action_type=ActivityLog.ActionTypes.PARTY_CREATED,
            details=f"Created party '{instance.party_name}'.",
            tenant=instance.tenant,
            category=ActivityLog.LogCategories.GENERAL
        )
    else: # Log edits
        ActivityLog.objects.create(
            actor=instance.user,
            action_type=ActivityLog.ActionTypes.PARTY_EDITED,
            details=f"Updated party '{instance.party_name}'.",
            tenant=instance.tenant,
            category=ActivityLog.LogCategories.GENERAL
        )

@receiver(post_save, sender=ItemBase)
def log_item_activity(sender, instance, created, **kwargs):
    # This will catch both Product and Service creations/updates
    if created:
        ActivityLog.objects.create(
            # actor=instance.user, # ItemBase model doesn't have a 'user' field. This can be added.
            action_type=ActivityLog.ActionTypes.ITEM_CREATED,
            details=f"Created {instance.item_type} '{instance.item_name}'.",
            tenant=instance.tenant,
            category=ActivityLog.LogCategories.GENERAL
        )

# --- FINANCIAL LOGS ---
@receiver(post_save, sender=Sale)
def log_sale_activity(sender, instance, created, **kwargs):
    if created:
        ActivityLog.objects.create(
            actor=instance.user,
            action_type=ActivityLog.ActionTypes.SALE_CREATED,
            details=f"Created invoice '{instance.invoice_no}' for {instance.party.party_name} (₹{instance.total_amount}).",
            tenant=instance.tenant,
            category=ActivityLog.LogCategories.FINANCIAL
        )
    else:
        ActivityLog.objects.create(
            actor=instance.user,
            action_type=ActivityLog.ActionTypes.SALE_EDITED,
            details=f"Updated invoice '{instance.invoice_no}'.",
            tenant=instance.tenant,
            category=ActivityLog.LogCategories.FINANCIAL
        )

@receiver(post_delete, sender=Sale)
def log_sale_deletion(sender, instance, **kwargs):
    ActivityLog.objects.create(
        actor=instance.user,
        action_type=ActivityLog.ActionTypes.SALE_DELETED,
        details=f"Deleted invoice '{instance.invoice_no}'.",
        tenant=instance.tenant,
        category=ActivityLog.LogCategories.FINANCIAL
    )

@receiver(post_save, sender=Payment)
def log_payment_activity(sender, instance, created, **kwargs):
    if created:
        ActivityLog.objects.create(
            actor=instance.user,
            action_type=ActivityLog.ActionTypes.PAYMENT_RECORDED,
            details=f"Recorded payment of ₹{instance.amount} for invoice '{instance.sale.invoice_no}'.",
            tenant=instance.sale.tenant,
            category=ActivityLog.LogCategories.FINANCIAL
        )