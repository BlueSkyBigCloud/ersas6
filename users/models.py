from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone

# Create your models here.

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

import uuid

class CustomUser(AbstractBaseUser, PermissionsMixin):
    promotion_code = models.CharField(max_length=50, blank=True, null=True, unique=True)
    stripe_coupon_id = models.CharField(max_length=100, blank=True, null=True)
    coupon_code = models.CharField(max_length=50, blank=True, null=True, unique=True)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company_name = models.CharField(max_length=30, blank=True)
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=30, blank=True, unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)  # Add this line
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    is_onboarded = models.BooleanField(default=False)
    company = models.ForeignKey(
        'app.Company', 
        on_delete=models.CASCADE, 
        related_name='customusers', 
        null=True, 
        blank=True
    )
    
    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customuser_set',  # Custom related name
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        verbose_name='groups'
    )
    
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customuser_set',  # Custom related name
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions'
    )

    def save(self, *args, **kwargs):
        """Automatically set `is_onboarded` based on whether `company` is assigned."""
        self.is_onboarded = self.company is not None
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email
    