import django_filters
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.utils.encoding import force_text
from rest_framework.filters import BaseFilterBackend

from poms.obj_perms.utils import obj_perms_filter_objects
from poms.tags.models import Tag
from poms.tags.utils import tags_prefetch


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

#
# class TagPrefetchFilter(BaseFilterBackend):
#     def filter_queryset(self, request, queryset, view):
#         # return queryset.prefetch_related(
#         #     'tags',
#         #     # 'tags__user_object_permissions',
#         #     # 'tags__user_object_permissions__permission',
#         #     'tags__group_object_permissions',
#         #     'tags__group_object_permissions__permission',
#         # )
#         return tags_prefetch(queryset)
#
#
# class ByTagNameFilter(BaseFilterBackend):
#     def filter_queryset(self, request, queryset, view):
#         tags = request.query_params.get('tags', None)
#         if not tags:
#             return queryset
#
#         tags = force_text(tags).split(',')
#         f = Q()
#         for t in tags:
#             f |= Q(name__istartswith=t)
#         tag_queryset = Tag.objects.filter(f)
#
#         member = request.user.member
#         if not member.is_superuser:
#             tag_queryset = obj_perms_filter_objects(member, ['view_tag', 'change_tag'], tag_queryset, prefetch=False)
#
#         return queryset.filter(tags__id__in=tag_queryset)


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
        f = Q()
        for t in tags:
            if t:
                f |= Q(name__istartswith=t)
        tag_queryset = obj_perms_filter_objects(request.user.member, perms=['view_tag', 'change_tag'],
                                                queryset=Tag.objects.filter(f), prefetch=False)
        return queryset.filter(tags__id__in=tag_queryset)
