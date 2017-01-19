from __future__ import absolute_import, unicode_literals

import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'poms_app.settings_dev_ai')

from celery import Celery
from django.conf import settings
from poms.common.kombu_serializers import register_pickle_signed

register_pickle_signed()

app = Celery('poms.backend')

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
