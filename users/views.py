from django.shortcuts import render
from django.contrib.auth.models import BaseUserManager
from allauth.socialaccount.views import SignupView as AllAuthSignupView
from allauth.account.views import LoginView
from django.shortcuts import redirect
from django.contrib.auth import login, authenticate
from allauth.socialaccount.models import SocialAccount
from django.contrib import messages
from users.models import CustomUser
from allauth.account.utils import complete_signup
from allauth.account import app_settings as account_settings
from . import signals

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

import logging
logger = logging.getLogger(__name__)


class CustomSocialLoginView(LoginView):
    template_name = 'login.html'

    def form_valid(self, form):
        # Authenticate the user using form data
        user = authenticate(
            self.request, 
            username=form.cleaned_data['username'], 
            password=form.cleaned_data['password']
        )
        
        if user is not None:
            if not user.is_onboarded:  # Check if the user is onboarded
                # Check for a matching invitation
                try:
                    invitation = Invitation.objects.get(email=user.email, accepted=False)
                    user.company = invitation.company  # Assign the company
                    user.save()  # Save the user with the updated company
                    invitation.accepted = True  # Mark the invitation as accepted
                    invitation.save()
                except Invitation.DoesNotExist:
                    logger.info(f"No pending invitation found for {user.email}.")
                    messages.error(
                        self.request,
                        "No invitation found. Please contact your administrator."
                    )
                    return redirect('login')
                
                logger.info(f"User {user.username} is not onboarded. Redirecting to onboarding.")
                return redirect('companyonboarding')  # Redirect to the onboarding page
            
            # Log in the user and show a profile recognized message
            login(self.request, user)
            logger.info(f"User {user.username} profile recognized.")
            return redirect(self.get_success_url())
        
        else:
            # Check if the user exists and has a social account
            try:
                user = CustomUser.objects.get(username=form.cleaned_data['username'])
                if SocialAccount.objects.filter(user=user).exists():
                    messages.error(self.request, "Please use your social account to log in.")
                else:
                    messages.error(self.request, "Invalid email or password.")
            except CustomUser.DoesNotExist:
                messages.error(self.request, "Invalid email or password.")
            
            return redirect('login')
        
from app.models import *

from ip_whitelist1.utils import get_client_ip

class CustomSignupView(AllAuthSignupView):
    def form_valid(self, form):

        signup_ip = self.get_client_ip(self.request)

        # Save the user first to get the user object
        user = form.save(self.request)

        user.signup_ip_address = signup_ip
        user.save(update_fields=["signup_ip_address"])

        print(f"User  signed up with email: {user.email} from IP {"signup_ip_address"}")  # Debugging line
        
        # Try to find an invitation by email
        try:
            invitation = Invitation.objects.get(email=user.email)
            # If invitation exists, assign its company to the user
            user.company = invitation.company
            user.save()
            
            # Optionally mark the invitation as accepted
            invitation.accepted = True
            invitation.save()
        except Invitation.DoesNotExist:
            # If no invitation exists, proceed without setting the company
            print("No company found")
            pass

        # Complete the signup process
        return complete_signup(self.request, user, account_settings.EMAIL_VERIFICATION, None)
    
    