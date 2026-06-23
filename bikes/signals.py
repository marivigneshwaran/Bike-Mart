from django.db.models.signals import pre_save, post_save, pre_delete
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from decimal import Decimal
from datetime import date, datetime

from .audit_context import get_current_user, get_current_ip
from .models import AuditLog, Bike, Customer, Vendor, Employee, BillPayment, ShopSetting


TRACKED_MODELS = (
    Bike,
    Customer,
    Vendor,
    Employee,
    BillPayment,
    ShopSetting,
)


def clean_value(value):
    if value is None:
        return None

    if isinstance(value, (date, datetime)):
        return value.isoformat()

    if isinstance(value, Decimal):
        return str(value)

    if hasattr(value, 'name'):
        return value.name if value.name else None

    return value


def get_model_values(instance):
    data = {}

    for field in instance._meta.fields:
        field_name = field.name
        value = getattr(instance, field_name, None)

        if field.is_relation and value:
            data[field_name] = str(value)
        else:
            data[field_name] = clean_value(value)

    return data


@receiver(pre_save)
def store_old_values(sender, instance, **kwargs):
    if sender not in TRACKED_MODELS:
        return

    if not instance.pk:
        instance._audit_old_values = None
        return

    try:
        old_instance = sender.objects.get(pk=instance.pk)
        instance._audit_old_values = get_model_values(old_instance)
    except sender.DoesNotExist:
        instance._audit_old_values = None


@receiver(post_save)
def create_update_audit_log(sender, instance, created, **kwargs):
    if sender not in TRACKED_MODELS:
        return

    user = get_current_user()
    ip_address = get_current_ip()
    new_values = get_model_values(instance)

    if created:
        AuditLog.objects.create(
            user=user,
            action='create',
            model_name=sender.__name__,
            object_id=str(instance.pk),
            object_repr=str(instance),
            ip_address=ip_address,
            old_values=None,
            new_values=new_values,
        )
    else:
        old_values = getattr(instance, '_audit_old_values', None)

        if old_values and old_values != new_values:
            AuditLog.objects.create(
                user=user,
                action='update',
                model_name=sender.__name__,
                object_id=str(instance.pk),
                object_repr=str(instance),
                ip_address=ip_address,
                old_values=old_values,
                new_values=new_values,
            )


@receiver(pre_delete)
def delete_audit_log(sender, instance, **kwargs):
    if sender not in TRACKED_MODELS:
        return

    AuditLog.objects.create(
        user=get_current_user(),
        action='delete',
        model_name=sender.__name__,
        object_id=str(instance.pk),
        object_repr=str(instance),
        ip_address=get_current_ip(),
        old_values=get_model_values(instance),
        new_values=None,
    )


@receiver(user_logged_in)
def login_audit_log(sender, request, user, **kwargs):
    ip_address = None

    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded_for:
        ip_address = forwarded_for.split(',')[0].strip()
    else:
        ip_address = request.META.get('REMOTE_ADDR')

    AuditLog.objects.create(
        user=user,
        action='login',
        model_name='User',
        object_id=str(user.id),
        object_repr=user.username,
        ip_address=ip_address,
        old_values=None,
        new_values={
            'username': user.username,
            'event': 'User logged in'
        },
    )


@receiver(user_logged_out)
def logout_audit_log(sender, request, user, **kwargs):
    if not user:
        return

    ip_address = None

    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded_for:
        ip_address = forwarded_for.split(',')[0].strip()
    else:
        ip_address = request.META.get('REMOTE_ADDR')

    AuditLog.objects.create(
        user=user,
        action='logout',
        model_name='User',
        object_id=str(user.id),
        object_repr=user.username,
        ip_address=ip_address,
        old_values=None,
        new_values={
            'username': user.username,
            'event': 'User logged out'
        },
    )