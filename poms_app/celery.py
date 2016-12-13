from __future__ import absolute_import, unicode_literals

import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'poms_app.settings_dev_ai')

from django.conf import settings

if 'pickle-signed' in settings.CELERY_ACCEPT_CONTENT or 'pickle-signed' in settings.CELERY_TASK_SERIALIZER or 'pickle-signed' in settings.CELERY_RESULT_SERIALIZER:
    from poms.common.kombu_serializers import register_pickle_signed

    register_pickle_signed()

app = Celery('poms.backend')

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
