from django.contrib import admin
from reversion.admin import VersionAdmin

# from poms.reports.models import Mapping, ReportType
#
#
# class ReportTypeAdmin(VersionAdmin):
#     model = ReportType
#
#
# admin.site.register(ReportType, ReportTypeAdmin)
#
#
# class MappingAdmin(admin.ModelAdmin):
#     model = Mapping
#     list_display = ['id', 'content_object', 'content_type', 'name', 'master_user']
#
#
# admin.site.register(Mapping, MappingAdmin)
