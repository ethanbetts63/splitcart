from pathlib import Path
import os
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv() # Load environment variables from .env file

BASE_DIR = Path(__file__).resolve().parent.parent
PIPELINE_DATA_DIR = BASE_DIR / "pipeline" / "data"

SECRET_KEY = os.getenv('SECRET_KEY')

DEBUG = os.getenv('DEBUG') == 'True'

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    'ethanbetts.pythonanywhere.com',
    'splitcart.com.au',
    'www.splitcart.com.au',
    'api.splitcart.com.au',
]


INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY")
API_SERVER_URL = os.getenv("API_SERVER_URL")
API_SERVER_HOSTNAME = urlparse(API_SERVER_URL).hostname if API_SERVER_URL else None

# Where the --dev flag points. This used to be the literal string
# "http://127.0.0.1:8000" written out in five separate modules, which meant the
# local half of the pipeline could only ever talk to port 8000 -- and when
# another project in this family holds that port, --dev silently uploads one
# site's scraped catalogue into another site's inbox. A wrong answer, delivered
# confidently, with the API key accepted at the other end.
DEV_API_SERVER_URL = os.getenv("DEV_API_SERVER_URL", "http://127.0.0.1:8000")

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
    "pipeline.apps.PipelineConfig",
    "scraping.apps.ScrapingConfig",

    "users.apps.UsersConfig",
    "rest_framework",
    'rest_framework.authtoken',
    'dj_rest_auth',
    'dj_rest_auth.registration',
    'corsheaders',
]

SITE_ID = 1


# No whole-site cache middleware. UpdateCacheMiddleware/FetchFromCacheMiddleware
# key a cached 200 on the URL plus the response's Vary headers -- and token
# authentication never touches the session, so no Vary: Cookie is ever added and
# every caller computes the same key. That served one shopper's cart, and another
# account's email address, to everyone who asked. The public read-only views that
# actually benefit from caching carry their own @cache_page, which keys the same
# way but is applied deliberately, to a view whose answer does not depend on who
# is asking. Per-caller endpoints additionally carry never_cache.
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.gzip.GZipMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "config.middleware.AnonymousUserMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# Development-only tooling. Both were previously installed unconditionally while
# being commented out of requirements.txt, so a clean install could not boot at
# all and the deployed environment was serving whatever an older venv still had
# on disk -- including the debug toolbar and its `__debug__/` route. Gating them
# here makes the production dependency set and the production URLconf agree.
if DEBUG:
    INSTALLED_APPS += ["django_extensions", "debug_toolbar"]
    # The toolbar wraps the response, so it goes last, after everything that
    # writes to one.
    MIDDLEWARE.append("debug_toolbar.middleware.DebugToolbarMiddleware")

INTERNAL_IPS = ['127.0.0.1']
if API_SERVER_HOSTNAME:
    INTERNAL_IPS.append(API_SERVER_HOSTNAME)

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # No frontend/dist entry: the Vite build directory it named has not
        # existed since the Next migration, and nothing here renders a template
        # from it. Django is API-only.
        "DIRS": [BASE_DIR / "templates"],
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

WSGI_APPLICATION = "config.wsgi.application"

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

