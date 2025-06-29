"""
Настройки Django для проекта kaudio_server.

Основной файл конфигурации Django проекта KAudio.
Включает настройки для:
- Базы данных
- Аутентификации и авторизации
- REST Framework
- CORS
- Медиа файлов
- Swagger документации
- Интернационализации

Для получения дополнительной информации см.:
https://docs.djangoproject.com/en/5.0/topics/settings/

Для полного списка настроек и их значений см.:
https://docs.djangoproject.com/en/5.0/ref/settings/
"""

from pathlib import Path
from datetime import timedelta
import os
import sentry_sdk
import sys
from dotenv import load_dotenv
import dj_database_url

# Загружаем переменные окружения из .env файла
load_dotenv()

# Пути к директориям проекта
BASE_DIR = Path(__file__).resolve().parent.parent


# Настройки для разработки - НЕ ПОДХОДЯТ ДЛЯ ПРОДАКШЕНА
# См. https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# ВНИМАНИЕ: храните секретный ключ в тайне в продакшене!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-5x^$=y3wp8#(%!*ram0&#&*nu=#wga-))%&knk$stz3=%71q83')

DEBUG = False
# Включать DEBUG только при запуске тестов
if 'test' in sys.argv:
    DEBUG = True

ALLOWED_HOSTS = ['*']


# Определение приложений

INSTALLED_APPS = [
    # Django встроенные приложения
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic', # должно быть над staticfiles
    'django.contrib.staticfiles',
    'django_extensions',
    
    # Сторонние приложения
    'rest_framework',
    'rest_framework.authtoken',
    'drf_yasg',
    'corsheaders',
    # 'silk',
    # раскоментить на локалке
    
    # Локальные приложения
    'kaudio',
    'django_celery_beat',
    'django.contrib.sites',  # обязательно!
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'dj_rest_auth',
    'dj_rest_auth.registration',
]

MIDDLEWARE = [
    # CORS middleware должен быть первым
    'corsheaders.middleware.CorsMiddleware',
    
    # Django middleware
    'django.middleware.common.CommonMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 'silk.middleware.SilkyMiddleware', 
    # раскоментить на локалке
]

# Настройки CORS для кросс-доменных запросов
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # React dev server
    "http://localhost:5173",  # Vite dev server
    "https://harmonious-zabaione-aa1493.netlify.app",  # Production frontend
]

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Дополнительные настройки CORS
CORS_URLS_REGEX = r'^.*$'
CORS_EXPOSE_HEADERS = ['Content-Type', 'X-CSRFToken']

ROOT_URLCONF = 'kaudio_server.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
        ],
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

WSGI_APPLICATION = 'kaudio_server.wsgi.application'


# Настройки базы данных
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Настройка базы данных для Render
if 'DATABASE_URL' in os.environ:
    DATABASES['default'] = dj_database_url.config(
        conn_max_age=600,
        ssl_require=True
    )


# Валидация паролей
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

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


# Интернационализация
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'ru'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Статические файлы (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Тип поля первичного ключа по умолчанию
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Кастомная модель пользователя
AUTH_USER_MODEL = 'kaudio.User'


# Настройки Swagger документации
SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header'
        }
    },
    'USE_SESSION_AUTH': True,
    'JSON_EDITOR': True,
    'PERSIST_AUTH': True,
    'REFETCH_SCHEMA_WITH_AUTH': True,
    'VALIDATOR_URL': None,
}

# Настройки Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
}

# Настройки медиа файлов
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        '': {  # Root logger
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Отключить логи при запуске тестов
if 'test' in sys.argv:
    LOGGING['loggers']['']['handlers'] = []
    LOGGING['loggers']['']['level'] = 'CRITICAL'

# Sentry
sentry_sdk.init(
    dsn=os.environ.get('SENTRY_DSN', "https://7f1a3a062f809d43f239b7e1e2e3a0aa@o4509527088496640.ingest.de.sentry.io/4509527092822096"),
    # Add data like request headers and IP for users,
    # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
    send_default_pii=True,
)

CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

from celery.schedules import crontab
CELERY_BEAT_SCHEDULE = {
    'send-statistics-every-minute': {
        'task': 'kaudio.tasks.send_statistics_email',
        'schedule': crontab(),
    },
    'print-hello-every-minute': {
        'task': 'kaudio.tasks.print_hello',
        'schedule': crontab(),
    },
}

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'localhost'
EMAIL_PORT = 1025
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
EMAIL_USE_TLS = False
DEFAULT_FROM_EMAIL = 'test@kaudio.local'

SITE_ID = 1

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)

ACCOUNT_EMAIL_VERIFICATION = "none"
ACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_EMAIL_VERIFICATION = "none"
SOCIALACCOUNT_QUERY_EMAIL = True