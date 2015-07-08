"""
Django settings for crewser project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
from django.conf.global_settings import TEMPLATE_CONTEXT_PROCESSORS as TCP
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '8xy4ac!42zy=xvrakny!o==wt^ru&!1wkzmn@gn@fvhv9m7i63'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []

TEMPLATE_CONTEXT_PROCESSORS = TCP + (
    'django.core.context_processors.request',
    'crewdb.context_processors.licensed',
    'crewdb.context_processors.suit_licensed'
)

# Application definition

INSTALLED_APPS = (
    'suit',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'crewdb',
    #'debug_toolbar',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    #'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'crewser.urls'

WSGI_APPLICATION = 'crewser.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/
#LANGUAGE_CODE = 'en-us'

# Warum geht das nicht? .. siehe: http://www.djangobook.com/en/2.0/chapter19.html
# imho. nur wenn man eine app auuf bestimmte sprachen begrenzen will, is das sinnvoll
# gehoert also wenn, dann in ein app-file, aber auf jeden Fall nich hierher,
# brauchen wir aber auch nich, oder?
# semmi: aah, verstehe (bei mehreren apps ja erst sinnvoll ... aber fkt. hats trotzdem nicht.. egal ;)
#LANGUAGES = (
   #('en', _('English')),	
   #('de', _('German')),	
#)

LOCALE_PATHS = (
  os.path.join(BASE_DIR, 'locale/'),
)

# damit "python manage.py makemessages -l de" funktioniert
# siehe: http://stackoverflow.com/questions/26675881/i18n-stopped-working
# This is a bug in Django 1.7.1 and should be removed in Django 1.7.2
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
MEDIA_ROOT = os.path.join(BASE_DIR, '')

TIME_ZONE = 'Europe/Berlin'
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/
STATIC_URL = '/static/'
# Additional locations of static files
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'crewdb/static'),
)

TEMPLATE_DIRS = [
  os.path.join(BASE_DIR, 'crewdb/templates'),
  os.path.join(BASE_DIR, 'templates'),
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
            },
        },
    'loggers': {
        # enable the following lines to have full debugging on runserver
        #'django': {
            #'handlers': ['console'],
            #'propagate': True,
            #'level': 'DEBUG',
        #},
        'crewdb.custom': {
            'handlers': ['console'],
            'level': 'DEBUG',
        }
    },
}

SUIT_CONFIG = {
    'ADMIN_NAME': 'Crewser Database',
    'HEADER_DATE_FORMAT': 'l, j. F Y',
    'HEADER_TIME_FORMAT': 'H:i',
    'CONFIRM_UNSAVED_CHANGES': True,
    'SEARCH_URL': '/crewdb/member/',
    'MENU_OPEN_FIRST_CHILD': True,
    'MENU_ICONS': {
        'sites': 'icon-leaf',
        'auth': 'glyphicons-group',
    },
    'MENU': (
      '-',
      {'label': 'Crews', 'url': 'crewdb.crew', 'icon':'icon-user'},
      {'label': 'Member', 'url': 'crewdb.member', 'icon':'icon-user'},
      {'label': 'Billing', 'url': 'crewdb.billing', 'icon':'icon-user'},
      '-',
      {'app': 'crewdb', 'label': 'Settings', 'icon':'icon-wrench',
       'models': ('ticket', 'compensationschema', 'eventtimes', 'service', 'vatrate', 'company', 'accountingdone')},
      '-',
      {'app': 'auth', 'label': 'Host-Users', 'icon':'icon-lock', 'models': ('user', 'group')},
    ),
    'LIST_PER_PAGE': 20
}
