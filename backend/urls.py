from django.urls import path
from backend import views 
urlpatterns=[

    path('superadmin_dashboard/', views.superadmin_dashboard, name='superadmin_dashboard'),
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
    path('sale_list/', lambda x: None, name='sale_list'),
    

    #.....Sales......#
    path('sales_list/', views.sales_list, name='sales_list'),
    path('sale/<int:sale_id>/edit/', views.edit_sale_view, name='edit_sale'),

    #--------add_unit---------#
    path('add-unit', views.add_unit, name='add_unit'),

    #--------add_category---------#
    path('add_category', views.add_category, name='add_category'),
    
]