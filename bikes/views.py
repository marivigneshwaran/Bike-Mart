import json
from decimal import Decimal
from urllib.parse import quote_plus

from django.db.models import Q, Sum, Count
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .serializers import UserSerializer

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
    CustomerIdProofFile,
    VendorIdProofFile,
    EmployeeIdProofFile,
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
    SignupForm,
    AdminUserForm,
)


def get_shop_setting():
    setting = ShopSetting.objects.first()

    if not setting:
        setting = ShopSetting.objects.create()

    return setting


def admin_required(user):
    return user.is_authenticated and user.is_superuser

def superuser_required_redirect(request):
    if not request.user.is_superuser:
        messages.error(request, 'You do not have permission to access this page.')
        return False

    return True


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

            messages.success(
                request,
                'Thank you! Your testimonial has been added successfully.'
            )
            return redirect('home')

    featured_bikes = Bike.objects.filter(
        status='available',
        is_featured=True
    ).order_by('-created_at')[:6]

    available_bikes_preview = Bike.objects.filter(
        status='available'
    ).order_by('-created_at')[:6]

    sold_bikes_preview = Bike.objects.filter(
        status='sold'
    ).order_by('-created_at')[:6]

    testimonials = Testimonial.objects.filter(
        is_active=True
    ).order_by('-created_at')

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
    bikes = Bike.objects.filter(status='available')

    brand = request.GET.get('brand')
    category = request.GET.get('category')
    from_year = request.GET.get('from_year')
    to_year = request.GET.get('to_year')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    if brand:
        bikes = bikes.filter(brand__iexact=brand)

    if category:
        bikes = bikes.filter(category=category)

    if from_year:
        bikes = bikes.filter(model_year__gte=from_year)

    if to_year:
        bikes = bikes.filter(model_year__lte=to_year)

    if min_price:
        bikes = bikes.filter(selling_price__gte=min_price)

    if max_price:
        bikes = bikes.filter(selling_price__lte=max_price)

    bikes = bikes.order_by('-created_at')

    brands = (
        Bike.objects
        .filter(status='available')
        .exclude(brand__isnull=True)
        .exclude(brand__exact='')
        .values_list('brand', flat=True)
        .distinct()
        .order_by('brand')
    )

    years = (
        Bike.objects
        .filter(status='available')
        .values_list('model_year', flat=True)
        .distinct()
        .order_by('-model_year')
    )

    brand_category_rows = (
        Bike.objects
        .filter(status='available')
        .exclude(brand__isnull=True)
        .exclude(brand__exact='')
        .values('brand', 'category')
        .distinct()
    )

    brand_category_map = {}

    for row in brand_category_rows:
        brand_name = row['brand']
        category_value = row['category']

        if brand_name not in brand_category_map:
            brand_category_map[brand_name] = []

        if category_value and category_value not in brand_category_map[brand_name]:
            brand_category_map[brand_name].append(category_value)

    has_filters = any([
        brand,
        category,
        from_year,
        to_year,
        min_price,
        max_price,
    ])

    context = {
        'bikes': bikes,
        'brands': brands,
        'years': years,
        'category_choices': Bike.CATEGORY_CHOICES,
        'brand_category_map': brand_category_map,

        'selected_brand': brand,
        'selected_category': category,
        'selected_from_year': from_year,
        'selected_to_year': to_year,
        'selected_min_price': min_price,
        'selected_max_price': max_price,
        'has_filters': has_filters,
    }

    return render(request, 'website/bikes.html', context)


def sold_bikes(request):
    bikes = Bike.objects.filter(status='sold').order_by('-created_at')
    return render(request, 'website/sold_bikes.html', {'bikes': bikes})


def bike_detail(request, bike_id):
    bike = get_object_or_404(Bike, id=bike_id)

    bike_images = []

    if bike.bike_photo:
        bike_images.append({
            'url': bike.bike_photo.url,
            'caption': bike.bike_name,
        })

    for image in bike.images.all().order_by('uploaded_at'):
        bike_images.append({
            'url': image.image.url,
            'caption': image.caption or bike.bike_name,
        })

    return render(request, 'website/bike_detail.html', {
        'bike': bike,
        'bike_images': bike_images,
    })


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

def signup(request):
    if request.user.is_authenticated:
        return redirect('admin_dashboard')

    form = SignupForm()

    if request.method == 'POST':
        form = SignupForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(
                request,
                'Signup successful. Please wait for admin approval before login.'
            )
            return redirect('admin_login')

    return render(request, 'panel/signup.html', {
        'form': form,
    })


