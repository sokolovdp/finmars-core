from __future__ import unicode_literals

from django.contrib import admin
from django.utils.translation import ugettext_lazy

admin.site.site_title = ugettext_lazy('Finmars site admin')
admin.site.site_header = ugettext_lazy('Finmars administration')
admin.site.index_title = ugettext_lazy('Finmars site administration')
admin.site.empty_value_display = '<small>NULL</small>'
