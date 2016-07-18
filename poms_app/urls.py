from __future__ import unicode_literals

from django.conf import settings
from django.conf.urls import url, include
from django.contrib import admin
from django.views.generic import RedirectView

urlpatterns = []

if 'rest_framework_swagger' in settings.INSTALLED_APPS:
    urlpatterns += [
        url(r'^api/doc/', include('rest_framework_swagger.urls')),
    ]

urlpatterns += [
    url(r'^api/', include('poms.api.urls')),
]

if 'django.contrib.admin' in settings.INSTALLED_APPS:
    if 'grappelli' in settings.INSTALLED_APPS:
        urlpatterns += [
            url(r'^admin/grappelli/', include('grappelli.urls')),
        ]
    urlpatterns += [
        url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
        url(r'^admin/', admin.site.urls),
    ]

if settings.DEBUG:
    urlpatterns += [
        url(r'^$', RedirectView.as_view(url='/admin/'), name='redirect-to-admin'),
    ]

if getattr(settings, 'MEDIA_SERVE', False):
    urlpatterns += [
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT})]
