import django_filters
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.utils.encoding import force_text
from rest_framework.filters import BaseFilterBackend

from poms.obj_perms.utils import obj_perms_filter_objects_for_view
from poms.tags.models import Tag


class TagFakeFilter(django_filters.Filter):
    def __init__(self, *args, **kwargs):
        super(TagFakeFilter, self).__init__(*args, **kwargs)

    def filter(self, qs, value):
        return qs


class TagContentTypeFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        from poms.accounts.models import AccountType
        from poms.accounts.models import Account
        from poms.currencies.models import Currency
        from poms.instruments.models import InstrumentType
        from poms.instruments.models import Instrument
        from poms.counterparties.models import Counterparty
        from poms.counterparties.models import Responsible
        from poms.strategies.models import Strategy1, Strategy2, Strategy3
        from poms.portfolios.models import Portfolio
        from poms.transactions.models import TransactionType

        models = [AccountType, Account, Currency, InstrumentType, Instrument, Counterparty, Responsible,
                  Strategy1, Strategy2, Strategy3, Portfolio, TransactionType]
        ctypes = [ContentType.objects.get_for_model(model).pk for model in models]
        return queryset.filter(pk__in=ctypes)


class TagFilterBackend(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        queryset = queryset.prefetch_related(
            'tags',
            'tags__user_object_permissions',
            'tags__user_object_permissions__permission',
            'tags__group_object_permissions',
            'tags__group_object_permissions__permission',
        )

        tags = request.query_params.get('tags', None)
        if not tags:
            return queryset
        tags = force_text(tags).split(',')

        # # as name
        # f = Q()
        # for t in tags:
        #     if t:
        #         f |= Q(name__icontains=t) | Q(name__icontains=t)

        # as id
        ids = [int(t) for t in tags if t]
        f = Q(id__in=ids)

        tag_qs = obj_perms_filter_objects_for_view(
            request.user.member,
            queryset=Tag.objects.filter(f, master_user=request.user.master_user),
            prefetch=False)
        return queryset.filter(tags__id__in=tag_qs)
