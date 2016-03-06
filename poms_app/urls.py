from __future__ import unicode_literals

from django.conf.urls import url, include
from django.contrib import admin

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^api/', include('poms.api.urls')),
    #    url(r'^postman/', include('postman.urls', namespace='postman', app_name='postman')),
]
