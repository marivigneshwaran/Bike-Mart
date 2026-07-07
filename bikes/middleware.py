import threading
from django.shortcuts import redirect
from django.contrib import messages
from .audit_context import set_audit_context, clear_audit_context

class AuditLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. READ-ONLY RESTRICTION FOR 'test' USER
        # Check if the user is authenticated and is the specific test user
        if request.user.is_authenticated and request.user.username == 'test':
            # Block any submission, creation, update or deletion (POST requests)
            if request.method == 'POST':
                messages.error(
                    request, 
                    "Permission Denied: The 'test' account has read-only access and cannot create, edit, or delete any data."
                )
                # Redirect back to where they came from, or the dashboard safely
                return redirect(request.META.get('HTTP_REFERER', 'admin_dashboard'))

        # 2. AUDIT LOG TRACKING CONTEXT
        # Get client IP address safely
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')

        user = request.user if request.user.is_authenticated else None
        
        # Store context details temporarily for the duration of the request
        set_audit_context(user, ip)

        response = self.get_response(request)

        # Clear context thread after response is generated
        clear_audit_context()
        
        return response