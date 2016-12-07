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
]

if 'django.contrib.admin' in settings.INSTALLED_APPS:
    if settings.DEV or settings.DEBUG:
        urlpatterns += [
            url(r'^/admin/doc/', include('django.contrib.admindocs.urls')),
            url(r'^/admin/', admin.site.urls),
        ]
    else:
        urlpatterns += [
            url(r'^/411C74D6C4E24D2B98D6B085A580FF61/admin/', admin.site.urls),
        ]

if settings.DEBUG:
    # urlpatterns += [
    #     url(r'^$', RedirectView.as_view(url='/api/v1/'), name='dev-only-root-redirect'),
    # ]

    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns += [
            url(r'^__debug__/', debug_toolbar.urls),
        ]

if getattr(settings, 'MEDIA_SERVE', False):
    urlpatterns += [
        url(r'^media/(?P<path>.*)$', static.serve, {'document_root': settings.MEDIA_ROOT})
    ]

if 'two_factor' in settings.INSTALLED_APPS:
    urlpatterns += [
        url(r'admin/', include('two_factor.urls', 'two_factor')),
    ]