# No STATICFILES_DIRS: it pointed at frontend/dist, the Vite output directory,
# which the Next migration removed. The only static files Django still serves
# are the admin's and DRF's, which APP_DIRS finders already find.
STATIC_ROOT = BASE_DIR / "staticfiles"


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = 'users.User'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 24,

    # Applies whatever scope a view declares, and nothing at all when a view
    # declares none. The catch-all `anon`/`user` rates it replaces were not rate
    # limiting: 5000/day anon is one attempt every seventeen seconds, forever,
    # against an endpoint with no account lockout behind it.
    'DEFAULT_THROTTLE_CLASSES': [
        'config.throttling.ScopedRequestThrottle',
    ],
    # Named for what each number protects, not for who is calling.
    'DEFAULT_THROTTLE_RATES': {
        # Credential guessing. There is no account lockout yet -- that arrives
        # with the session migration -- so for now these are the only thing
        # standing between a script and this site's passwords.
        'login': '5/minute',
        'register': '5/hour',
        'password_reset': '5/hour',
        'password_change': '10/hour',
        # dj_rest_auth stamps this scope on its own views. Every one of them is
        # shadowed by a scoped subclass in users/urls.py, but a rate has to
        # exist regardless: ScopedRateThrottle raises ImproperlyConfigured --
        # a 500, on first call -- for a scope with no rate, so a route added by
        # a library upgrade must land on a number rather than on an exception.
        'dj_rest_auth': '5/minute',
        # Cost and load. `cart-sync` writes rows in bulk and `cart-optimize`
        # runs an LP solve, so both are bounded well below ordinary reads.
        'session': '600/hour',
        'cart': '600/hour',
        'cart-sync': '300/hour',
        'cart-optimize': '60/hour',
        # Public reads. Not a security control -- who may call these is settled
        # by the permission class -- so set where a runaway client stops and a
        # person browsing normally never notices.
        'public': '600/hour',
        # Server-to-server, already gated by IsInternalAPIRequest. The throttle
        # bounds call volume between trusted services, not an attack surface.
        'internal': '1000000/day',
    }
}

# The ceiling on the request body itself, which is the only bound that applies
# before anything is parsed: a serializer's per-field maximums are checked after
# the body has already been read into memory. Django's own defaults, stated
# rather than inherited, so that raising one is a visible decision.
#
# Neither figure caps the pipeline's gzipped .jsonl uploads: those arrive as
# multipart files, stream to disk, and are governed by FILE_UPLOAD_MAX_MEMORY_SIZE.
DATA_UPLOAD_MAX_MEMORY_SIZE = 2621440  # 2.5 MiB
# Parsing is quadratic in the number of form fields, so an unbounded count is a
# cheap denial of service.
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "https://ethanbetts63.pythonanywhere.com", 
    "https://www.splitcart.com.au",
    "https://splitcart.com.au",
    "https://api.splitcart.com.au",
]

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://127.0.0.1:8000",
    "https://www.splitcart.com.au",
    "https://splitcart.com.au",
    "https://api.splitcart.com.au",
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
ACCOUNT_EMAIL_VERIFICATION = 'none'
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
    # Backs the per-view @cache_page decorators on the public read-only
    # endpoints. Nothing per-caller is stored here.
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake', # A unique string for this cache instance
        'TIMEOUT': 3600, # Cache for 1 hour (3600 seconds)
        'OPTIONS': {
            'MAX_ENTRIES': 1000 # Maximum number of entries in the cache
        }
    },
    # Separate cache for throttle counters. The default cache above backs the
    # per-view page caches and caps out at 1000 entries, so without this a
    # burst of page traffic would evict an attacker's attempt count.
    'throttling': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'throttling',
        'OPTIONS': {
            'MAX_ENTRIES': 10000,  # Generous -- eviction is what this cache exists to avoid.
        },
    },
}

# Transport and cookie hardening. Every one of these was absent, so the site was
# deployed with no HSTS, no SSL redirect and no Secure flag on the session or
# CSRF cookie that Django's admin login uses.
#
# The transport half is under DEBUG=False only, because an SSL redirect and an
# HSTS header make a plain-HTTP development server unreachable. The rest holds
# in every environment -- there is no environment in which this API wants to be
# framed or sniffed.
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
# DENY, not Django's SAMEORIGIN default. Nothing here is meant to be framed.
X_FRAME_OPTIONS = "DENY"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

if not DEBUG:
    # PythonAnywhere terminates TLS in front of Django, so without this
    # request.is_secure() is False for every request and the redirect below
    # would loop.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 63072000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# One `check --deploy` warning is a decision, not an oversight. It is silenced by
# name so the gate reads as pass/fail: a gate that always prints a warning is one
# people stop reading, and then the real one arrives unnoticed.
SILENCED_SYSTEM_CHECKS = [
    # SECURE_HSTS_PRELOAD. Preload is a one-way commitment binding every present
    # and future subdomain to HTTPS, and it takes a manual submission to
    # hstspreload.org that nothing here performs. No sibling site sets it.
    "security.W021",
]