def admin_login(request):
    if request.user.is_authenticated:
        return redirect('admin_dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        inactive_user = User.objects.filter(
            username=username,
            is_active=False
        ).first()

        if inactive_user:
            messages.error(
                request,
                'Your account is created but not approved yet. Please contact admin.'
            )
            return redirect('admin_login')

        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_staff:
            login(request, user)
            return redirect('admin_dashboard')

        messages.error(request, 'Invalid username or password.')

    return render(request, 'panel/login.html')


def create_emergency_admin(request):
    username = "admin"
    email = "marisankar78@gmail.com"
    password = "admin@12345"

    user, created = User.objects.get_or_create(username=username)

    user.email = email
    user.first_name = "Admin"
    user.last_name = "User"
    user.is_staff = True
    user.is_superuser = True
    user.is_active = True
    user.set_password(password)
    user.save()

    messages.success(
        request,
        "Emergency admin user is ready. Username: admin, Password: admin@12345"
    )

    return redirect('admin_login')


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
    available_bikes_queryset = Bike.objects.filter(status='available')

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

    available_stock_value = available_bikes_queryset.aggregate(
        total=Sum('buying_price')
    )['total'] or Decimal('0.00')

    available_expected_sales = available_bikes_queryset.aggregate(
        total=Sum('selling_price')
    )['total'] or Decimal('0.00')

    total_profit = total_sales_amount - sold_invested_amount
    potential_profit = available_expected_sales - available_stock_value

    finance_sales_count = BillPayment.objects.filter(
        settlement_type='finance'
    ).count()

    full_settlement_count = BillPayment.objects.filter(
        settlement_type='full'
    ).count()

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
        'status_chart_data': json.dumps([
            available_bikes_count,
            sold_bikes_count
        ]),
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
        'settlement_chart_data': json.dumps([
            full_settlement_count,
            finance_sales_count
        ]),
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


# Bike CRUD
@login_required
def bike_list(request):
    bikes = Bike.objects.select_related('vendor').all().order_by('-id')

    total_count = bikes.count()

    search = request.GET.get('search')
    status_filter = request.GET.get('status')
    category = request.GET.get('category')

    if search:
        bikes = bikes.filter(
            Q(bike_name__icontains=search) |
            Q(brand__icontains=search) |
            Q(registration_number__icontains=search) |
            Q(vendor__name__icontains=search)
        )

    if status_filter:
        bikes = bikes.filter(status=status_filter)

    if category:
        bikes = bikes.filter(category=category)

    filtered_count = bikes.count()

    return render(request, 'panel/bike_list.html', {
        'bikes': bikes,
        'search': search,
        'status': status_filter,
        'category': category,
        'category_choices': Bike.CATEGORY_CHOICES,
        'total_count': total_count,
        'filtered_count': filtered_count,
    })


@login_required
def bike_create(request):
    form = BikeForm(user=request.user)

    if request.method == 'POST':
        form = BikeForm(request.POST, request.FILES, user=request.user)

        if form.is_valid():
            bike = form.save()

            extra_images = request.FILES.getlist('extra_images')

            for image in extra_images:
                BikeImage.objects.create(
                    bike=bike,
                    image=image
                )

            messages.success(request, 'Bike added successfully.')
            return redirect('bike_list')

    return render(request, 'panel/bike_form.html', {
        'form': form,
        'title': 'Add Bike',
        'bike': None,
    })


@login_required
def bike_update(request, bike_id):
    bike = get_object_or_404(Bike, id=bike_id)
    form = BikeForm(instance=bike, user=request.user)

    if request.method == 'POST':
        form = BikeForm(
            request.POST,
            request.FILES,
            instance=bike,
            user=request.user
        )

        if form.is_valid():
            bike = form.save()

            extra_images = request.FILES.getlist('extra_images')

            for image in extra_images:
                BikeImage.objects.create(
                    bike=bike,
                    image=image
                )

            messages.success(request, 'Bike updated successfully.')
            return redirect('bike_list')

    return render(request, 'panel/bike_form.html', {
        'form': form,
        'title': 'Edit Bike',
        'bike': bike,
    })


