from __future__ import unicode_literals

from rest_framework.filters import BaseFilterBackend

from poms.instruments.models import Instrument
from poms.users.filters import OwnerByMasterUserFilter


class OwnerByInstrumentFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        instruments = Instrument.objects.all()
        instruments = OwnerByMasterUserFilter().filter_queryset(request, instruments, view)
        return queryset.filter(instrument__in=instruments)
