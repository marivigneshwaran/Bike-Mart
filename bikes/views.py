import json
from decimal import Decimal
from urllib.parse import quote_plus

from django.db.models import Sum, Count
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
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
from .forms import (
    BikeForm,
    CustomerForm,
    VendorForm,
    ContactInquiryForm,
    TestimonialForm,
    ShopSettingForm,
    EmployeeForm,
    BillPaymentForm,
    AdminUserForm,
)


def get_shop_setting():
    setting = ShopSetting.objects.first()

    if not setting:
        setting = ShopSetting.objects.create()

    return setting

def admin_required(user):
    return user.is_authenticated and user.is_superuser

def refresh_bike_status_after_bill_change(bike):
    if not bike:
        return

    has_bill = BillPayment.objects.filter(bike=bike).exists()

    if has_bill:
        bike.status = 'sold'
    else:
        bike.status = 'available'

    bike.save()


# -------------------------
# Public Website Views
# -------------------------

def home(request):
    testimonial_form = TestimonialForm()

    if request.method == 'POST' and request.POST.get('form_type') == 'testimonial_form':
        testimonial_form = TestimonialForm(request.POST)
        if testimonial_form.is_valid():
            testimonial = testimonial_form.save(commit=False)
            testimonial.is_active = True
            testimonial.save()
            messages.success(request, 'Thank you! Your testimonial has been added successfully.')
            return redirect('home')

    featured_bikes = Bike.objects.filter(status='available', is_featured=True).order_by('-created_at')[:6]
    available_bikes_preview = Bike.objects.filter(status='available').order_by('-created_at')[:6]
    sold_bikes_preview = Bike.objects.filter(status='sold').order_by('-created_at')[:6]
    testimonials = Testimonial.objects.filter(is_active=True).order_by('-created_at')

    available_count = Bike.objects.filter(status='available').count()
    sold_count = Bike.objects.filter(status='sold').count()
    total_bikes = Bike.objects.count()

    context = {
        'featured_bikes': featured_bikes,
        'available_bikes_preview': available_bikes_preview,
        'sold_bikes_preview': sold_bikes_preview,
        'testimonials': testimonials,
        'testimonial_form': testimonial_form,
        'available_count': available_count,
        'sold_count': sold_count,
        'total_bikes': total_bikes,
    }

    return render(request, 'website/home.html', context)


def about(request):
    return render(request, 'website/about.html')


def available_bikes(request):
    bikes = Bike.objects.filter(status='available').order_by('-created_at')
    return render(request, 'website/bikes.html', {'bikes': bikes})


def sold_bikes(request):
    bikes = Bike.objects.filter(status='sold').order_by('-created_at')
    return render(request, 'website/sold_bikes.html', {'bikes': bikes})


def bike_detail(request, bike_id):
    bike = get_object_or_404(Bike, id=bike_id)
    return render(request, 'website/bike_detail.html', {'bike': bike})


def contact(request):
    shop_setting = get_shop_setting()
    form = ContactInquiryForm()

    if request.method == 'POST':
        form = ContactInquiryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your inquiry has been submitted successfully.')
            return redirect('contact')

    map_query = quote_plus(shop_setting.map_location or shop_setting.address)

    context = {
        'form': form,
        'shop_setting': shop_setting,
        'map_query': map_query,
    }

    return render(request, 'website/contact.html', context)


# -------------------------
# Login / Logout
# -------------------------

def admin_login(request):
    if request.user.is_authenticated:
        return redirect('admin_dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_staff:
            login(request, user)
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'panel/login.html')


@login_required
def admin_logout(request):
    logout(request)
    return redirect('home')


# -------------------------
# Admin Dashboard
# -------------------------

