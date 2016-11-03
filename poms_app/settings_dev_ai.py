from __future__ import unicode_literals

# noinspection PyUnresolvedReferences
import env_ai
import os

# noinspection PyUnresolvedReferences
from .settings import *

# DATABASES['test_default'] = DATABASES['default'].copy()
# DATABASES['test_default']['NAME'] = 'poms_dev2_test'

if 'crispy_forms' not in INSTALLED_APPS:
    INSTALLED_APPS += ['crispy_forms', ]
if 'redisboard' not in INSTALLED_APPS:
    INSTALLED_APPS += ['redisboard', ]
if 'debug_toolbar' not in INSTALLED_APPS:
    INSTALLED_APPS += ['debug_toolbar', ]

LOGGING['formatters']['verbose']['format'] = '[%(levelname)1.1s %(asctime)s %(name)s %(module)s:%(lineno)d] %(message)s'
LOGGING['loggers']['django.db'] = {'level': 'DEBUG'}
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

if 'debug_toolbar' in INSTALLED_APPS:
    MIDDLEWARE_CLASSES = MIDDLEWARE_CLASSES + ['debug_toolbar.middleware.DebugToolbarMiddleware', ]
    INTERNAL_IPS = ['127.0.0.1']

# CELERY ------------------------------------------------


CELERY_ALWAYS_EAGER = True
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
CELERYD_LOG_FORMAT = LOGGING['formatters']['verbose']['format']
CELERY_TASK_RESULT_EXPIRES = 600
# CELERYBEAT_SCHEDULE = {}
CELERYBEAT_SCHEDULE = {
    # 'integrations.download_pricing_auto_scheduler': {
    #     'task': 'integrations.download_pricing_auto_scheduler',
    #     'schedule': 60,
    # },
    # 'instruments.process_events_auto': {
    #     'task': 'instruments.process_events_auto',
    #     'schedule': 60,
    # }
}

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


# if REDIS_HOST:
#     if 'cacheops' not in INSTALLED_APPS:
#         INSTALLED_APPS += ['cacheops', ]
#     CACHEOPS_REDIS = {
#         'host': REDIS_HOST.split(':')[0],
#         # 'host': '127.0.0.1',
#         # 'port': 6379,
#         'db': 5,
#         'socket_timeout': 3,
#     }
#     # CACHEOPS_DEGRADE_ON_FAILURE = True
#     CACHEOPS_DEFAULTS = {
#         'timeout': 60
#     }
#     # on 'all' also cached m2m
#     CACHEOPS = {
#         # 'auth.user': {'ops': 'get', 'cache_on_save': True},
#         'auth.permission': {'ops': 'all'},
#         'contenttypes.contenttype': {'ops': 'all'},
#
#         '*.*': {'ops': ()},
#     }
