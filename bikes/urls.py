from django.urls import path
from . import views

urlpatterns = [
    # Public website
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('available-bikes/', views.available_bikes, name='available_bikes'),
    path('sold-bikes/', views.sold_bikes, name='sold_bikes'),
    path('bike/<int:bike_id>/', views.bike_detail, name='bike_detail'),
    path('contact/', views.contact, name='contact'),

    # Custom admin login
    path('signup/', views.signup, name='signup'),
    path('create-emergency-admin/', views.create_emergency_admin, name='create_emergency_admin'),
    path('login/', views.admin_login, name='admin_login'),
    path('logout/', views.admin_logout, name='admin_logout'),

    # Admin panel
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/shop-settings/', views.shop_settings_update, name='shop_settings_update'),

    # Bike management
    path('admin-dashboard/bikes/', views.bike_list, name='bike_list'),
    path('admin-dashboard/bikes/add/', views.bike_create, name='bike_create'),
    path('admin-dashboard/bikes/edit/<int:bike_id>/', views.bike_update, name='bike_update'),
    path('admin-dashboard/bikes/delete/<int:bike_id>/', views.bike_delete, name='bike_delete'),

    # Customer management
    path('admin-dashboard/customers/', views.customer_list, name='customer_list'),
    path('admin-dashboard/customers/add/', views.customer_create, name='customer_create'),
    path('admin-dashboard/customers/edit/<int:customer_id>/', views.customer_update, name='customer_update'),
    path('admin-dashboard/customers/delete/<int:customer_id>/', views.customer_delete, name='customer_delete'),

    # Vendor management
    path('admin-dashboard/vendors/', views.vendor_list, name='vendor_list'),
    path('admin-dashboard/vendors/add/', views.vendor_create, name='vendor_create'),
    path('admin-dashboard/vendors/edit/<int:vendor_id>/', views.vendor_update, name='vendor_update'),
    path('admin-dashboard/vendors/delete/<int:vendor_id>/', views.vendor_delete, name='vendor_delete'),

    # Employee management
    path('admin-dashboard/employees/', views.employee_list, name='employee_list'),
    path('admin-dashboard/employees/add/', views.employee_create, name='employee_create'),
    path('admin-dashboard/employees/edit/<int:employee_id>/', views.employee_update, name='employee_update'),
    path('admin-dashboard/employees/delete/<int:employee_id>/', views.employee_delete, name='employee_delete'),

    # Bill payment management
    path('admin-dashboard/bill-payments/', views.bill_payment_list, name='bill_payment_list'),
    path('admin-dashboard/bill-payments/add/', views.bill_payment_create, name='bill_payment_create'),
    path('admin-dashboard/bill-payments/edit/<int:bill_id>/', views.bill_payment_update, name='bill_payment_update'),
    path('admin-dashboard/bill-payments/delete/<int:bill_id>/', views.bill_payment_delete, name='bill_payment_delete'),
    path('admin-dashboard/bill-payments/print/<int:bill_id>/', views.bill_payment_print, name='bill_payment_print'),

    # User management
    path('admin-dashboard/users/', views.user_list, name='user_list'),
    path('admin-dashboard/users/add/', views.user_create, name='user_create'),
    path('admin-dashboard/users/edit/<int:user_id>/', views.user_update, name='user_update'),
    path('admin-dashboard/users/delete/<int:user_id>/', views.user_delete, name='user_delete'),
]