@login_required
def admin_dashboard(request):
    total_bikes = Bike.objects.count()
    available_bikes_count = Bike.objects.filter(status='available').count()
    sold_bikes_count = Bike.objects.filter(status='sold').count()
    customers_count = Customer.objects.count()
    vendors_count = Vendor.objects.count()
    employees_count = Employee.objects.count()
    inquiries_count = ContactInquiry.objects.count()
    bill_count = BillPayment.objects.count()

    recent_bikes = Bike.objects.order_by('-created_at')[:6]
    recent_bills = BillPayment.objects.order_by('-created_at')[:6]

    sold_bike_ids = BillPayment.objects.values_list('bike_id', flat=True)
    sold_bikes = Bike.objects.filter(id__in=sold_bike_ids)
    available_bikes = Bike.objects.filter(status='available')

    total_invested_amount = Bike.objects.aggregate(
        total=Sum('buying_price')
    )['total'] or Decimal('0.00')

    sold_invested_amount = sold_bikes.aggregate(
        total=Sum('buying_price')
    )['total'] or Decimal('0.00')

    total_sales_amount = BillPayment.objects.aggregate(
        total=Sum('final_price')
    )['total'] or Decimal('0.00')

    total_advance_amount = BillPayment.objects.aggregate(
        total=Sum('advance_amount')
    )['total'] or Decimal('0.00')

    total_payable_amount = BillPayment.objects.aggregate(
        total=Sum('payable_amount')
    )['total'] or Decimal('0.00')

    total_finance_amount = BillPayment.objects.aggregate(
        total=Sum('finance_amount')
    )['total'] or Decimal('0.00')

    total_interest_amount = BillPayment.objects.aggregate(
        total=Sum('finance_interest_amount')
    )['total'] or Decimal('0.00')

    total_amount_include_interest = BillPayment.objects.aggregate(
        total=Sum('total_amount_include_interest')
    )['total'] or Decimal('0.00')

    available_stock_value = available_bikes.aggregate(
        total=Sum('buying_price')
    )['total'] or Decimal('0.00')

    available_expected_sales = available_bikes.aggregate(
        total=Sum('selling_price')
    )['total'] or Decimal('0.00')

    total_profit = total_sales_amount - sold_invested_amount
    potential_profit = available_expected_sales - available_stock_value

    finance_sales_count = BillPayment.objects.filter(settlement_type='finance').count()
    full_settlement_count = BillPayment.objects.filter(settlement_type='full').count()

    brand_data = Bike.objects.values('brand').annotate(
        count=Count('id')
    ).order_by('-count')[:6]

    brand_labels = [item['brand'] for item in brand_data]
    brand_counts = [item['count'] for item in brand_data]

    context = {
        'total_bikes': total_bikes,
        'available_bikes_count': available_bikes_count,
        'sold_bikes_count': sold_bikes_count,
        'customers_count': customers_count,
        'vendors_count': vendors_count,
        'employees_count': employees_count,
        'inquiries_count': inquiries_count,
        'bill_count': bill_count,

        'recent_bikes': recent_bikes,
        'recent_bills': recent_bills,

        'total_invested_amount': total_invested_amount,
        'sold_invested_amount': sold_invested_amount,
        'total_sales_amount': total_sales_amount,
        'total_advance_amount': total_advance_amount,
        'total_payable_amount': total_payable_amount,
        'total_finance_amount': total_finance_amount,
        'total_interest_amount': total_interest_amount,
        'total_amount_include_interest': total_amount_include_interest,
        'available_stock_value': available_stock_value,
        'available_expected_sales': available_expected_sales,
        'total_profit': total_profit,
        'potential_profit': potential_profit,
        'finance_sales_count': finance_sales_count,
        'full_settlement_count': full_settlement_count,

        'status_chart_labels': json.dumps(['Available Bikes', 'Sold Bikes']),
        'status_chart_data': json.dumps([available_bikes_count, sold_bikes_count]),
        'can_view_finance': request.user.is_superuser,

        'finance_chart_labels': json.dumps([
            'Sales Amount',
            'Advance',
            'Payable',
            'Finance Amount',
            'Interest',
            'Profit',
        ]),
        'finance_chart_data': json.dumps([
            float(total_sales_amount),
            float(total_advance_amount),
            float(total_payable_amount),
            float(total_finance_amount),
            float(total_interest_amount),
            float(total_profit),
            
        ]),

        'brand_chart_labels': json.dumps(brand_labels),
        'brand_chart_data': json.dumps(brand_counts),

        'settlement_chart_labels': json.dumps(['Full Settlement', 'Finance']),
        'settlement_chart_data': json.dumps([full_settlement_count, finance_sales_count]),
    }

    return render(request, 'panel/dashboard.html', context)


