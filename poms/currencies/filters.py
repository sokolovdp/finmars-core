from __future__ import unicode_literals

from rest_framework.filters import BaseFilterBackend

from poms.currencies.models import Currency
from poms.users.filters import OwnerByMasterUserFilter


class OwnerByCurrencyFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        currencies = Currency.objects.all()
        currencies = OwnerByMasterUserFilter().filter_queryset(request, currencies, view)
        return queryset.filter(currency__in=currencies)

# class CurrencyFilter(ModelMultipleChoiceFilter):
#     model = Currency
