import threading

_thread_locals = threading.local()


def set_audit_context(user, ip_address):
    _thread_locals.user = user
    _thread_locals.ip_address = ip_address


def get_current_user():
    return getattr(_thread_locals, 'user', None)


def get_current_ip():
    return getattr(_thread_locals, 'ip_address', None)


def clear_audit_context():
    if hasattr(_thread_locals, 'user'):
        del _thread_locals.user
    if hasattr(_thread_locals, 'ip_address'):
        del _thread_locals.ip_address