@login_required
def shop_settings_update(request):
    shop_setting = get_shop_setting()
    form = ShopSettingForm(instance=shop_setting)

    if request.method == 'POST':
        form = ShopSettingForm(request.POST, instance=shop_setting)
        if form.is_valid():
            form.save()
            messages.success(request, 'Shop contact details updated successfully.')
            return redirect('shop_settings_update')

    return render(request, 'panel/shop_settings_form.html', {
        'form': form,
        'title': 'Shop Contact Settings',
    })


# -------------------------
# Bike CRUD
# -------------------------

@login_required
def bike_list(request):
    bikes = Bike.objects.all().order_by('-created_at')
    return render(request, 'panel/bike_list.html', {'bikes': bikes})


@login_required
def bike_create(request):
    form = BikeForm(user=request.user)

    if request.method == 'POST':
        form = BikeForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Bike added successfully.')
            return redirect('bike_list')

    return render(request, 'panel/bike_form.html', {'form': form, 'title': 'Add Bike'})


@login_required
def bike_update(request, bike_id):
    bike = get_object_or_404(Bike, id=bike_id)
    form = BikeForm(instance=bike, user=request.user)

    if request.method == 'POST':
        form = BikeForm(request.POST, request.FILES, instance=bike, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Bike updated successfully.')
            return redirect('bike_list')

    return render(request, 'panel/bike_form.html', {'form': form, 'title': 'Edit Bike'})


@login_required
def bike_delete(request, bike_id):
    bike = get_object_or_404(Bike, id=bike_id)
    bike.delete()
    messages.success(request, 'Bike deleted successfully.')
    return redirect('bike_list')


# -------------------------
# Customer CRUD
# -------------------------

@login_required
def customer_list(request):
    customers = Customer.objects.all().order_by('-created_at')
    return render(request, 'panel/customer_list.html', {'customers': customers})


@login_required
def customer_create(request):
    form = CustomerForm()

    if request.method == 'POST':
        form = CustomerForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Customer added successfully.')
            return redirect('customer_list')

    return render(request, 'panel/customer_form.html', {'form': form, 'title': 'Add Customer'})


@login_required
def customer_update(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    form = CustomerForm(instance=customer)

    if request.method == 'POST':
        form = CustomerForm(request.POST, request.FILES, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Customer updated successfully.')
            return redirect('customer_list')

    return render(request, 'panel/customer_form.html', {'form': form, 'title': 'Edit Customer'})


@login_required
def customer_delete(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    customer.delete()
    messages.success(request, 'Customer deleted successfully.')
    return redirect('customer_list')


# -------------------------
# Vendor CRUD
# -------------------------

@login_required
def vendor_list(request):
    vendors = Vendor.objects.all().order_by('name')
    return render(request, 'panel/vendor_list.html', {'vendors': vendors})


@login_required
def vendor_create(request):
    form = VendorForm()

    if request.method == 'POST':
        form = VendorForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Vendor added successfully.')
            return redirect('vendor_list')

    return render(request, 'panel/vendor_form.html', {'form': form, 'title': 'Add Vendor'})


@login_required
def vendor_update(request, vendor_id):
    vendor = get_object_or_404(Vendor, id=vendor_id)
    form = VendorForm(instance=vendor)

    if request.method == 'POST':
        form = VendorForm(request.POST, request.FILES, instance=vendor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Vendor updated successfully.')
            return redirect('vendor_list')

    return render(request, 'panel/vendor_form.html', {'form': form, 'title': 'Edit Vendor'})


@login_required
def vendor_delete(request, vendor_id):
    vendor = get_object_or_404(Vendor, id=vendor_id)
    vendor.delete()
    messages.success(request, 'Vendor deleted successfully.')
    return redirect('vendor_list')


# -------------------------
# Employee CRUD
# -------------------------

@login_required
def employee_list(request):
    employees = Employee.objects.all().order_by('-created_at')
    return render(request, 'panel/employee_list.html', {'employees': employees})


@login_required
def employee_create(request):
    form = EmployeeForm()

    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Employee added successfully.')
            return redirect('employee_list')

    return render(request, 'panel/employee_form.html', {'form': form, 'title': 'Add Employee'})


@login_required
def employee_update(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)
    form = EmployeeForm(instance=employee)

    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES, instance=employee)
        if form.is_valid():
            form.save()
            messages.success(request, 'Employee updated successfully.')
            return redirect('employee_list')

    return render(request, 'panel/employee_form.html', {'form': form, 'title': 'Edit Employee'})


@login_required
def employee_delete(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)
    employee.delete()
    messages.success(request, 'Employee deleted successfully.')
    return redirect('employee_list')


# -------------------------
# Bill Payment CRUD
# -------------------------

@login_required
def bill_payment_list(request):
    bills = BillPayment.objects.select_related('customer', 'bike').order_by('-created_at')
    return render(request, 'panel/bill_payment_list.html', {'bills': bills})


@login_required
def bill_payment_create(request):
    form = BillPaymentForm()

    available_bikes = Bike.objects.filter(status='available').values(
        'id',
        'selling_price',
    )

    bike_price_data = {
        str(item['id']): float(item['selling_price'])
        for item in available_bikes
    }

    if request.method == 'POST':
        form = BillPaymentForm(request.POST)
        if form.is_valid():
            bill = form.save()
            bill.bike.status = 'sold'
            bill.bike.save()

            messages.success(request, 'Bill payment created successfully.')
            return redirect('bill_payment_list')

    return render(request, 'panel/bill_payment_form.html', {
        'form': form,
        'title': 'Add Bill Payment',
        'bike_price_data': json.dumps(bike_price_data),
    })


@login_required
def bill_payment_update(request, bill_id):
    bill = get_object_or_404(BillPayment, id=bill_id)
    old_bike = bill.bike

    form = BillPaymentForm(instance=bill)

    available_bikes = Bike.objects.filter(status='available').values(
        'id',
        'selling_price',
    )

    current_bike_data = Bike.objects.filter(id=bill.bike.id).values(
        'id',
        'selling_price',
    )

    bike_price_data = {
        str(item['id']): float(item['selling_price'])
        for item in list(available_bikes) + list(current_bike_data)
    }

    if request.method == 'POST':
        form = BillPaymentForm(request.POST, instance=bill)
        if form.is_valid():
            bill = form.save()

            bill.bike.status = 'sold'
            bill.bike.save()

            if old_bike != bill.bike:
                refresh_bike_status_after_bill_change(old_bike)

            messages.success(request, 'Bill payment updated successfully.')
            return redirect('bill_payment_list')

    return render(request, 'panel/bill_payment_form.html', {
        'form': form,
        'title': 'Edit Bill Payment',
        'bike_price_data': json.dumps(bike_price_data),
    })


@login_required
def bill_payment_delete(request, bill_id):
    bill = get_object_or_404(BillPayment, id=bill_id)
    linked_bike = bill.bike
    bill.delete()

    refresh_bike_status_after_bill_change(linked_bike)

    messages.success(request, 'Bill payment deleted successfully.')
    return redirect('bill_payment_list')


@login_required
def bill_payment_print(request, bill_id):
    bill = get_object_or_404(BillPayment, id=bill_id)
    shop_setting = get_shop_setting()

    return render(request, 'panel/bill_invoice.html', {
        'bill': bill,
        'shop_setting': shop_setting,
    })

# -------------------------
# User Management
# -------------------------

@login_required
def user_list(request):
    if not request.user.is_superuser:
        raise PermissionDenied

    users = User.objects.all().order_by('-date_joined')

    return render(request, 'panel/user_list.html', {
        'users': users,
    })


@login_required
def user_create(request):
    if not request.user.is_superuser:
        raise PermissionDenied

    form = AdminUserForm()

    if request.method == 'POST':
        form = AdminUserForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'User created successfully.')
            return redirect('user_list')

    return render(request, 'panel/user_form.html', {
        'form': form,
        'title': 'Add User',
    })


@login_required
def user_update(request, user_id):
    if not request.user.is_superuser:
        raise PermissionDenied

    user_obj = get_object_or_404(User, id=user_id)
    form = AdminUserForm(instance=user_obj)

    if request.method == 'POST':
        form = AdminUserForm(request.POST, instance=user_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'User updated successfully.')
            return redirect('user_list')

    return render(request, 'panel/user_form.html', {
        'form': form,
        'title': 'Edit User',
    })


@login_required
def user_delete(request, user_id):
    if not request.user.is_superuser:
        raise PermissionDenied

    user_obj = get_object_or_404(User, id=user_id)

    if user_obj == request.user:
        messages.error(request, 'You cannot delete your own user account.')
        return redirect('user_list')

    user_obj.delete()
    messages.success(request, 'User deleted successfully.')
    return redirect('user_list')