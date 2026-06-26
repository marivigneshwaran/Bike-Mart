from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from decimal import Decimal


class Vendor(models.Model):
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    id_proof = models.CharField(max_length=100, blank=True, null=True)
    id_proof_file = models.FileField(upload_to='vendor_id_proofs/', blank=True, null=True)
    photo = models.ImageField(upload_to='vendor_photos/', blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Bike(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('sold', 'Sold'),
    ]

    CATEGORY_CHOICES = [
        ('bike', 'Bike'),
        ('scooter', 'Scooter'),
        ('ev', 'EV'),
    ]

    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    bike_name = models.CharField(max_length=150)
    brand = models.CharField(max_length=100)
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='bike'
    )
    model_year = models.IntegerField()
    registration_number = models.CharField(max_length=50, unique=True)
    km_driven = models.PositiveIntegerField()
    fuel_type = models.CharField(max_length=50, default='Petrol')
    ownership = models.CharField(max_length=50, blank=True, null=True)
    buying_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True
    )
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    bike_photo = models.ImageField(
        upload_to='bike_photos/',
        blank=True,
        null=True
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='available'
    )
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.bike_name} - {self.registration_number}"

class BikeImage(models.Model):
    bike = models.ForeignKey(
        Bike,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to='bike_photos/')
    caption = models.CharField(max_length=150, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.bike.bike_name} Image"


class Customer(models.Model):
    bike = models.ForeignKey(Bike, on_delete=models.SET_NULL, null=True, blank=True)

    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    photo = models.ImageField(upload_to='customer_photos/', blank=True, null=True)
    id_proof_file = models.FileField(upload_to='customer_id_proofs/', blank=True, null=True)

    interested_bike = models.CharField(max_length=150, blank=True, null=True)
    purchased = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Employee(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    name = models.CharField(max_length=150)
    age = models.PositiveIntegerField(blank=True, null=True)
    phone = models.CharField(max_length=20)
    alternate_phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    designation = models.CharField(max_length=100, blank=True, null=True)
    salary = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    joining_date = models.DateField(blank=True, null=True)

    photo = models.ImageField(upload_to='employee_photos/', blank=True, null=True)
    id_proof_file = models.FileField(upload_to='employee_id_proofs/', blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class BillPayment(models.Model):
    SETTLEMENT_CHOICES = [
        ('full', 'Full Settlement'),
        ('finance', 'Finance'),
    ]

    PAYMENT_TYPE_CHOICES = [
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('upi', 'UPI'),
    ]

    bill_no = models.CharField(max_length=50, unique=True, blank=True)
    bill_date = models.DateField(default=timezone.now)

    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    bike = models.ForeignKey(Bike, on_delete=models.PROTECT)

    bike_price = models.DecimalField(max_digits=10, decimal_places=2)
    advance_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Amount paid by customer"
    )
    final_price = models.DecimalField(max_digits=10, decimal_places=2)

    payable_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Balance amount after paid amount"
    )

    settlement_type = models.CharField(max_length=20, choices=SETTLEMENT_CHOICES, default='full')

    finance_company_name = models.CharField(max_length=150, blank=True, null=True)
    finance_down_payment = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    finance_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    finance_interest_percentage = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    finance_interest_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    finance_months = models.PositiveIntegerField(blank=True, null=True)
    total_amount_include_interest = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    monthly_emi = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES, default='cash')
    upi_id = models.CharField(max_length=100, blank=True, null=True)

    remarks = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def paid_amount(self):
        return self.advance_amount or Decimal('0.00')

    @property
    def balance_amount(self):
        return self.payable_amount or Decimal('0.00')

    @property
    def bill_status(self):
        if self.settlement_type == 'finance':
            return "Finance"

        if self.balance_amount > 0:
            return "Partial"

        return "Full"

    @property
    def payment_status(self):
        return self.bill_status

    @property
    def profit_amount(self):
        buying_price = self.bike.buying_price or Decimal('0.00')
        final_price = self.final_price or Decimal('0.00')
        return final_price - buying_price

    def save(self, *args, **kwargs):
        zero = Decimal('0.00')

        if not self.bill_no:
            last_bill = BillPayment.objects.order_by('-id').first()
            next_number = 1

            if last_bill:
                next_number = last_bill.id + 1

            self.bill_no = f"INV-{next_number:05d}"

        if not self.bike_price:
            self.bike_price = self.bike.selling_price

        if not self.final_price:
            self.final_price = self.bike_price

        if self.advance_amount is None:
            self.advance_amount = zero

        if self.final_price is None:
            self.final_price = zero

        # advance_amount is used as Paid Amount.
        # payable_amount is used as Balance Amount.
        self.payable_amount = self.final_price - self.advance_amount

        if self.payable_amount < zero:
            self.payable_amount = zero

        if self.settlement_type == 'finance':
            down_payment = self.finance_down_payment or zero
            interest_percentage = self.finance_interest_percentage or zero

            self.finance_amount = self.final_price - down_payment

            if self.finance_amount < zero:
                self.finance_amount = zero

            self.finance_interest_amount = self.finance_amount * interest_percentage / Decimal('100')
            self.total_amount_include_interest = self.finance_amount + self.finance_interest_amount

            if self.finance_months and self.finance_months > 0:
                self.monthly_emi = self.total_amount_include_interest / self.finance_months
            else:
                self.monthly_emi = None
        else:
            self.finance_company_name = None
            self.finance_down_payment = None
            self.finance_amount = None
            self.finance_interest_percentage = None
            self.finance_interest_amount = None
            self.finance_months = None
            self.total_amount_include_interest = None
            self.monthly_emi = None

        if self.payment_type != 'upi':
            self.upi_id = None

        super().save(*args, **kwargs)

    def __str__(self):
        return self.bill_no


class Testimonial(models.Model):
    customer_name = models.CharField(max_length=150)
    email = models.EmailField(blank=True, null=True)
    message = models.TextField()
    rating = models.PositiveIntegerField(default=5)
    photo = models.ImageField(upload_to='testimonials/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.customer_name


class ContactInquiry(models.Model):
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_contacted = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class ShopSetting(models.Model):
    shop_name = models.CharField(max_length=150, default='BikeMart')
    owner_name = models.CharField(max_length=150, default='Mr. Mari Vigneshwaran')
    address = models.TextField(default='Chennai, Tamil Nadu')
    phone = models.CharField(max_length=20, default='+91 98765 43210')
    email = models.EmailField(default='bikemart@example.com')
    working_hours = models.CharField(max_length=100, default='9:00 AM - 8:00 PM')
    map_location = models.CharField(
        max_length=255,
        default='Chennai Tamil Nadu',
        help_text='Enter Google map search location. Example: Tambaram Chennai Tamil Nadu'
    )
    short_description = models.TextField(
        default='Trusted second-hand bike showroom for verified bikes, fair pricing, and easy customer support.'
    )

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.shop_name

    class Meta:
        verbose_name = 'Shop Setting'
        verbose_name_plural = 'Shop Settings'


class AuditLog(models.Model):
    ACTION_CHOICES = (
        ('create', 'Created'),
        ('update', 'Updated'),
        ('delete', 'Deleted'),
        ('login', 'Login'),
        ('logout', 'Logout'),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100, blank=True, null=True)
    object_repr = models.CharField(max_length=255, blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    old_values = models.JSONField(blank=True, null=True)
    new_values = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.model_name} - {self.action}"