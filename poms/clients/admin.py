from django.contrib import admin

from poms.clients.models import Client
from poms.common.admin import ClassModelAdmin

admin.site.register(Client, ClassModelAdmin)
