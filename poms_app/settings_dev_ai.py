from __future__ import unicode_literals

# noinspection PyUnresolvedReferences
import env_ai

# noinspection PyUnresolvedReferences
from .settings import *

if 'crispy_forms' not in INSTALLED_APPS:
    INSTALLED_APPS += ['crispy_forms', ]
if 'redisboard' not in INSTALLED_APPS:
    INSTALLED_APPS += ['redisboard', ]
if 'debug_toolbar' not in INSTALLED_APPS:
    INSTALLED_APPS += ['debug_toolbar', ]

LOGGING['formatters']['verbose']['format'] = '[%(levelname)1.1s %(asctime)s %(name)s %(module)s:%(lineno)d] %(message)s'
# LOGGING['loggers']['django.db'] = {'level': 'DEBUG'}
LOGGING['loggers']['poms']['level'] = 'DEBUG'

SECRET_KEY = 's#)m^ug%_jr0dtko#83_55rd_we&xu#f9p#!1gh@k&$=5&3e67'

AUTH_PASSWORD_VALIDATORS = []

DEFAULT_FROM_EMAIL = '"AI: Finmars Notifications" <no-reply@finmars.com>'
SERVER_EMAIL = '"AI-ADMIN: FinMars" <no-reply@finmars.com>'
ADMINS = MANAGERS = [
    ['ailyukhin', 'ailyukhin@vitaminsoft.ru'],
]
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

MEDIA_URL = '/api/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'tmp', 'media')
MEDIA_SERVE = True

# CELERY ------------------------------------------------


CELERY_ALWAYS_EAGER = True
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
CELERYD_LOG_FORMAT = LOGGING['formatters']['verbose']['format']
CELERY_TASK_RESULT_EXPIRES = 600

# INTEGRATIONS ------------------------------------------------


IMPORT_CONFIG_STORAGE = {
    'BACKEND': 'django.core.files.storage.FileSystemStorage',
    'KWARGS': {
        'location': os.path.join(BASE_DIR, 'tmp', 'import', 'config'),
        'base_url': '/api/hidden/'
    }
}

IMPORT_FILE_STORAGE = {
    'BACKEND': 'django.core.files.storage.FileSystemStorage',
    'KWARGS': {
        'location': os.path.join(BASE_DIR, 'tmp', 'import', 'files'),
        'base_url': '/api/import/'
    }
}

PRICING_AUTO_DOWNLOAD_ENABLED = False
PRICING_AUTO_DOWNLOAD_MIN_TIMEDELTA = None

BLOOMBERG_SANDBOX = True
if BLOOMBERG_SANDBOX:
    BLOOMBERG_RETRY_DELAY = 0.1
BLOOMBERG_SANDBOX_SEND_EMPTY = False
BLOOMBERG_SANDBOX_SEND_FAIL = False
BLOOMBERG_SANDBOX_WAIT_FAIL = False
