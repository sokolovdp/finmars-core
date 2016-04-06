from __future__ import unicode_literals

from django.conf import settings
from django.conf.urls import url, include
from django.contrib import admin


urlpatterns = [
    url(r'^api/', include('poms.api.urls')),
]

if settings.ADMIN:
    urlpatterns += [
        url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
        url(r'^admin/', admin.site.urls),
    ]


