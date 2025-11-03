from pathlib import Path
import os
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv() # Load environment variables from .env file

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY')

DEBUG = os.getenv('DEBUG') == 'True'

ALLOWED_HOSTS = ['localhost', 'ethanbetts.pythonanywhere.com', 'splitcart.com.au', 'www.splitcart.com.au', '127.0.0.1']


INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY")
API_SERVER_URL = os.getenv("API_SERVER_URL")
API_SERVER_HOSTNAME = urlparse(API_SERVER_URL).hostname if API_SERVER_URL else None

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    "companies.apps.CompaniesConfig",
    "products.apps.ProductsConfig",
    "data_management.apps.DataManagementConfig",
    "scraping.apps.ScrapingConfig",
    "api.apps.ApiConfig",
    "users.apps.UsersConfig",
    "rest_framework",
    'rest_framework.authtoken',
    'dj_rest_auth',
    'dj_rest_auth.registration',
    "django_extensions",
    "debug_toolbar",
    'corsheaders',
]

SITE_ID = 1


MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "splitcart.middleware.AnonymousUserMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

INTERNAL_IPS = []
if API_SERVER_HOSTNAME:
    INTERNAL_IPS.append(API_SERVER_HOSTNAME)

ROOT_URLCONF = "splitcart.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "frontend" / "dist", BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "splitcart.wsgi.application"

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT', '3306'),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

STATIC_URL = "static/"

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'frontend', 'dist'),
]

STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_STORAGE = "splitcart.storage.CachedManifestStaticFilesStorage"


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = 'users.User'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 500,
    'EXCEPTION_HANDLER': 'api.exception_handler.custom_exception_handler',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        'internal': '100000/day',
    }
}

CORS_ALLOWED_ORIGINS = [

    "http://localhost:5173",
    "https://ethanbetts63.pythonanywhere.com", 
    "https://www.splitcart.com.au",
    "https://splitcart.com.au"
]

from corsheaders.defaults import default_headers

CORS_ALLOW_HEADERS = [
    *default_headers,
    "X-Anonymous-ID",
]



# Custom Account Adapter
ACCOUNT_ADAPTER = 'users.adapter.CustomAccountAdapter'

# Email Authentication Settings
ACCOUNT_AUTHENTICATION_METHOD = 'email'

ACCOUNT_EMAIL_REQUIRED = True

ACCOUNT_UNIQUE_EMAIL = True

ACCOUNT_USERNAME_REQUIRED = False

ACCOUNT_USER_MODEL_USERNAME_FIELD = None

# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_EMAIL_HTML_EMAIL = True
DEFAULT_FROM_EMAIL = 'ethan.betts.dev@gmail.com'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'ethan.betts.dev@gmail.com'
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')


# Custom Serializer for Registration

REST_AUTH = {
    'LOGIN_SERIALIZER': 'users.serializers.CustomLoginSerializer',
    'REGISTER_SERIALIZER': 'users.serializers.CustomRegisterSerializer',

}

# Caching configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake', # A unique string for this cache instance
        'TIMEOUT': 3600, # Cache for 1 hour (3600 seconds)
        'OPTIONS': {
            'MAX_ENTRIES': 1000 # Maximum number of entries in the cache
        }
    }
}
