from __future__ import unicode_literals

from django.conf import settings
from django.conf.urls import url, include
from django.contrib import admin


urlpatterns = []

if 'rest_framework_swagger' in settings.INSTALLED_APPS:
    urlpatterns += [
        url(r'^api/doc/', include('rest_framework_swagger.urls')),
    ]

urlpatterns += [
    url(r'^api/', include('poms.api.urls')),
]

if settings.ADMIN:
    if 'grappelli' in settings.INSTALLED_APPS:
        urlpatterns += [
            url(r'^admin/grappelli/', include('grappelli.urls')),
        ]
    urlpatterns += [
        url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
        url(r'^admin/', admin.site.urls),
    ]


