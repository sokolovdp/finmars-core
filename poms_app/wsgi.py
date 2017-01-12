"""
WSGI config for poms2 project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/howto/deployment/wsgi/
"""

from __future__ import unicode_literals

import os

from django.contrib.staticfiles.handlers import StaticFilesHandler
from django.core.wsgi import get_wsgi_application

# import djcelery
# djcelery.setup_loader()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "poms_app.settings")

application = get_wsgi_application()

# application = StaticFilesHandler(application)
