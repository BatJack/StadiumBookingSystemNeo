from .settings import *
import re

DEBUG = False

SECRET_KEY = 'your-production-secret-key-here-change-this'

ALLOWED_HOSTS = ['*']

CSRF_TRUSTED_ORIGINS = []

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

def is_natapp_domain(domain):
    natapp_patterns = [
        r'.*\.natappfree\.cc$',
        r'.*\.natapp1\.cc$',
        r'.*\.natapp\.cc$',
        r'.*\.natapp\d*\.cc$',
    ]
    for pattern in natapp_patterns:
        if re.match(pattern, domain):
            return True
    return False

class DynamicCSRFOriginMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(':')[0]
        if is_natapp_domain(host) or host in ['localhost', '127.0.0.1']:
            origin = f"{request.scheme}://{host}"
            if origin not in CSRF_TRUSTED_ORIGINS:
                CSRF_TRUSTED_ORIGINS.append(origin)
        return self.get_response(request)

class DomainChangeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(':')[0]
        
        stored_host = request.session.get('_domain_host')
        
        if stored_host and stored_host != host:
            request.session.flush()
            from django.middleware.csrf import rotate_token
            rotate_token()
        
        request.session['_domain_host'] = host
        
        response = self.get_response(request)
        
        return response

MIDDLEWARE.insert(0, 'stadium_booking.settings_production.DynamicCSRFOriginMiddleware')
MIDDLEWARE.insert(1, 'stadium_booking.settings_production.DomainChangeMiddleware')

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'data' / 'db.sqlite3',
    }
}

# Security headers
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_HTTPONLY = True
