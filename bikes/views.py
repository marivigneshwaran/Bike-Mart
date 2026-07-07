import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q, Sum, Count
from django.utils import timezone
from decimal import Decimal
from django.http import JsonResponse

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
    AuditLog,
)
from .forms import (
    BikeForm,
    BikeImageForm,
    CustomerForm,
    VendorForm,
    EmployeeForm,
    BillPaymentForm,
    ContactInquiryForm,
    TestimonialForm,
    ShopSettingForm,
    SignupForm,
    AdminUserForm,
)

# Helper function to refresh bike status based on invoices
def refresh_bike_status_after_bill_change(bike):
    if not bike:
        return
    has_invoice = BillPayment.objects.filter(bike=bike).exists()
    if has_invoice:
        bike.status = 'sold'
    else:
        bike.status = 'available'
    bike.save()


# Website Views
def home(request):
    shop_settings = ShopSetting.objects.first()
    featured_bikes = Bike.objects.filter(status='available', is_featured=True)[:6]
    testimonials = Testimonial.objects.filter(is_active=True).order_by('-created_at')[:5]
    context = {
        'shop_settings': shop_settings,
        'featured_bikes': featured_bikes,
        'testimonials': testimonials,
    }
    return render(request, 'website/home.html', context)


def about(request):
    shop_settings = ShopSetting.objects.first()
    context = {'shop_settings': shop_settings}
    return render(request, 'website/about.html', context)


def available_bikes(request):
    shop_settings = ShopSetting.objects.first()
    bikes = Bike.objects.filter(status='available').order_by('-created_at')
    context = {
        'shop_settings': shop_settings,
        'bikes': bikes,
    }
    return render(request, 'website/available_bikes.html', context)


def sold_bikes(request):
    shop_settings = ShopSetting.objects.first()
    bikes = Bike.objects.filter(status='sold').order_by('-created_at')
    context = {
        'shop_settings': shop_settings,
        'bikes': bikes,
    }
    return render(request, 'website/sold_bikes.html', context)


def bike_detail(request, pk):
    shop_settings = ShopSetting.objects.first()
    bike = get_object_or_404(Bike, pk=pk)
    context = {
        'shop_settings': shop_settings,
        'bike': bike,
    }
    return render(request, 'website/bike_detail.html', context)


def contact(request):
    shop_settings = ShopSetting.objects.first()
    if request.method == 'POST':
        form = ContactInquiryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your inquiry has been submitted successfully!')
            return redirect('contact')
    else:
        form = ContactInquiryForm()
    context = {
        'shop_settings': shop_settings,
        'form': form,
    }
    return render(request, 'website/contact.html', context)


def add_testimonial_api(request):
    if request.method == 'POST':
        form = TestimonialForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return JsonResponse({'status': 'success', 'message': 'Thank you for your testimonial!'})
        return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)


# Authentication Views
def login_view(request):
    if request.user.is_authenticated:
        return redirect('admin_dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                return redirect('admin_dashboard')
            else:
                messages.error(request, 'Your account is inactive. Please contact admin.')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'panel/login.html')


def logout_view(request):
    logout(request)
    messages.success(request, 'Logged out successfully.')
    return redirect('login')


def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Registration successful! Wait for admin approval.')
            return redirect('login')
    else:
        form = SignupForm()
    return render(request, 'panel/signup.html', {'form': form})


# Dashboard
@login_required(login_url='login')
def admin_dashboard(request):
    total_bikes = Bike.objects.count()
    available_bikes_count = Bike.objects.filter(status='available').count()
    sold_bikes_count = Bike.objects.filter(status='sold').count()
    total_customers = Customer.objects.count()
    total_vendors = Vendor.objects.count()
    active_employees = Employee.objects.filter(status='active').count()
    total_bills = BillPayment.objects.count()
    pending_inquiries = ContactInquiry.objects.filter(is_contacted=False).count()

    sales_amount = BillPayment.objects.aggregate(total=Sum('final_price'))['total'] or Decimal('0.00')
    investment_amount = Bike.objects.aggregate(total=Sum('buying_price'))['total'] or Decimal('0.00')
    balance_amount = BillPayment.objects.aggregate(total=Sum('payable_amount'))['total'] or Decimal('0.00')
    finance_amount = BillPayment.objects.filter(settlement_type='finance').aggregate(total=Sum('finance_amount'))['total'] or Decimal('0.00')
    interest_amount = BillPayment.objects.filter(settlement_type='finance').aggregate(total=Sum('finance_interest_amount'))['total'] or Decimal('0.00')

    profit_amount = Decimal('0.00')
    for bill in BillPayment.objects.all():
        profit_amount += bill.profit_amount

    context = {
        'total_bikes': total_bikes,
        'available_bikes': available_bikes_count,
        'sold_bikes': sold_bikes_count,
        'total_customers': total_customers,
        'total_vendors': total_vendors,
        'active_employees': active_employees,
        'total_bills': total_bills,
        'pending_inquiries': pending_inquiries,
        'sales_amount': sales_amount,
        'investment_amount': investment_amount,
        'profit_amount': profit_amount,
        'balance_amount': balance_amount,
        'finance_amount': finance_amount,
        'interest_amount': interest_amount,
    }
    return render(request, 'panel/dashboard.html', context)


