from __future__ import unicode_literals

from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

# Register your models here.

admin.site.site_title = _('Finmars site admin')
admin.site.site_header = _('Finmars administration')
admin.site.index_title = _('Finmars site administration')
