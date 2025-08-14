from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password
from backend.models import Account

class AccountBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            account = Account.objects.get(email=username)
            if account.is_active and check_password(password, account.password):
                # The 'is_authenticated' property on the model now handles this.
                return account
            return None
        except Account.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            account = Account.objects.get(pk=user_id, is_active=True)
            # The 'is_authenticated' property on the model now handles this.
            return account
        except Account.DoesNotExist:
            return None