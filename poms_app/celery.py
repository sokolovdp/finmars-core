from __future__ import absolute_import, unicode_literals

import os

from celery import Celery

from poms.common.kombu_serializers import register_pickle_signed

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'poms_app.settings_dev_ai')

from django.conf import settings

register_pickle_signed()

app = Celery('poms.backend')

app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
