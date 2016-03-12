from __future__ import unicode_literals

from django.db.models import Q
from rest_framework.filters import BaseFilterBackend

from poms.api.filters import IsOwnerByMasterUserFilter, IsOwnerByMasterUserOrSystemFilter
from poms.currencies.models import Currency


class IsOwnerViaCurrencyProfileFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        currencies = Currency.objects.all()
        currencies = IsOwnerByMasterUserOrSystemFilter().filter_queryset(request, currencies, view)
        return queryset.filter(currency__in=currencies)
