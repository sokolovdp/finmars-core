from __future__ import unicode_literals
import os

os.environ['DJANGO_DEBUG'] = 'True'

from .settings import *

DATABASES['default'] = {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': ':memory:',
}

# LOGGING['loggers']['django.db'] = {'level': 'DEBUG',}