@login_required
def bike_image_delete(request, image_id):
    bike_image = get_object_or_404(BikeImage, id=image_id)
    bike_id = bike_image.bike.id

    bike_image.delete()

    messages.success(request, 'Bike image deleted successfully.')
    return redirect('bike_update', bike_id=bike_id)


@login_required
def bike_delete(request, bike_id):
    bike = get_object_or_404(Bike, id=bike_id)
    bike.delete()

    messages.success(request, 'Bike deleted successfully.')
    return redirect('bike_list')


# Customer CRUD
@login_required
def customer_list(request):
    customers = Customer.objects.all().order_by('-id')

    total_count = customers.count()

    search = request.GET.get('search')

    if search:
        customers = customers.filter(
            Q(name__icontains=search) |
            Q(phone__icontains=search) |
            Q(email__icontains=search) |
            Q(address__icontains=search)
        )

    filtered_count = customers.count()

    return render(request, 'panel/customer_list.html', {
        'customers': customers,
        'search': search,
        'total_count': total_count,
        'filtered_count': filtered_count,
    })


@login_required
def customer_create(request):
    form = CustomerForm()

    if request.method == 'POST':
        form = CustomerForm(request.POST, request.FILES)

        if form.is_valid():
            customer = form.save()

            for file in request.FILES.getlist('id_proof_files'):
                CustomerIdProofFile.objects.create(
                    customer=customer,
                    file=file
                )

            messages.success(request, 'Customer added successfully.')
            return redirect('customer_list')

    return render(request, 'panel/customer_form.html', {
        'form': form,
        'title': 'Add Customer',
    })


