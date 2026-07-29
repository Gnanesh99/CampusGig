from .base import *

DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost').split(',')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB', 'campusgig'),
        'USER': os.environ.get('POSTGRES_USER', 'campusgig'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'campusgigpassword'),
        'HOST': os.environ.get('POSTGRES_HOST', 'localhost'),
        'PORT': os.environ.get('POSTGRES_PORT', '5432'),
    }
}
LOGIN_REDIRECT_URL = "/gigs/"
LOGOUT_REDIRECT_URL = "/accounts/login/"