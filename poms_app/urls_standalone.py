from __future__ import unicode_literals

from django.conf import settings
from django.conf.urls import url, include
from django.contrib import admin
from django.views import static

from poms.api.views import index

urlpatterns = []

urlpatterns += [
    url(r'^$', index, name='index'),
    url(r'^api/', include('poms.api.urls')),

    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', admin.site.urls),
]
