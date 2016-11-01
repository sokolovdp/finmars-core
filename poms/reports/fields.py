from rest_framework.relations import PrimaryKeyRelatedField

from poms.common.fields import PrimaryKeyRelatedFilteredField
from poms.reports.models import CustomField
from poms.users.filters import OwnerByMasterUserFilter


class CustomFieldField(PrimaryKeyRelatedFilteredField):
    queryset = CustomField.objects.all()
    filter_backends = [
        OwnerByMasterUserFilter,
    ]


# class ReportClassField(PrimaryKeyRelatedField):
#     queryset = ReportClass.objects
#
#
# class BalanceReportCustomFieldField(PrimaryKeyRelatedFilteredField):
#     queryset = CustomField.objects.filter(report_class=ReportClass.BALANCE)
#     filter_backends = [OwnerByMasterUserFilter]
#
#
# class PLReportCustomFieldField(PrimaryKeyRelatedFilteredField):
#     queryset = CustomField.objects.filter(report_class=ReportClass.P_L)
#     filter_backends = [OwnerByMasterUserFilter]
