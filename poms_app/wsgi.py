"""
WSGI config for poms2 project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/howto/deployment/wsgi/
"""

import os
import sys

from django.core.wsgi import get_wsgi_application

del sys.path[0]

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "poms_app.settings")

application = get_wsgi_application()
