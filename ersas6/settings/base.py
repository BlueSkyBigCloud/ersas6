import os
from pathlib import Path
from dotenv import load_dotenv
import stripe

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv('SECRET_KEY')
FERNET_KEY = os.getenv('FERNET_KEY')
stripe.api_key = os.getenv('STRIPE_API_KEY')
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISH_KEY')
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = []

SUBSCRIPTION = 'price_1SHVT1GLcTDJWbqVgmemWiuC'
# Application definition

X_FRAME_OPTIONS = 'SAMEORIGIN'

INSTALLED_APPS = [
    'django.contrib.sitemaps',
    'priceanalysis',
    'prospects',
    'contact',
    'inventory',
    'storages',
    'file_store',
    'aiformat',
    'crm',
    'embed_video',
    'video',
    'dataupload',
    'googlemap',
    'ip_whitelist1',
    'file_transfer',
    'print',
    'business',
    'userpayment',
    'app',
    'users',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'allauth',
    'allauth.account',  # Add this
    'allauth.socialaccount',
    'django_cryptography',
    'dj_rest_auth',
    'rest_framework_simplejwt',
    'rest_framework.authtoken',
    'rest_framework',
    
]

# Allow all domains for now

MIDDLEWARE = [


    'django.middleware.common.CommonMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',

    #'ip_whitelist1.middleware.AutoBlockIPMiddleware',
    'ip_whitelist1.middleware.LogAllIPMiddleware',
    #'ip_whitelist1.middleware.BlockSpecificIPMiddleware',
]

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',  # Keep this
    'allauth.account.auth_backends.AuthenticationBackend',  # Add this
    
)


REST_FRAMEWORK = {
     'DEFAULT_AUTHENTICATION_CLASSES': (
         'rest_framework.authentication.TokenAuthentication',
 
     ),
     'DEFAULT_PERMISSION_CLASSES': [
         'app.permissions.CustomIsAuthenticated',
     ]
 }

CORS_ALLOWED_ORIGINS = [

    "http://www.proforops.com",  # For production
]




ROOT_URLCONF = 'ersas6.urls'



STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'app', 'templates')], 
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'ersas6.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),  # Fallback to default if not set
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

USE_I18N = True

LANGUAGES = [
        ('en-us', 'English'),
        ('es', 'Spanish'),
        ('fr', 'French'),
        # Add more languages as needed
    ]

LOCALE_PATHS = [
        os.path.join(BASE_DIR, 'locale'),
    ]

TIME_ZONE = 'America/Chicago'
USE_I18N = True
USE_TZ = True


# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
SOCIALACCOUNT_PROVIDERS = {}
SOCIALACCOUNT_LOGIN_ON_GET=True

AUTH_USER_MODEL = 'users.CustomUser'  

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'), 
]
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_KEY_REFERENCE = 'AWETY129'
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.privateemail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'contact@proforops.com'
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = 'contact@proforops.com'
INTERNAL_CONTACT_EMAIL = 'contact@proforops.com'
PASSWORD_RESET_TIMEOUT = 86400
ACCOUNT_EMAIL_VERIFICATION= 'mandatory'
KEY_REFERENCE = '2345GHTY1295768AWE'
# Use 56 for app.settings ref #
ACCOUNT_EMAIL_REQUIRED = True 
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
LOGIN_METHODS = "email"

from storages.backends.s3boto3 import S3Boto3Storage

class StaticStorage(S3Boto3Storage):
    location = 'static'
    default_acl = 'public-read'

class MediaStorage(S3Boto3Storage):
    location = 'media'
    file_overwrite = False

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME')  # e.g. 'us-east-1'
AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME
AWS_S3_FILE_OVERWRITE = False
STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'


DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_REFERRER_POLICY = "no-referrer-when-downgrade"

YOUR_IPINFO_API_KEY= os.getenv('YOUR_IPINFO_API_KEY')

CELERY_BROKER_URL = "redis://127.0.0.1:6379/0"
CELERY_RESULT_BACKEND = "redis://127.0.0.1:6379/0"
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"