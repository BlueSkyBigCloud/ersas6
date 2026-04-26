from functools import wraps
from django.shortcuts import redirect

def onboarded(redirect_view='companyonboarding'):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')

            # Check if the user is onboarded and if their company subscription is active
            if not request.user.is_onboarded or not getattr(request.user.company, 'is_company_subscription_active', False):
                return redirect(redirect_view)

            return view_func(request, *args, **kwargs)

        return _wrapped_view
    return decorator

from functools import wraps
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

def staff_required(redirect_view='dashboard'):
    """
    Decorator to ensure the user is a staff member.
    Redirects to the specified view if the user is not a staff member.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')  # Ensure the user is logged in
            if not request.user.is_staff:
                return redirect(redirect_view)  # Redirect non-staff users
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator