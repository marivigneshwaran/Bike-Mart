from django.contrib import admin
from .models import (
    Bike,
    Customer,
    Vendor,
    Testimonial,
    ContactInquiry,
    ShopSetting,
    Employee,
    BillPayment,
)


@admin.register(Bike)
class BikeAdmin(admin.ModelAdmin):
    list_display = (
        'bike_name',
        'brand',
        'model_year',
        'registration_number',
        'selling_price',
        'status',
        'is_featured',
    )
    list_filter = ('status', 'brand', 'model_year', 'is_featured')
    search_fields = ('bike_name', 'brand', 'registration_number')


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email', 'created_at')
    search_fields = ('name', 'phone', 'email')


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email')
    search_fields = ('name', 'phone')


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'designation', 'salary', 'status', 'created_at')
    list_filter = ('status', 'designation')
    search_fields = ('name', 'phone', 'email')


@admin.register(BillPayment)
class BillPaymentAdmin(admin.ModelAdmin):
    list_display = (
        'bill_no',
        'bill_date',
        'customer',
        'bike',
        'final_price',
        'advance_amount',
        'settlement_type',
        'payment_type',
        'created_at',
    )
    list_filter = ('settlement_type', 'payment_type', 'bill_date')
    search_fields = ('bill_no', 'customer__name', 'bike__bike_name', 'bike__registration_number')


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'email', 'rating', 'is_active', 'created_at')
    list_filter = ('is_active', 'rating')
    search_fields = ('customer_name', 'email')


@admin.register(ContactInquiry)
class ContactInquiryAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email', 'is_contacted', 'created_at')
    list_filter = ('is_contacted',)
    search_fields = ('name', 'phone', 'email')


@admin.register(ShopSetting)
class ShopSettingAdmin(admin.ModelAdmin):
    list_display = ('shop_name', 'owner_name', 'phone', 'email', 'updated_at')