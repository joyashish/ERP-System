# Generated by Django 5.0.6 on 2025-07-26 07:51

import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('password', models.CharField(max_length=128)),
                ('phone', models.CharField(blank=True, max_length=15, null=True)),
                ('role', models.CharField(choices=[('superadmin', 'Superadmin'), ('admin', 'Admin'), ('user', 'User')], default='user', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cname', models.CharField(max_length=100)),
                ('is_active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='ItemBase',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('item_name', models.CharField(max_length=255)),
                ('item_type', models.CharField(choices=[('product', 'Product'), ('service', 'Service')], max_length=10)),
                ('description', models.TextField(blank=True, null=True)),
                ('gst_rate', models.CharField(blank=True, max_length=10, null=True)),
                ('hsn_sac_code', models.CharField(blank=True, max_length=20, null=True)),
                ('sale_price', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(0)])),
                ('image', models.ImageField(blank=True, null=True, upload_to='items/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='backend.category')),
            ],
        ),
        migrations.CreateModel(
            name='Tenant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('subdomain', models.CharField(help_text='Subdomain for tenant-specific access', max_length=100, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='Create_party',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('party_name', models.CharField(max_length=255)),
                ('mobile_num', models.CharField(max_length=15)),
                ('email', models.EmailField(max_length=254)),
                ('opening_balance', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('gst_no', models.CharField(blank=True, max_length=20, null=True)),
                ('pan_no', models.CharField(blank=True, max_length=10, null=True)),
                ('party_type', models.CharField(max_length=100)),
                ('party_category', models.CharField(max_length=100)),
                ('billing_address', models.TextField()),
                ('shipping_address', models.TextField()),
                ('credit_period', models.IntegerField(default=0)),
                ('credit_limit', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('is_active', models.BooleanField(default=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_parties', to='backend.account')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='parties', to='backend.tenant')),
            ],
        ),
        migrations.CreateModel(
            name='Service',
            fields=[
                ('itembase_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='backend.itembase')),
                ('service_unit', models.CharField(blank=True, choices=[('HRS', 'Hours'), ('DAY', 'Days'), ('PCS', 'Pieces'), ('UNT', 'Unit')], max_length=10, null=True)),
                ('estimated_duration', models.PositiveIntegerField(blank=True, help_text='Duration in minutes', null=True)),
            ],
            bases=('backend.itembase',),
        ),
        migrations.CreateModel(
            name='Sale',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('invoice_no', models.CharField(max_length=20)),
                ('invoice_date', models.DateField(default=django.utils.timezone.now)),
                ('due_date', models.DateField(blank=True, null=True)),
                ('payment_terms', models.IntegerField(default=0)),
                ('subtotal', models.DecimalField(decimal_places=2, default=0.0, max_digits=12)),
                ('total_tax', models.DecimalField(decimal_places=2, default=0.0, max_digits=12)),
                ('discount', models.DecimalField(decimal_places=2, default=0.0, max_digits=12)),
                ('additional_charges', models.DecimalField(decimal_places=2, default=0.0, max_digits=12)),
                ('additional_charges_note', models.CharField(blank=True, help_text='Reason for additional charges, e.g., Shipping', max_length=255, null=True)),
                ('total_amount', models.DecimalField(decimal_places=2, default=0.0, max_digits=12)),
                ('amount_received', models.DecimalField(decimal_places=2, default=0.0, max_digits=12)),
                ('balance_amount', models.DecimalField(decimal_places=2, default=0.0, max_digits=12)),
                ('notes', models.TextField(blank=True, null=True)),
                ('terms_conditions', models.TextField(blank=True, null=True)),
                ('signature', models.ImageField(blank=True, null=True, upload_to='signatures/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_draft', models.BooleanField(default=False)),
                ('party', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='backend.create_party')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='backend.account')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sales', to='backend.tenant')),
            ],
        ),
        migrations.CreateModel(
            name='SaleItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('discount', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('tax_amount', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('amount', models.DecimalField(decimal_places=2, default=0.0, max_digits=12)),
                ('item', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='backend.itembase')),
                ('sale', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='backend.sale')),
            ],
        ),
        migrations.AddField(
            model_name='itembase',
            name='tenant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='backend.tenant'),
        ),
        migrations.AddField(
            model_name='category',
            name='tenant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='categories', to='backend.tenant'),
        ),
        migrations.AddField(
            model_name='account',
            name='tenant',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='accounts', to='backend.tenant'),
        ),
        migrations.CreateModel(
            name='Unit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('is_active', models.BooleanField(default=True)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='units', to='backend.tenant')),
            ],
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('itembase_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='backend.itembase')),
                ('purchase_price', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(0)])),
                ('opening_stock', models.PositiveIntegerField(default=0)),
                ('stock_date', models.DateField(blank=True, null=True)),
                ('expiry_date', models.DateField(blank=True, null=True)),
                ('batch_number', models.CharField(blank=True, max_length=50, null=True)),
                ('min_stock_level', models.PositiveIntegerField(default=0)),
                ('unit', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='backend.unit')),
            ],
            bases=('backend.itembase',),
        ),
        migrations.AddIndex(
            model_name='sale',
            index=models.Index(fields=['tenant', 'invoice_no'], name='backend_sal_tenant__f3487a_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='sale',
            unique_together={('tenant', 'invoice_no')},
        ),
        migrations.AddIndex(
            model_name='itembase',
            index=models.Index(fields=['tenant', 'item_name'], name='backend_ite_tenant__1df805_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='itembase',
            unique_together={('tenant', 'item_name')},
        ),
        migrations.AlterUniqueTogether(
            name='create_party',
            unique_together={('tenant', 'party_name', 'email')},
        ),
        migrations.AlterUniqueTogether(
            name='category',
            unique_together={('tenant', 'cname')},
        ),
        migrations.AlterUniqueTogether(
            name='unit',
            unique_together={('tenant', 'name')},
        ),
    ]
