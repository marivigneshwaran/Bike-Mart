from django import forms
from django.contrib.auth.models import User

from .models import (
    Bike,
    BikeImage,
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

class BikeImageForm(forms.ModelForm):
    class Meta:
        model = BikeImage
        fields = ['image', 'caption']


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

class SignupForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Enter password'
        })
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Confirm password'
        })
    )

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'username',
            'email',
            'password',
            'confirm_password',
        ]

        widgets = {
            'first_name': forms.TextInput(attrs={
                'placeholder': 'First Name'
            }),
            'last_name': forms.TextInput(attrs={
                'placeholder': 'Last Name'
            }),
            'username': forms.TextInput(attrs={
                'placeholder': 'Username'
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': 'Email Address'
            }),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')

        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already taken.')

        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')

        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already registered.')

        return email

    def clean(self):
        cleaned_data = super().clean()

        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError('Password and confirm password do not match.')

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)

        user.set_password(self.cleaned_data['password'])

        # Signup users are staff users but inactive until admin approval
        user.is_staff = True
        user.is_superuser = False
        user.is_active = False

        if commit:
            user.save()

        return user


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

    user.set_password(self.cleaned_data['password'])

    username = self.cleaned_data.get('username')

    # Temporary bootstrap rule:
    # If username is admin, make this account active superuser.
    # After login succeeds, you can remove this special condition.
    if username == 'admin':
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
    elif not User.objects.exists():
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
    else:
        user.is_staff = True
        user.is_superuser = False
        user.is_active = False

    if commit:
        user.save()

    return user