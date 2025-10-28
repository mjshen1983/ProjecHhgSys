import os
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'replace-this-with-a-secure-key'
DEBUG = True
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'app',
    'projects',
    'tasks',
    'attachments',
    'knowledge',
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

ROOT_URLCONF = 'project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'project.wsgi.application'

# DATABASES 配置（已硬编码为项目默认，优先级高于环境变量）
# 已根据需求将数据库连接信息写入 settings.py。注意：这是永久设置，
# 如果你以后想用环境变量或不同环境（dev/prod），请恢复到基于环境变量的实现。
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'HHG_APP_DB',
        'USER': 'systemid',
        'PASSWORD': 'Qwerty!qaz2wsx',
        'HOST': '192.168.6.71',
        'PORT': '3306',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# End of DATABASES configuration (hardcoded)

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Prefer the C driver (mysqlclient) when available. Fall back to PyMySQL only if
# mysqlclient isn't installed. This avoids PyMySQL from masking mysqlclient when
# both are present (which causes Django to see the wrong DB API version).
try:
    # If mysqlclient is installed it provides the MySQLdb module
    import MySQLdb  # noqa: F401
except Exception:
    try:
        import pymysql
        pymysql.install_as_MySQLdb()
    except Exception:
        # If neither driver is present, let Django raise the appropriate error
        pass
