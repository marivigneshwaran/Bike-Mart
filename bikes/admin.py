from django.contrib import admin
from .models import (
    Bike,
    BikeImage,
    Customer,
    Vendor,
    Testimonial,
    ContactInquiry,
    ShopSetting,
    Employee,
    BillPayment,
)


class BikeImageInline(admin.TabularInline):
    model = BikeImage
    extra = 1


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
    inlines = [BikeImageInline]

@admin.register(BikeImage)
class BikeImageAdmin(admin.ModelAdmin):
    list_display = ('bike', 'caption', 'uploaded_at')
    search_fields = ('bike__bike_name', 'caption')


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


# Make the `test` user read-only in Django admin (can view but not add/change/delete)
_orig_has_add = admin.ModelAdmin.has_add_permission
_orig_has_change = admin.ModelAdmin.has_change_permission
_orig_has_delete = admin.ModelAdmin.has_delete_permission

def _has_add(self, request):
    if request.user.is_authenticated and getattr(request.user, 'username', '') == 'test':
        return False
    return _orig_has_add(self, request)

def _has_change(self, request, obj=None):
    if request.user.is_authenticated and getattr(request.user, 'username', '') == 'test':
        return False
    return _orig_has_change(self, request, obj)

def _has_delete(self, request, obj=None):
    if request.user.is_authenticated and getattr(request.user, 'username', '') == 'test':
        return False
    return _orig_has_delete(self, request, obj)

admin.ModelAdmin.has_add_permission = _has_add
admin.ModelAdmin.has_change_permission = _has_change
admin.ModelAdmin.has_delete_permission = _has_delete