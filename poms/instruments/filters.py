from __future__ import unicode_literals

from rest_framework.filters import BaseFilterBackend

from poms.instruments.models import Instrument, InstrumentType
from poms.obj_attrs.models import GenericAttributeType
from poms.obj_perms.utils import obj_perms_filter_objects_for_view


class OwnerByInstrumentFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        instruments = Instrument.objects.filter(master_user=request.user.master_user)
        return queryset.filter(instrument__in=instruments)


class OwnerByInstrumentTypeFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        instrument_types = InstrumentType.objects.filter(master_user=request.user.master_user)
        return queryset.filter(instrument_type__in=instrument_types)


class OwnerByInstrumentAttributeTypeFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        instrument_attribute_types = GenericAttributeType.objects.filter(master_user=request.user.master_user)
        return queryset.filter(attribute_type__in=instrument_attribute_types)


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
