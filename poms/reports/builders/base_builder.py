import logging

from poms.accounts.models import Account, AccountType
from poms.counterparties.models import Responsible, ResponsibleGroup, Counterparty, CounterpartyGroup
from poms.currencies.models import Currency
from poms.instruments.models import Instrument, InstrumentType
from poms.obj_attrs.utils import get_attributes_prefetch
from poms.obj_perms.utils import get_permissions_prefetch_lookups
from poms.portfolios.models import Portfolio
from poms.strategies.models import Strategy1, Strategy1Subgroup, Strategy1Group, Strategy2, Strategy2Subgroup, \
    Strategy2Group, Strategy3, Strategy3Subgroup, Strategy3Group
from poms.tags.utils import get_tag_prefetch
from poms.transactions.models import ComplexTransaction, TransactionClass, TransactionType, TransactionTypeGroup

_l = logging.getLogger('poms.reports')


class BaseReportBuilder:
    def _refresh_attrs(self, items, attrs, queryset):
        _l.debug('refresh: %s -> %s', attrs, queryset.model)

        if not items or not attrs:
            return []

        pks = set()
        for item in items:
            for attr in attrs:
                obj = getattr(item, attr, None)
                if obj:
                    pks.add(obj.id)

        objs = queryset.in_bulk(pks)
        _l.debug('objs: %s', objs.keys())

        for item in items:
            for attr in attrs:
                obj = getattr(item, attr, None)
                if obj:
                    setattr(item, attr, objs[obj.id])

        return list(objs.values())

    def _refresh_attrs_simple(self, items, attrs):
        _l.debug('refresh: %s', attrs)

        if not items or not attrs:
            return []

        objs = {}
        for item in items:
            for attr in attrs:
                obj = getattr(item, attr, None)
                if obj:
                    objs[obj.id] = obj
        # _l.debug('objs: %s', sorted(objs.keys()))
        _l.debug('objs: %s', objs.keys())

        return list(objs.values())

    def _refresh_complex_transactions(self, master_user, items, attrs):
        return self._refresh_attrs(
            items=items,
            attrs=attrs,
            queryset=ComplexTransaction.objects.filter(
                transaction_type__master_user=master_user
            ).prefetch_related(
                'transaction_type',
                'transaction_type__group',
                get_attributes_prefetch(),
                *get_permissions_prefetch_lookups(
                    ('transaction_type', TransactionType),
                    ('transaction_type__group', TransactionTypeGroup),
                )
            )
        )

    def _refresh_transaction_classes(self, master_user, items, attrs):
        return self._refresh_attrs(
            items=items,
            attrs=attrs,
            queryset=TransactionClass.objects.all()
        )

    def _refresh_instruments(self, master_user, items, attrs):
        return self._refresh_attrs(
            items=items,
            attrs=attrs,
            queryset=Instrument.objects.filter(
                master_user=master_user
            ).prefetch_related(
                'master_user',
                'instrument_type',
                'instrument_type__instrument_class',
                'pricing_currency',
                'accrued_currency',
                'payment_size_detail',
                'daily_pricing_model',
                'price_download_scheme',
                'price_download_scheme__provider',
                get_attributes_prefetch(),
                get_tag_prefetch(),
                *get_permissions_prefetch_lookups(
                    (None, Instrument),
                    ('instrument_type', InstrumentType),
                )
            )
        )

    def _refresh_currencies(self, master_user, items, attrs):
        return self._refresh_attrs(
            items=items,
            attrs=attrs,
            queryset=Currency.objects.filter(
                master_user=master_user,
            ).prefetch_related(
                get_attributes_prefetch(),
            )
        )

    def _refresh_portfolios(self, master_user, items, attrs):
        return self._refresh_attrs(
            items=items,
            attrs=attrs,
            queryset=Portfolio.objects.filter(
                master_user=master_user,
            ).prefetch_related(
                get_attributes_prefetch(),
                *get_permissions_prefetch_lookups(
                    (None, Portfolio),
                )
            )
        )

    def _refresh_accounts(self, master_user, items, attrs):
        return self._refresh_attrs(
            items=items,
            attrs=attrs,
            queryset=Account.objects.filter(
                master_user=master_user,
            ).prefetch_related(
                'type',
                get_attributes_prefetch(),
                *get_permissions_prefetch_lookups(
                    (None, Account),
                    ('type', AccountType),
                )
            )
        )

    def _refresh_strategies1(self, master_user, items, attrs):
        return self._refresh_attrs(
            items=items,
            attrs=attrs,
            queryset=Strategy1.objects.filter(
                master_user=master_user,
            ).prefetch_related(
                'subgroup',
                'subgroup__group',
                *get_permissions_prefetch_lookups(
                    (None, Strategy1),
                    ('subgroup', Strategy1Subgroup),
                    ('subgroup__group', Strategy1Group),
                )
            )
        )

    def _refresh_strategies2(self, master_user, items, attrs):
        return self._refresh_attrs(
            items=items,
            attrs=attrs,
            queryset=Strategy2.objects.filter(
                master_user=master_user,
            ).prefetch_related(
                'subgroup',
                'subgroup__group',
                *get_permissions_prefetch_lookups(
                    (None, Strategy2),
                    ('subgroup', Strategy2Subgroup),
                    ('subgroup__group', Strategy2Group),
                )
            )
        )

    def _refresh_strategies3(self, master_user, items, attrs):
        return self._refresh_attrs(
            items=items,
            attrs=attrs,
            queryset=Strategy3.objects.filter(
                master_user=master_user,
            ).prefetch_related(
                'subgroup',
                'subgroup__group',
                *get_permissions_prefetch_lookups(
                    (None, Strategy3),
                    ('subgroup', Strategy3Subgroup),
                    ('subgroup__group', Strategy3Group),
                )
            )
        )

    def _refresh_responsibles(self, master_user, items, attrs):
        return self._refresh_attrs(
            items=items,
            attrs=attrs,
            queryset=Responsible.objects.filter(
                master_user=master_user,
            ).prefetch_related(
                'group',
                get_attributes_prefetch(),
                *get_permissions_prefetch_lookups(
                    (None, Responsible),
                    ('group', ResponsibleGroup),
                )
            )
        )

    def _refresh_counterparties(self, master_user, items, attrs):
        return self._refresh_attrs(
            items=items,
            attrs=attrs,
            queryset=Counterparty.objects.filter(
                master_user=master_user,
            ).prefetch_related(
                'group',
                get_attributes_prefetch(),
                *get_permissions_prefetch_lookups(
                    (None, Counterparty),
                    ('group', CounterpartyGroup),
                )
            )
        )

    def _refresh_currency_fx_rates(self, master_user, items, attrs):
        return self._refresh_attrs_simple(items, attrs)

    def _refresh_item_instrument_pricings(self, master_user, items, attrs):
        return self._refresh_attrs_simple(items, attrs)

    def _refresh_item_instrument_accruals(self, master_user, items, attrs):
        return self._refresh_attrs_simple(items, attrs)
