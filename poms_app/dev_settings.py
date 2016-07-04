from __future__ import unicode_literals

import os

# ENV    : DJANGO_SETTINGS_MODULE=poms_app.test_settings;PYTHONUNBUFFERED=1

os.environ['DJANGO_DEBUG'] = 'True'
os.environ['POMS_DEV'] = 'True'

from .settings import *

SECRET_KEY = 's#)m^ug%_jr0dtko#83_55rd_we&xu#f9p#!1gh@k&$=5&3e67'

DATABASES['default'] = {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    'TEST': {
        'NAME': os.path.join(BASE_DIR, 'db-tests.sqlite3'),
    },
}

INSTALLED_APPS += ['debug_toolbar', ]

AUTH_PASSWORD_VALIDATORS = []

ADMINS = MANAGERS = [
    ['ailyukhin', 'ailyukhin@vitaminsoft.ru'],
    ['alyakhov', 'alyakhov@vitaminsoft.ru'],
]
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# CELERY ------------------------------------------------

import djcelery

djcelery.setup_loader()

BROKER_URL = 'django://'
# BROKER_URL = 'redis://127.0.0.1:6379/15'
KOMBU_POLLING_INTERVAL = 1
CELERY_RESULT_BACKEND = 'djcelery.backends.database:DatabaseBackend'
CELERYBEAT_SCHEDULER = 'djcelery.schedulers.DatabaseScheduler'
CELERY_ALWAYS_EAGER = DEBUG
CELERY_EAGER_PROPAGATES_EXCEPTIONS = DEBUG