@login_required
def customer_update(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    form = CustomerForm(instance=customer)

    if request.method == 'POST':
        form = CustomerForm(
            request.POST,
            request.FILES,
            instance=customer
        )

        if form.is_valid():
            customer = form.save()

            for file in request.FILES.getlist('id_proof_files'):
                CustomerIdProofFile.objects.create(
                    customer=customer,
                    file=file
                )

            messages.success(request, 'Customer updated successfully.')
            return redirect('customer_list')

    return render(request, 'panel/customer_form.html', {
        'form': form,
        'title': 'Edit Customer',
    })


@login_required
def customer_delete(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    customer.delete()

    messages.success(request, 'Customer deleted successfully.')
    return redirect('customer_list')


# Vendor CRUD
@login_required
def vendor_list(request):
    vendors = Vendor.objects.all().order_by('-id')

    total_count = vendors.count()

    search = request.GET.get('search')

    if search:
        vendors = vendors.filter(
            Q(name__icontains=search) |
            Q(phone__icontains=search) |
            Q(email__icontains=search) |
            Q(address__icontains=search)
        )

    filtered_count = vendors.count()

    return render(request, 'panel/vendor_list.html', {
        'vendors': vendors,
        'search': search,
        'total_count': total_count,
        'filtered_count': filtered_count,
    })


@login_required
def vendor_create(request):
    form = VendorForm()

    if request.method == 'POST':
        form = VendorForm(request.POST, request.FILES)

        if form.is_valid():
            vendor = form.save()

            for file in request.FILES.getlist('id_proof_files'):
                VendorIdProofFile.objects.create(
                    vendor=vendor,
                    file=file
                )

            messages.success(request, 'Vendor added successfully.')
            return redirect('vendor_list')

    return render(request, 'panel/vendor_form.html', {
        'form': form,
        'title': 'Add Vendor',
    })


@login_required
def vendor_update(request, vendor_id):
    vendor = get_object_or_404(Vendor, id=vendor_id)
    form = VendorForm(instance=vendor)

    if request.method == 'POST':
        form = VendorForm(
            request.POST,
            request.FILES,
            instance=vendor
        )

        if form.is_valid():
            vendor = form.save()

            for file in request.FILES.getlist('id_proof_files'):
                VendorIdProofFile.objects.create(
                    vendor=vendor,
                    file=file
                )

            messages.success(request, 'Vendor updated successfully.')
            return redirect('vendor_list')

    return render(request, 'panel/vendor_form.html', {
        'form': form,
        'title': 'Edit Vendor',
    })


@login_required
def vendor_delete(request, vendor_id):
    vendor = get_object_or_404(Vendor, id=vendor_id)
    vendor.delete()

    messages.success(request, 'Vendor deleted successfully.')
    return redirect('vendor_list')


# Employee CRUD
@login_required
def employee_list(request):
    if not superuser_required_redirect(request):
        return redirect('admin_dashboard')

    employees = Employee.objects.all().order_by('-id')

    total_count = employees.count()

    search = request.GET.get('search')
    status_filter = request.GET.get('status')

    if search:
        employees = employees.filter(
            Q(name__icontains=search) |
            Q(phone__icontains=search) |
            Q(email__icontains=search) |
            Q(designation__icontains=search)
        )

    if status_filter:
        employees = employees.filter(status=status_filter)

    filtered_count = employees.count()

    return render(request, 'panel/employee_list.html', {
        'employees': employees,
        'search': search,
        'status': status_filter,
        'total_count': total_count,
        'filtered_count': filtered_count,
    })


@login_required
def employee_create(request):
    if not superuser_required_redirect(request):
        return redirect('admin_dashboard')

    form = EmployeeForm()

    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES)

        if form.is_valid():
            employee = form.save()

            for file in request.FILES.getlist('id_proof_files'):
                EmployeeIdProofFile.objects.create(
                    employee=employee,
                    file=file
                )

            messages.success(request, 'Employee added successfully.')
            return redirect('employee_list')

    return render(request, 'panel/employee_form.html', {
        'form': form,
        'title': 'Add Employee',
    })


@login_required
def employee_update(request, employee_id):
    if not superuser_required_redirect(request):
        return redirect('admin_dashboard')

    employee = get_object_or_404(Employee, id=employee_id)
    form = EmployeeForm(instance=employee)

    if request.method == 'POST':
        form = EmployeeForm(
            request.POST,
            request.FILES,
            instance=employee
        )

        if form.is_valid():
            employee = form.save()

            for file in request.FILES.getlist('id_proof_files'):
                EmployeeIdProofFile.objects.create(
                    employee=employee,
                    file=file
                )

            messages.success(request, 'Employee updated successfully.')
            return redirect('employee_list')

    return render(request, 'panel/employee_form.html', {
        'form': form,
        'title': 'Edit Employee',
    })


@login_required
def employee_delete(request, employee_id):
    if not superuser_required_redirect(request):
        return redirect('admin_dashboard')

    employee = get_object_or_404(Employee, id=employee_id)
    employee.delete()

    messages.success(request, 'Employee deleted successfully.')
    return redirect('employee_list')


# Billing & Invoices
@login_required
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


@login_required
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


@login_required
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


@login_required
def bill_delete(request, pk):
    bill = get_object_or_404(BillPayment, pk=pk)
    bike = bill.bike
    if request.method == 'POST':
        bill.delete()
        refresh_bike_status_after_bill_change(bike)
        messages.success(request, 'Bill deleted successfully.')
        return redirect('bill_list')
    return render(request, 'panel/confirm_delete.html', {'object': bill, 'cancel_url': 'bill_list'})


@login_required
def print_invoice(request, pk):
    bill = get_object_or_404(BillPayment, pk=pk)
    shop_settings = ShopSetting.objects.first()
    return render(request, 'panel/invoice_print.html', {'bill': bill, 'shop_settings': shop_settings})


# Shop Settings
@login_required
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
@login_required
def user_list(request):
    if not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('admin_dashboard')
    users = User.objects.all().order_by('-id')
    return render(request, 'panel/user_list.html', {'users': users})


@login_required
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


@login_required
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


@login_required
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
@login_required
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
@login_required
def contact_inquiry_list(request):
    inquiries = ContactInquiry.objects.all().order_by('-created_at')
    return render(request, 'panel/contact_inquiry_list.html', {'inquiries': inquiries})


@login_required
def toggle_inquiry_status(request, pk):
    inquiry = get_object_or_404(ContactInquiry, pk=pk)
    inquiry.is_contacted = not inquiry.is_contacted
    inquiry.save()
    messages.success(request, 'Inquiry status updated.')
    return redirect('contact_inquiry_list')


# Custom Rest Framework Endpoints (Restored API Classes)
class CurrentUserAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response({
            'success': True,
            'message': 'User details fetched successfully.',
            'data': serializer.data
        }, status=status.HTTP_200_OK)


class JWTLogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')

        if not refresh_token:
            return Response({
                'success': False,
                'message': 'Refresh token is required.'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response({
                'success': True,
                'message': 'Logout successful. Token blacklisted.'
            }, status=status.HTTP_200_OK)

        except TokenError:
            return Response({
                'success': False,
                'message': 'Invalid or already blacklisted token.'
            }, status=status.HTTP_400_BAD_REQUEST)