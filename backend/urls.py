from django.urls import path
from backend import views 
urlpatterns=[

    #..... Admin Login ......# 
    path('',views.Admin_loginVW,name='admin_login'),

    #..... Logout ......#
    path('logout/', views.logout_view, name='logout'),

    #..... Change_Password......#
    path('change_pass',views.ChangePasswordVw,name="change_pass"),
    

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

    # Url for Tenant Switching used for superadmin only to view other pages by setting tenant_id
    path('set-tenant-context/<int:tenant_id>/', views.set_tenant_context, name='set_tenant_context'),
    path('clear-tenant-context/', views.clear_tenant_context, name='clear_tenant_context'),

    path('tenants/toggle-status/<int:tenant_id>/', views.toggle_tenant_status, name='toggle_tenant_status'),
    #..... Admin dash ......# 
    path('dash',views.DashVw,name='dash'),

    #..... Print ......# 
    path('print',views.printVw,name='print'),


    #.....Party_Views......#
    path('Party_list',views.Party_listVw,name="Party_list"),
    #.....update_party......#
    path('update_party/<id>',views.Updt_Party_List,name="update_party"),
    #.....delete_party......#
    path('delete_party/<id>',views.Dlt_Party_ListVw,name="delete_party"),
    #.....create_party......#
    path('Create_party',views.Create_partyVw,name="Create_party"),
    path('party/view/<int:party_id>/', views.party_detail_view, name='party_detail'),

    #.....Item_Url......#
        #.....create_item......#
    path('Create_item',views.create_item_view,name="Create_item"),
    # path('Item_list',views.Item_listVw,name="Item_list"),
    path('Item_list/', views.item_list_view, name='Item_list'),
    path('item/update/<int:item_id>/', views.update_item_view, name='update_item'),
    path('item/delete/<int:item_id>/', views.delete_item_view, name='delete_item'),
    path('item/toggle-status/<int:item_id>/', views.toggle_item_status, name='toggle_item_status'),
    # path('item/update/<int:id>/', lambda x, id: None, name='update_item'),


    
    # Get Tenant Data 
    path('api/get_tenant_data/<int:tenant_id>/', views.get_tenant_data_for_sale_form, name='get_tenant_data'),
    # path('sale_list/', lambda x: None, name='sale_list'),
    

    #.....Sales URL......#
    #.....create_sale......#
    path('Create_Sale',views.create_sale_view,name="Create_Sale"),
    path('sales_list/', views.sales_list, name='sales_list'),
    path('sale/<int:sale_id>/edit/', views.edit_sale_view, name='edit_sale'),
    path('sales/delete/<int:sale_id>/', views.delete_sale, name='delete_sale'),
    path('sales/print/<int:sale_id>/', views.sale_invoice_pdf, name='sale_invoice_pdf'),
    path('sales/view/<int:sale_id>/', views.sale_detail_view, name='sale_detail'),
    path('sales/record_payment/<int:sale_id>/', views.record_payment, name='record_payment'),
    path('reports/sales/', views.sales_report_view, name='sales_report'),

    #--------add_unit---------#
    path('add-unit', views.add_unit, name='add_unit'),

    #--------add_category---------#
    path('add_category', views.add_category, name='add_category'),

    # Activity Logs
    path('logs/all/', views.all_activity_logs_view, name='all_activity_logs'),
    path('logs/financial/', views.financial_logs_view, name='financial_logs'),

    # API Endpoints for Chart Data
    path('api/superadmin/analytics/', views.superadmin_analytics_api, name='superadmin_analytics_api'),
    # Impersonation Mode
    path('impersonate/start/<int:account_id>/', views.impersonate_start, name='impersonate_start'),
    path('impersonate/stop/', views.impersonate_stop, name='impersonate_stop'),

    # Profile URL
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),


    # Purchase url
    path('purchase/create/', views.create_purchase_view, name='create_purchase'),
    path('purchases/', views.purchase_list_view, name='purchase_list'),
    path('api/get_purchase_data/<int:tenant_id>/', views.get_purchase_data_for_form, name='get_purchase_data'),
    path('purchase/<int:purchase_id>/', views.view_purchase, name='view_purchase'),
    path('purchase/<int:purchase_id>/edit/', views.edit_purchase_view, name='edit_purchase'),
    path('purchase/<int:purchase_id>/delete/', views.delete_purchase, name='delete_purchase'),
    path('purchase/<int:purchase_id>/pdf/', views.purchase_pdf, name='purchase_pdf'),
    path('purchase/<int:purchase_id>/update-status/', views.update_purchase_status, name='update_purchase_status'),
    path('purchase/<int:purchase_id>/add-payment/', views.add_purchase_payment, name='add_purchase_payment'),
    path('payment/<int:payment_id>/delete/', views.delete_purchase_payment, name='delete_purchase_payment'),
    path('purchase/<int:purchase_id>/return/', views.create_purchase_return, name='create_purchase_return'),
    path('purchase/update-status/<int:purchase_id>/', views.update_purchase_status_inline, name='update_purchase_status_inline'),

    # Vendor Performance url
    path('vendors/performance/', views.vendor_performance_view, name='vendor_performance'),

    # Stock Adjustments url
    path('stock-adjustments/', views.stock_adjustment_list, name='stock_adjustment_list'),
    path('stock-adjustments/new/', views.create_stock_adjustment, name='create_stock_adjustment'),
    path('api/get-products/<int:tenant_id>/', views.get_products_for_tenant_api, name='api_get_products_for_tenant'),
    path('reports/inventory/', views.inventory_report_view, name='inventory_report'),
    

    # Expenses Url
    path('expenses/', views.expense_list, name='expense_list'),
    path('expenses/new/', views.create_expense, name='create_expense'),
    path('expenses/<int:pk>/edit/', views.edit_expense, name='edit_expense'),
    path('expenses/<int:pk>/delete/', views.delete_expense, name='delete_expense'),
    path('expenses/category/add/', views.add_expense_category, name='add_expense_category'),
    path('api/get-expense-categories/<int:tenant_id>/', views.get_expense_categories_api, name='api_get_expense_categories'),

    # Settings Url
    path('settings/', views.settings_view, name='settings'),

    
]