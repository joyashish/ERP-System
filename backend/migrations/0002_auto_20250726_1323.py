from django.db import migrations
from django.contrib.auth.hashers import make_password

def forwards_func(apps, schema_editor):
    Account = apps.get_model('backend', 'Account')
    Tenant = apps.get_model('backend', 'Tenant')
    
    # Create a superadmin if none exists
    if not Account.objects.filter(role='superadmin').exists():
        Account.objects.create(
            email='superadmin@yourapp.com',
            password=make_password('superadmin123'),
            role='superadmin',
            is_active=True
        )
    
    # Migrate Admin_login data if the table exists
    try:
        Admin_login = apps.get_model('backend', 'Admin_login')
        for admin in Admin_login.objects.all():
            # Create a tenant for each admin
            tenant = Tenant.objects.create(
                name=f"Tenant_{admin.email}",
                subdomain=f"tenant{admin.id}",
                is_active=admin.status if hasattr(admin, 'status') else True
            )
            # Create corresponding Account
            Account.objects.create(
                email=admin.email,
                password=admin.password,  # Assumes password is hashed; adjust if needed
                phone=str(admin.phone) if hasattr(admin, 'phone') else '',
                role=admin.role if hasattr(admin, 'role') else 'admin',
                tenant=tenant,
                is_active=admin.status if hasattr(admin, 'status') else True
            )
    except LookupError:
        # Admin_login model doesn't exist; skip migration
        pass

def backwards_func(apps, schema_editor):
    # Optional: Define reverse migration if needed
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('backend', '0001_initial'),  # Depends on the initial migration
    ]
    operations = [
        migrations.RunPython(forwards_func, backwards_func),
    ]