# Bike Management
@login_required(login_url='login')
def bike_list(request):
    query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')

    bikes = Bike.objects.all().order_by('-created_at')

    if query:
        bikes = bikes.filter(
            Q(bike_name__icontains=query) |
            Q(brand__icontains=query) |
            Q(registration_number__icontains=query) |
            Q(vendor__name__icontains=query)
        )

    if status_filter:
        bikes = bikes.filter(status=status_filter)

    return render(request, 'panel/bike_list.html', {'bikes': bikes, 'query': query, 'status_filter': status_filter})


@login_required(login_url='login')
def bike_add(request):
    if request.method == 'POST':
        form = BikeForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Bike added successfully.')
            return redirect('bike_list')
    else:
        form = BikeForm(user=request.user)
    return render(request, 'panel/bike_form.html', {'form': form, 'title': 'Add Bike'})


@login_required(login_url='login')
def bike_edit(request, pk):
    bike = get_object_or_404(Bike, pk=pk)
    if request.method == 'POST':
        form = BikeForm(request.POST, request.FILES, instance=bike, user=request.user)
        if form.is_valid():
            saved_bike = form.save()
            refresh_bike_status_after_bill_change(saved_bike)
            messages.success(request, 'Bike updated successfully.')
            return redirect('bike_list')
    else:
        form = BikeForm(instance=bike, user=request.user)
    return render(request, 'panel/bike_form.html', {'form': form, 'title': 'Edit Bike'})


@login_required(login_url='login')
def bike_delete(request, pk):
    bike = get_object_or_404(Bike, pk=pk)
    if request.method == 'POST':
        bike.delete()
        messages.success(request, 'Bike deleted successfully.')
        return redirect('bike_list')
    return render(request, 'panel/confirm_delete.html', {'object': bike, 'cancel_url': 'bike_list'})


@login_required(login_url='login')
def bike_gallery(request, pk):
    bike = get_object_or_404(Bike, pk=pk)
    images = bike.images.all()

    if request.method == 'POST':
        form = BikeImageForm(request.POST, request.FILES)
        if form.is_valid():
            bike_image = form.save(commit=False)
            bike_image.bike = bike
            bike_image.save()
            messages.success(request, 'Image added to gallery.')
            return redirect('bike_gallery', pk=bike.pk)
    else:
        form = BikeImageForm()

    return render(request, 'panel/bike_gallery.html', {'bike': bike, 'images': images, 'form': form})


@login_required(login_url='login')
def delete_gallery_image(request, pk):
    image = get_object_or_404(BikeImage, pk=pk)
    bike_id = image.bike.id
    if request.method == 'POST':
        image.delete()
        messages.success(request, 'Gallery image deleted.')
    return redirect('bike_gallery', pk=bike_id)


# Vendor Management
@login_required(login_url='login')
def vendor_list(request):
    query = request.GET.get('q', '')
    vendors = Vendor.objects.all().order_by('-id')
    if query:
        vendors = vendors.filter(
            Q(name__icontains=query) |
            Q(phone__icontains=query) |
            Q(email__icontains=query) |
            Q(address__icontains=query) |
            Q(id_proof__icontains=query)
        )
    return render(request, 'panel/vendor_list.html', {'vendors': vendors, 'query': query})


@login_required(login_url='login')
def vendor_add(request):
    if request.method == 'POST':
        form = VendorForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Vendor added successfully.')
            return redirect('vendor_list')
    else:
        form = VendorForm()
    return render(request, 'panel/vendor_form.html', {'form': form, 'title': 'Add Vendor'})


