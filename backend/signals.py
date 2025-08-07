from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Account, Create_party, Sale, ActivityLog

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Logs when any user successfully logs in."""
    ActivityLog.objects.create(
        actor=user,
        action_type=ActivityLog.ActionTypes.USER_LOGGED_IN,
        details=f"User '{user.email}' logged in.",
        tenant=user.tenant
    )

@receiver(post_save, sender=Create_party)
def log_party_creation(sender, instance, created, **kwargs):
    """Logs when a new party is created."""
    if created: # Only log on creation, not on update
        ActivityLog.objects.create(
            actor=instance.user,
            action_type=ActivityLog.ActionTypes.PARTY_CREATED,
            details=f"Created party '{instance.party_name}'.",
            tenant=instance.tenant
        )

@receiver(post_delete, sender=Sale)
def log_sale_deletion(sender, instance, **kwargs):
    """Logs when a sale is deleted."""
    ActivityLog.objects.create(
        actor=instance.user, # Assumes the user who created it is the one deleting
        action_type=ActivityLog.ActionTypes.SALE_DELETED,
        details=f"Deleted invoice '{instance.invoice_no}'.",
        tenant=instance.tenant
    )

# You can add more receivers here for creating items, sales, etc.