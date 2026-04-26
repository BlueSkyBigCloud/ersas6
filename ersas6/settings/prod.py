from .base import *

DEBUG = False

ALLOWED_HOSTS = ['www.tradesec.us', 'tradesec.us', 'proforops.com', 'www.proforops.com', 'ersas-32ed9640lkmsjsdkjsd7b2f.herokuapp.com']


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

CORS_ALLOWED_ORIGINS = [
    "https://www.proforops.com",
    "https://proforops.com",
    "https://www.tradesec.us",
    "https://tradesec.us",
    ]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}