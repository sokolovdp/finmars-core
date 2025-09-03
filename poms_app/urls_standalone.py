from django.conf.urls import include, url
from django.contrib import admin

from poms.api.views import index

urlpatterns = []

urlpatterns += [
    url(r"^$", index, name="index"),
    url(r"^api/", include("poms.api.urls")),
    url(r"^admin/doc/", include("django.contrib.admindocs.urls")),
    url(r"^admin/", admin.site.urls),
]
