from django import forms
from django.contrib.auth.models import User

from .models import (
    Bike,
    Customer,
    Vendor,
    ContactInquiry,
    Testimonial,
    ShopSetting,
    Employee,
    BillPayment,
)


class BikeForm(forms.ModelForm):
    class Meta:
        model = Bike
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.user and not self.user.is_superuser:
            self.fields.pop('buying_price', None)


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            'name',
            'phone',
            'email',
            'address',
            'photo',
            'id_proof_file',
            'notes',
        ]


class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = '__all__'


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = '__all__'

        widgets = {
            'joining_date': forms.DateInput(attrs={'type': 'date'}),
        }


class BillPaymentForm(forms.ModelForm):
    class Meta:
        model = BillPayment
        fields = [
            'bill_date',
            'customer',
            'bike',
            'bike_price',
            'advance_amount',
            'final_price',
            'payable_amount',
            'settlement_type',
            'finance_company_name',
            'finance_down_payment',
            'finance_amount',
            'finance_interest_percentage',
            'finance_interest_amount',
            'finance_months',
            'total_amount_include_interest',
            'monthly_emi',
            'payment_type',
            'upi_id',
            'remarks',
        ]

        widgets = {
            'bill_date': forms.DateInput(attrs={'type': 'date'}),
            'remarks': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        selected_bike = None

        if self.instance and self.instance.pk:
            selected_bike = self.instance.bike

        available_bikes = Bike.objects.filter(status='available')

        if selected_bike:
            available_bikes = available_bikes | Bike.objects.filter(id=selected_bike.id)

        self.fields['bike'].queryset = available_bikes.distinct().order_by('-created_at')

        readonly_fields = [
            'bike_price',
            'final_price',
            'payable_amount',
            'finance_amount',
            'finance_interest_amount',
            'total_amount_include_interest',
            'monthly_emi',
        ]

        for field_name in readonly_fields:
            self.fields[field_name].widget.attrs.update({'readonly': 'readonly'})


class ContactInquiryForm(forms.ModelForm):
    class Meta:
        model = ContactInquiry
        fields = ['name', 'phone', 'email', 'message']


class TestimonialForm(forms.ModelForm):
    class Meta:
        model = Testimonial
        fields = ['customer_name', 'email', 'message', 'rating']

        widgets = {
            'customer_name': forms.TextInput(attrs={
                'placeholder': 'Your Name'
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': 'Your Email'
            }),
            'message': forms.Textarea(attrs={
                'placeholder': 'Write your feedback',
                'rows': 4
            }),
            'rating': forms.NumberInput(attrs={
                'min': 1,
                'max': 5
            }),
        }


class ShopSettingForm(forms.ModelForm):
    class Meta:
        model = ShopSetting
        fields = [
            'shop_name',
            'owner_name',
            'address',
            'phone',
            'email',
            'working_hours',
            'map_location',
            'short_description',
        ]

        widgets = {
            'shop_name': forms.TextInput(attrs={'placeholder': 'Shop Name'}),
            'owner_name': forms.TextInput(attrs={'placeholder': 'Owner Name'}),
            'address': forms.Textarea(attrs={'placeholder': 'Shop Address', 'rows': 3}),
            'phone': forms.TextInput(attrs={'placeholder': 'Phone Number'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Email Address'}),
            'working_hours': forms.TextInput(attrs={'placeholder': '9:00 AM - 8:00 PM'}),
            'map_location': forms.TextInput(attrs={'placeholder': 'Example: Tambaram Chennai Tamil Nadu'}),
            'short_description': forms.Textarea(attrs={'placeholder': 'Short shop description', 'rows': 4}),
        }


class AdminUserForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        help_text='Enter password only when creating or changing password.'
    )

    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('staff', 'Staff'),
    ]

    role = forms.ChoiceField(choices=ROLE_CHOICES)

    class Meta:
        model = User
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'password',
            'role',
            'is_active',
        ]

    def __init__(self, *args, **kwargs):
        self.instance_user = kwargs.get('instance')
        super().__init__(*args, **kwargs)

        if self.instance_user and self.instance_user.pk:
            self.fields['password'].required = False

            if self.instance_user.is_superuser:
                self.fields['role'].initial = 'admin'
            else:
                self.fields['role'].initial = 'staff'
        else:
            self.fields['password'].required = True

    def save(self, commit=True):
        user = super().save(commit=False)

        role = self.cleaned_data.get('role')
        password = self.cleaned_data.get('password')

        user.is_staff = True
        user.is_superuser = role == 'admin'

        if password:
            user.set_password(password)

        if commit:
            user.save()

        return user