@login_required(login_url='login')
def vendor_edit(request, pk):
    vendor = get_object_or_404(Vendor, pk=pk)
    if request.method == 'POST':
        form = VendorForm(request.POST, request.FILES, instance=vendor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Vendor updated successfully.')
            return redirect('vendor_list')
    else:
        form = VendorForm(instance=vendor)
    return render(request, 'panel/vendor_form.html', {'form': form, 'title': 'Edit Vendor'})


@login_required(login_url='login')
def vendor_delete(request, pk):
    vendor = get_object_or_404(Vendor, pk=pk)
    if request.method == 'POST':
        vendor.delete()
        messages.success(request, 'Vendor deleted successfully.')
        return redirect('vendor_list')
    return render(request, 'panel/confirm_delete.html', {'object': vendor, 'cancel_url': 'vendor_list'})


# Customer Management
@login_required(login_url='login')
def customer_list(request):
    query = request.GET.get('q', '')
    customers = Customer.objects.all().order_by('-created_at')
    if query:
        customers = customers.filter(
            Q(name__icontains=query) |
            Q(phone__icontains=query) |
            Q(email__icontains=query) |
            Q(address__icontains=query)
        )
    return render(request, 'panel/customer_list.html', {'customers': customers, 'query': query})


@login_required(login_url='login')
def customer_add(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Customer added successfully.')
            return redirect('customer_list')
    else:
        form = CustomerForm()
    return render(request, 'panel/customer_form.html', {'form': form, 'title': 'Add Customer'})


@login_required(login_url='login')
def customer_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        form = CustomerForm(request.POST, request.FILES, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Customer updated successfully.')
            return redirect('customer_list')
    else:
        form = CustomerForm(instance=customer)
    return render(request, 'panel/customer_form.html', {'form': form, 'title': 'Edit Customer'})


@login_required(login_url='login')
def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        customer.delete()
        messages.success(request, 'Customer deleted successfully.')
        return redirect('customer_list')
    return render(request, 'panel/confirm_delete.html', {'object': customer, 'cancel_url': 'customer_list'})


# Employee Management
@login_required(login_url='login')
def employee_list(request):
    query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')

    employees = Employee.objects.all().order_by('-created_at')

    if query:
        employees = employees.filter(
            Q(name__icontains=query) |
            Q(phone__icontains=query) |
            Q(email__icontains=query) |
            Q(designation__icontains=query)
        )

    if status_filter:
        employees = employees.filter(status=status_filter)

    return render(
        request, 'panel/employee_list.html', {'employees': employees, 'query': query, 'status_filter': status_filter}
    )


@login_required(login_url='login')
def employee_add(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Employee added successfully.')
            return redirect('employee_list')
    else:
        form = EmployeeForm()
    return render(request, 'panel/employee_form.html', {'form': form, 'title': 'Add Employee'})


@login_required(login_url='login')
def employee_edit(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES, instance=employee)
        if form.is_valid():
            form.save()
            messages.success(request, 'Employee updated successfully.')
            return redirect('employee_list')
    else:
        form = EmployeeForm(instance=employee)
    return render(request, 'panel/employee_form.html', {'form': form, 'title': 'Edit Employee'})


@login_required(login_url='login')
def employee_delete(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        employee.delete()
        messages.success(request, 'Employee deleted successfully.')
        return redirect('employee_list')
    return render(request, 'panel/confirm_delete.html', {'object': employee, 'cancel_url': 'employee_list'})


# Billing & Invoices
@login_required(login_url='login')
def bill_list(request):
    query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    type_filter = request.GET.get('type', '')

    bills = BillPayment.objects.all().order_by('-created_at')

    if query:
        bills = bills.filter(
            Q(bill_no__icontains=query) |
            Q(customer__name__icontains=query) |
            Q(bike__bike_name__icontains=query) |
            Q(bike__registration_number__icontains=query)
        )

    filtered_bills = []
    for b in bills:
        match_status = True
        match_type = True

        if status_filter:
            if status_filter.lower() != b.bill_status.lower():
                match_status = False

        if type_filter:
            if type_filter.lower() != b.payment_type.lower():
                match_type = False

        if match_status and match_type:
            filtered_bills.append(b)

    return render(
        request,
        'panel/bill_list.html',
        {'bills': filtered_bills, 'query': query, 'status_filter': status_filter, 'type_filter': type_filter},
    )


@login_required(login_url='login')
def bill_add(request):
    if request.method == 'POST':
        form = BillPaymentForm(request.POST)
        if form.is_valid():
            bill = form.save()
            refresh_bike_status_after_bill_change(bill.bike)
            messages.success(request, 'Bill generated successfully.')
            return redirect('bill_list')
    else:
        form = BillPaymentForm()
    return render(request, 'panel/bill_form.html', {'form': form, 'title': 'Generate Bill'})


@login_required(login_url='login')
def bill_edit(request, pk):
    bill = get_object_or_404(BillPayment, pk=pk)
    old_bike = bill.bike
    if request.method == 'POST':
        form = BillPaymentForm(request.POST, instance=bill)
        if form.is_valid():
            new_bill = form.save()
            if old_bike != new_bill.bike:
                refresh_bike_status_after_bill_change(old_bike)
            refresh_bike_status_after_bill_change(new_bill.bike)
            messages.success(request, 'Bill updated successfully.')
            return redirect('bill_list')
    else:
        form = BillPaymentForm(instance=bill)
    return render(request, 'panel/bill_form.html', {'form': form, 'title': 'Edit Bill'})


@login_required(login_url='login')
def bill_delete(request, pk):
    bill = get_object_or_404(BillPayment, pk=pk)
    bike = bill.bike
    if request.method == 'POST':
        bill.delete()
        refresh_bike_status_after_bill_change(bike)
        messages.success(request, 'Bill deleted successfully.')
        return redirect('bill_list')
    return render(request, 'panel/confirm_delete.html', {'object': bill, 'cancel_url': 'bill_list'})


@login_required(login_url='login')
def print_invoice(request, pk):
    bill = get_object_or_404(BillPayment, pk=pk)
    shop_settings = ShopSetting.objects.first()
    return render(request, 'panel/invoice_print.html', {'bill': bill, 'shop_settings': shop_settings})


# Shop Settings
@login_required(login_url='login')
def shop_settings_view(request):
    settings_obj = ShopSetting.objects.first()
    if not settings_obj:
        settings_obj = ShopSetting.objects.create()

    if request.method == 'POST':
        form = ShopSettingForm(request.POST, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Shop configurations updated.')
            return redirect('shop_settings')
    else:
        form = ShopSettingForm(instance=settings_obj)
    return render(request, 'panel/shop_setting_form.html', {'form': form})


# User Management
@login_required(login_url='login')
def user_list(request):
    if not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('admin_dashboard')
    users = User.objects.all().order_by('-id')
    return render(request, 'panel/user_list.html', {'users': users})


@login_required(login_url='login')
def user_add(request):
    if not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('admin_dashboard')
    if request.method == 'POST':
        form = AdminUserForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Staff user registered.')
            return redirect('user_list')
    else:
        form = AdminUserForm()
    return render(request, 'panel/user_form.html', {'form': form, 'title': 'Add User'})


@login_required(login_url='login')
def user_edit(request, pk):
    if not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('admin_dashboard')
    target_user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = AdminUserForm(request.POST, instance=target_user)
        if form.is_valid():
            form.save()
            messages.success(request, 'User properties saved.')
            return redirect('user_list')
    else:
        form = AdminUserForm(instance=target_user)
    return render(request, 'panel/user_form.html', {'form': form, 'title': 'Edit User'})


@login_required(login_url='login')
def user_delete(request, pk):
    if not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('admin_dashboard')
    target_user = get_object_or_404(User, pk=pk)
    if target_user == request.user:
        messages.error(request, 'You cannot remove your own active login profile.')
        return redirect('user_list')
    if request.method == 'POST':
        target_user.delete()
        messages.success(request, 'User dropped from application access index.')
        return redirect('user_list')
    return render(request, 'panel/confirm_delete.html', {'object': target_user, 'cancel_url': 'user_list'})


# Audit Logs
@login_required(login_url='login')
def audit_log_list(request):
    if not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('admin_dashboard')

    search = request.GET.get('search', '')
    action = request.GET.get('action', '')
    model_name = request.GET.get('model_name', '')

    logs = AuditLog.objects.all()

    if search:
        logs = logs.filter(
            Q(user__username__icontains=search) |
            Q(model_name__icontains=search) |
            Q(object_repr__icontains=search) |
            Q(ip_address__icontains=search)
        )

    if action:
        logs = logs.filter(action=action)

    if model_name:
        logs = logs.filter(model_name=model_name)

    modules = AuditLog.objects.values_list('model_name', flat=True).distinct()
    return render(
        request, 'panel/audit_log_list.html', {'logs': logs, 'search': search, 'action': action, 'model_name': model_name, 'modules': modules}
    )


# Contact Inquiries List
@login_required(login_url='login')
def contact_inquiry_list(request):
    inquiries = ContactInquiry.objects.all().order_by('-created_at')
    return render(request, 'panel/contact_inquiry_list.html', {'inquiries': inquiries})


@login_required(login_url='login')
def toggle_inquiry_status(request, pk):
    inquiry = get_object_or_404(ContactInquiry, pk=pk)
    inquiry.is_contacted = not inquiry.is_contacted
    inquiry.save()
    messages.success(request, 'Inquiry status updated.')
    return redirect('contact_inquiry_list')


# Custom Rest Framework Endpoint Authentication Stubs
def get_current_user_api(request):
    if request.user.is_authenticated:
        return JsonResponse({'username': request.user.username, 'email': request.user.email, 'is_staff': request.user.is_staff})
    return JsonResponse({'error': 'Not authenticated'}, status=401)