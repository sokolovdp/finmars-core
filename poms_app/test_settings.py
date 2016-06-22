from __future__ import unicode_literals

import os

# OPTIONS: --keepdb
# ENV    : DJANGO_SETTINGS_MODULE=poms_app.test_settings;PYTHONUNBUFFERED=1

os.environ['DJANGO_DEBUG'] = 'True'

from .settings import *

DATABASES['default'] = {
    'ENGINE': 'django.db.backends.sqlite3',
    # 'NAME': ':memory:',
    'TEST': {
        # 'NAME': 'mytestdatabase',
        'NAME': os.path.join(BASE_DIR, 'db-tests.sqlite3'),
    },
}

# LOGGING['loggers']['django.db'] = {'level': 'DEBUG',}
