from __future__ import unicode_literals

from rest_framework.filters import BaseFilterBackend

from poms.instruments.models import Instrument
from poms.obj_perms.utils import obj_perms_filter_objects_for_view
from poms.users.filters import OwnerByMasterUserFilter


class OwnerByInstrumentFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        instruments = Instrument.objects.all()
        instruments = OwnerByMasterUserFilter().filter_queryset(request, instruments, view)
        return queryset.filter(instrument__in=instruments)


class PriceHistoryObjectPermissionFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        member = request.user.member
        master_user = request.user.master_user
        if member.is_superuser:
            return queryset
        instrument_qs = obj_perms_filter_objects_for_view(member, Instrument.objects.filter(master_user=master_user))
        queryset = queryset.filter(instrument__in=instrument_qs)
        return queryset

# class InstrumentTypeFilter(ModelWithPermissionMultipleChoiceFilter):
#     model = InstrumentType
#
#
# class InstrumentFilter(ModelWithPermissionMultipleChoiceFilter):
#     model = Instrument
