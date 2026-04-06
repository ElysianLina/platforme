import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
# BASE_DIR        = PLATFORM/backend/
# BASE_DIR.parent = PLATFORM/

SECRET_KEY = 'django-insecure-5sg^+1)x2977513bpw(zm-6@3d3g07)+#4m08h**xe%4n)6#2f'
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'users',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

ROOT_URLCONF = 'Django_prj.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
            BASE_DIR.parent / 'frontend' / 'home', 
            BASE_DIR.parent / 'frontend' / 'leveltest',        # startlevel.html, test-cefr.html
            BASE_DIR.parent / 'frontend' / 'authentification', # login.html
            BASE_DIR.parent / 'frontend' / 'preferences',
            BASE_DIR.parent / 'frontend' / 'reset-password',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'Django_prj.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'pfe_db',
        'USER': 'postgres',
        'PASSWORD': 'lina',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


STATIC_URL = '/static/'

STATICFILES_DIRS = [
    BASE_DIR.parent / 'frontend' / 'home',
    BASE_DIR.parent / 'frontend' / 'leveltest',        # startlevel.css/js, test-cefr.css/js
    BASE_DIR.parent / 'frontend' / 'authentification', # login.css/js
    BASE_DIR.parent / 'frontend' / 'preferences', 
    BASE_DIR.parent / 'frontend' / 'reset-password', 
]

# AJOUT : Fichiers media (audio MP3 pour le test CEFR)
# Les fichiers audio sont dans PLATFORM/backend/media/audio/
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'