from __future__ import unicode_literals

# noinspection PyUnresolvedReferences
import env_ai
import os

# noinspection PyUnresolvedReferences
from .settings import *

DEBUG = True

# DATABASES['default']['NAME'] = 'test_poms_dev2'

if 'crispy_forms' not in INSTALLED_APPS:
    INSTALLED_APPS += ['crispy_forms', ]
if 'redisboard' not in INSTALLED_APPS:
    INSTALLED_APPS += ['redisboard', ]
# if 'debug_toolbar' not in INSTALLED_APPS:
#     INSTALLED_APPS += ['debug_toolbar', ]
#     MIDDLEWARE_CLASSES = MIDDLEWARE_CLASSES + ['debug_toolbar.middleware.DebugToolbarMiddleware', ]
#     INTERNAL_IPS = ['127.0.0.1']

LOGGING['formatters']['verbose']['format'] = '[%(levelname)1.1s %(asctime)s %(name)s %(module)s:%(lineno)d] %(message)s'
# LOGGING['formatters']['verbose']['format'] = '[%(asctime)s] %(message)s'
LOGGING['formatters']['verbose']['format'] = '%(message)s'
# LOGGING['loggers']['django.db'] = {'level': 'DEBUG'}
LOGGING['loggers']['poms']['level'] = 'DEBUG'
# LOGGING['loggers']['poms']['level'] = 'INFO'
# LOGGING['loggers']['poms']['level'] = 'WARN'

SECRET_KEY = 's#)m^ug%_jr0dtko#83_55rd_we&xu#f9p#!1gh@k&$=5&3e67'

AUTH_PASSWORD_VALIDATORS = []
# SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

CORS_ORIGIN_WHITELIST += ('localhost:8000', '127.0.0.1:8000', )

DEFAULT_FROM_EMAIL = '"AI: Finmars Notifications" <no-reply@finmars.com>'
SERVER_EMAIL = '"AI-ADMIN: FinMars" <no-reply@finmars.com>'
ADMINS = MANAGERS = [
    ['ailyukhin', 'ailyukhin@vitaminsoft.ru'],
]
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'

MEDIA_URL = '/api/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'tmp', 'media')
MEDIA_SERVE = True


# REST_FRAMEWORK ------------------------------------------------


REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'] = (
    'rest_framework.authentication.SessionAuthentication',
    'rest_framework.authentication.BasicAuthentication',
)


# CELERY ------------------------------------------------

CELERY_WORKER_CONCURRENCY = 1
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
# CELERY_WORKER_LOG_FORMAT = LOGGING['formatters']['verbose']['format']
# CELERY_RESULT_EXPIRES = 60
CELERY_BEAT_SCHEDULE = {
    # 'integrations.download_pricing_auto_scheduler': {
    #     'task': 'integrations.download_pricing_auto_scheduler',
    #     'schedule': 10,
    # },
    # 'instruments.generate_events': {
    #     'task': 'instruments.generate_events',
    #     'schedule': 10,
    # },
    # 'instruments.process_events': {
    #     'task': 'instruments.process_events',
    #     'schedule': 10,
    # },
}

# REDIS ------------------------------------------------


def _redis(url):
    from urllib.parse import urlsplit, urlunsplit
    components = urlsplit(url)
    components = list(components)
    components[2] = '/3'
    loc = urlunsplit(components)
    return loc


for k, v in CACHES.items():
    if 'RedisCache' in v['BACKEND']:
        v['LOCATION'] = _redis(v['LOCATION'])

if 'redis' in CELERY_BROKER_URL:
    CELERY_BROKER_URL = _redis(CELERY_BROKER_URL)
if 'redis' in CELERY_RESULT_BACKEND:
    CELERY_RESULT_BACKEND = _redis(CELERY_RESULT_BACKEND)


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

PRICING_AUTO_DOWNLOAD_DISABLED = False
PRICING_AUTO_DOWNLOAD_MIN_TIMEDELTA = None

BLOOMBERG_SANDBOX = True
# BLOOMBERG_RETRY_DELAY = 0.1
BLOOMBERG_RETRY_DELAY = 5
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
