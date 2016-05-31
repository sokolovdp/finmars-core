from __future__ import unicode_literals

from .settings import *

DATABASES['default'] = {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': ':memory:',
}

# LOGGING['loggers']['django.db'] = {'level': 'DEBUG',}
