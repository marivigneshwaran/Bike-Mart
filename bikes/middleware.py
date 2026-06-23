from .audit_context import set_current_user, set_current_ip


def get_client_ip(request):
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')

    if forwarded_for:
        return forwarded_for.split(',')[0].strip()

    return request.META.get('REMOTE_ADDR')


class AuditLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)

        if user and user.is_authenticated:
            set_current_user(user)
        else:
            set_current_user(None)

        set_current_ip(get_client_ip(request))

        response = self.get_response(request)

        set_current_user(None)
        set_current_ip(None)

        return response