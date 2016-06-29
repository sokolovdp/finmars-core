from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from rest_framework.filters import BaseFilterBackend

from poms.accounts.models import Account
from poms.counterparties.models import Counterparty
from poms.counterparties.models import Responsible
from poms.currencies.models import Currency
from poms.instruments.models import InstrumentType, Instrument, DailyPricingModel, PaymentSizeDetail
from poms.obj_perms.utils import obj_perms_filter_objects_for_view
from poms.portfolios.models import Portfolio
from poms.strategies.models import Strategy1, Strategy2, Strategy3


class TransactionObjectPermissionFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        member = request.user.member
        master_user = request.user.master_user
        if member.is_superuser:
            return queryset
        portfolio_qs = obj_perms_filter_objects_for_view(member, Portfolio.objects.filter(master_user=master_user))
        account_qs = obj_perms_filter_objects_for_view(member, Account.objects.filter(master_user=master_user))
        # minimize inlined SQL
        portfolio_qs = list(portfolio_qs.values_list('id', flat=True))
        account_qs = list(account_qs.values_list('id', flat=True))
        queryset = queryset.filter(
            Q(portfolio__in=portfolio_qs) & (
                Q(account_position__in=account_qs) |
                Q(account_cash__in=account_qs) |
                Q(account_interim__in=account_qs)
            )
        )
        return queryset


class TransactionTypeInputContentTypeFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        models = [Account, Instrument, InstrumentType, Currency, Counterparty, Responsible,
                  Strategy1, Strategy2, Strategy3, DailyPricingModel, PaymentSizeDetail, Portfolio]
        ctypes = [ContentType.objects.get_for_model(model).pk for model in models]
        return queryset.filter(pk__in=ctypes)

# class TransactionTypeGroupFilter(ModelWithPermissionMultipleChoiceFilter):
#     model = TransactionTypeGroup
