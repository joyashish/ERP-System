from django.urls import path
from backend import views 
urlpatterns=[

    # Super Admin Dashboard
    path('superadmin_dashboard/', views.superadmin_dashboard, name='superadmin_dashboard'),

    # Create Tenant/ Company
    path('create_tenant/', views.create_tenant, name='create_tenant'),
    # Edit Tenant
    path('edit_tenant/<int:tenant_id>/', views.edit_tenant, name='edit_tenant'),
    # Delete Tenant
    path('delete_tenant/<int:tenant_id>/', views.delete_tenant, name='delete_tenant'),
    # Manage Accounts
    path('manage_accounts/<int:tenant_id>/', views.manage_accounts, name='manage_accounts'),

    # --- NEW URLS FOR ACCOUNT MANAGEMENT ---
    path('accounts/add/<int:tenant_id>/', views.add_account, name='add_account'),
    path('accounts/delete/<int:account_id>/', views.delete_account, name='delete_account'),
    path('accounts/edit/<int:account_id>/', views.edit_account, name='edit_account'),
    #..... Admin dash ......# 
    path('dash',views.DashVw,name='dash'),

    #..... Print ......# 
    path('print',views.printVw,name='print'),

    #..... Admin Login ......# 
    path('',views.Admin_loginVW,name='admin_login'),

    #..... Logout ......#
    path('logout',views.logout,name='logout'),

    #..... Change_Password......#
    path('change_pass',views.ChangePasswordVw,name="change_pass"),

    #.....Party_list......#
    path('Party_list',views.Party_listVw,name="Party_list"),

    #.....update_party......#
    path('update_party/<id>',views.Updt_Party_List,name="update_party"),

    #.....delete_party......#
    path('delete_party/<id>',views.Dlt_Party_ListVw,name="delete_party"),

    #.....create_party......#
    path('Create_party',views.Create_partyVw,name="Create_party"),

    #.....Item_list......#
    # path('Item_list',views.Item_listVw,name="Item_list"),
    path('Item_list/', views.item_list_view, name='Item_list'),
    path('item/update/<int:id>/', lambda x, id: None, name='update_item'),
    path('item/delete/<int:id>/', lambda x, id: None, name='delete_item'),


    #.....create_item......#
    path('Create_item',views.create_item_view,name="Create_item"),

    #.....create_sale......#
    path('Create_Sale',views.create_sale_view,name="Create_Sale"),
    # Get Tenant Data 
    path('api/get_tenant_data/<int:tenant_id>/', views.get_tenant_data_for_sale_form, name='get_tenant_data'),
    path('sale_list/', lambda x: None, name='sale_list'),
    

    #.....Sales......#
    path('sales_list/', views.sales_list, name='sales_list'),
    path('sale/<int:sale_id>/edit/', views.edit_sale_view, name='edit_sale'),
    path('sales/delete/<int:sale_id>/', views.delete_sale, name='delete_sale'),
    path('sales/print/<int:sale_id>/', views.sale_invoice_pdf, name='sale_invoice_pdf'),
    path('sales/view/<int:sale_id>/', views.sale_detail_view, name='sale_detail'),
    path('sales/record_payment/<int:sale_id>/', views.record_payment, name='record_payment'),

    #--------add_unit---------#
    path('add-unit', views.add_unit, name='add_unit'),

    #--------add_category---------#
    path('add_category', views.add_category, name='add_category'),
    
]