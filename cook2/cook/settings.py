from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-tr=%p*wzknz)y4cxa4#o1_-@vlb300q3r8kc9upj!*=^u*0r)n'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'account',
    'chat',
    'review',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'cook.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'cook', 'templates'),
                os.path.join(BASE_DIR, 'account', 'templates'),
                os.path.join(BASE_DIR, 'chat', 'templates'),
                os.path.join(BASE_DIR, 'review', 'templates'),
                ],
        'APP_DIRS': True,
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

WSGI_APPLICATION = 'cook.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',  # MySQL 엔진 사용
        'NAME': 'cookit',  #aws rds만든 DB 이름
        'USER': 'ucandoit',  # MySQL 사용자
        'PASSWORD': 'cookitcookeat',  # aws rds 비밀번호
        'HOST': 'cookitcookeat.cluster-cfwm602q8xg8.ap-northeast-2.rds.amazonaws.com',  # 로컬 MySQL 사용
        'PORT': '3306',  # 기본 포트
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', "OPTIONS": {"min_length": 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, "cook", "static")]

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# 로그인 후 이동할 기본 페이지
LOGIN_REDIRECT_URL = '/chat/'
LOGOUT_REDIRECT_URL = '/account/login/'

# 로그인 페이지 URL
LOGIN_URL = '/account/login/'

# 커스텀 유저 모델 설정
AUTH_USER_MODEL = 'account.Users'

#카카오톡 RestAPI키
KAKAO_REST_API_KEY = 'cef73be738ef09d08640bcdfa716d4dc'

# 미디어 파일 설정 추가
MEDIA_URL = '/media/' 
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# 이메일 설정 (Gmail 예시)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
EMAIL_HOST_USER = 'cookitcookeat@gmail.com'  # 발신자 이메일
EMAIL_HOST_PASSWORD = 'jdceaodzlqughsgm'  # 앱 비밀번호 사용
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

SESSION_ENGINE = "django.contrib.sessions.backends.db"  # 기본 설정
SESSION_COOKIE_AGE = 5000
SESSION_SAVE_EVERY_REQUEST = False
SESSION_EXPIRE_AT_BROWSER_CLOSE = False