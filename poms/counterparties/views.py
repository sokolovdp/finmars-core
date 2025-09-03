import django_filters
from django.db.models import Q
from django_filters.rest_framework import FilterSet
from rest_framework.decorators import action
from rest_framework.response import Response

from poms.common.filters import (
    AttributeFilter,
    CharFilter,
    EntitySpecificFilter,
    GroupsAttributeFilter,
    NoOpFilter,
)
from poms.common.utils import get_list_of_entity_attributes
from poms.common.views import AbstractModelViewSet
from poms.counterparties.models import (
    Counterparty,
    CounterpartyGroup,
    Responsible,
    ResponsibleGroup,
)
from poms.counterparties.serializers import (
    CounterpartyGroupSerializer,
    CounterpartyLightSerializer,
    CounterpartySerializer,
    ResponsibleGroupSerializer,
    ResponsibleLightSerializer,
    ResponsibleSerializer,
)
from poms.obj_attrs.utils import get_attributes_prefetch
from poms.obj_attrs.views import GenericAttributeTypeViewSet, GenericClassifierViewSet
from poms.users.filters import OwnerByMasterUserFilter


class CounterpartyAttributeTypeViewSet(GenericAttributeTypeViewSet):
    target_model = Counterparty
    target_model_serializer = CounterpartySerializer
    permission_classes = GenericAttributeTypeViewSet.permission_classes + []


class CounterpartyClassifierViewSet(GenericClassifierViewSet):
    target_model = Counterparty


class CounterpartyGroupFilterSet(FilterSet):
    id = NoOpFilter()
    is_deleted = django_filters.BooleanFilter()
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()
    public_name = CharFilter()

    class Meta:
        model = CounterpartyGroup
        fields = []


class CounterpartyGroupViewSet(AbstractModelViewSet):
    queryset = CounterpartyGroup.objects.select_related("master_user")
    serializer_class = CounterpartyGroupSerializer
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMasterUserFilter,
    ]
    filter_class = CounterpartyGroupFilterSet
    ordering_fields = [
        "user_code",
        "name",
        "short_name",
        "public_name",
    ]

    def perform_destroy(self, instance):
        super().perform_destroy(instance)

        items_qs = Counterparty.objects.filter(master_user=instance.master_user, group=instance)
        default_group = CounterpartyGroup.objects.get(master_user=instance.master_user, user_code="-")

        items_qs.update(group=default_group)


class CounterpartyFilterSet(FilterSet):
    id = NoOpFilter()
    is_deleted = django_filters.BooleanFilter()
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()
    is_valid_for_all_portfolios = django_filters.BooleanFilter()
    query = CharFilter(method="query_search")

    class Meta:
        model = Counterparty
        fields = []

    def query_search(self, queryset, _, value):
        if value:
            # Split the value by spaces to get individual search terms
            search_terms = value.split()

            # Create an OR condition to search across multiple fields
            conditions = Q()
            for term in search_terms:
                conditions |= (
                    Q(user_code__icontains=term)
                    | Q(name__icontains=term)
                    | Q(short_name__icontains=term)
                    | Q(public_name__icontains=term)
                )
            queryset = queryset.filter(conditions)

        return queryset


class CounterpartyViewSet(AbstractModelViewSet):
    queryset = Counterparty.objects.select_related(
        "master_user",
        "owner",
        "group",
    ).prefetch_related("portfolios", get_attributes_prefetch())
    serializer_class = CounterpartySerializer
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMasterUserFilter,
        AttributeFilter,
        GroupsAttributeFilter,
        EntitySpecificFilter,
    ]
    filter_class = CounterpartyFilterSet
    ordering_fields = [
        "user_code",
        "name",
        "short_name",
        "public_name",
        "group",
        "group__user_code",
        "group__name",
        "group__short_name",
        "group__public_name",
    ]

    @action(
        detail=False,
        methods=["get"],
        url_path="light",
        serializer_class=CounterpartyLightSerializer,
    )
    def list_light(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginator.post_paginate_queryset(queryset, request)
        serializer = self.get_serializer(page, many=True)

        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=["get"], url_path="attributes")
    def list_attributes(self, request, *args, **kwargs):
        items = [
            {
                "key": "name",
                "name": "Name",
                "value_type": 10,
            },
            {
                "key": "short_name",
                "name": "Short name",
                "value_type": 10,
            },
            {
                "key": "user_code",
                "name": "User code",
                "value_type": 10,
            },
            {
                "key": "public_name",
                "name": "Public name",
                "value_type": 10,
            },
            {
                "key": "notes",
                "name": "Notes",
                "value_type": 10,
            },
            {
                "key": "group",
                "name": "Group",
                "value_type": "field",
                "value_entity": "counterparty-group",
                "value_content_type": "counterparties.counterpartygroup",
                "code": "user_code",
            },
            {
                "key": "portfolios",
                "name": "Portfolios",
                "value_type": "mc_field",
            },
        ]

        items += get_list_of_entity_attributes("counterparties.counterparty")

        result = {
            "count": len(items),
            "next": None,
            "previous": None,
            "results": items,
        }

        return Response(result)


class ResponsibleAttributeTypeViewSet(GenericAttributeTypeViewSet):
    target_model = Responsible
    target_model_serializer = ResponsibleSerializer

    permission_classes = GenericAttributeTypeViewSet.permission_classes + []


class ResponsibleClassifierViewSet(GenericClassifierViewSet):
    target_model = Responsible


class ResponsibleGroupFilterSet(FilterSet):
    id = NoOpFilter()
    is_deleted = django_filters.BooleanFilter()
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()

    class Meta:
        model = ResponsibleGroup
        fields = []


class ResponsibleGroupViewSet(AbstractModelViewSet):
    queryset = ResponsibleGroup.objects.select_related("master_user")
    serializer_class = ResponsibleGroupSerializer
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMasterUserFilter,
        EntitySpecificFilter,
    ]
    filter_class = ResponsibleGroupFilterSet
    ordering_fields = [
        "user_code",
        "name",
        "short_name",
        "public_name",
    ]

    def perform_destroy(self, instance):
        super().perform_destroy(instance)

        items_qs = Responsible.objects.filter(master_user=instance.master_user, group=instance)
        default_group = ResponsibleGroup.objects.get(master_user=instance.master_user, user_code="-")

        items_qs.update(group=default_group)


class ResponsibleFilterSet(FilterSet):
    id = NoOpFilter()
    is_deleted = django_filters.BooleanFilter()
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()
    public_name = CharFilter()
    is_valid_for_all_portfolios = django_filters.BooleanFilter()

    class Meta:
        model = Responsible
        fields = []


class ResponsibleViewSet(AbstractModelViewSet):
    queryset = Responsible.objects.select_related(
        "master_user",
        "owner",
        "group",
    ).prefetch_related(
        "portfolios",
        get_attributes_prefetch(),
    )
    serializer_class = ResponsibleSerializer
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMasterUserFilter,
        AttributeFilter,
        GroupsAttributeFilter,
        EntitySpecificFilter,
    ]
    filter_class = ResponsibleFilterSet
    ordering_fields = [
        "user_code",
        "name",
        "short_name",
        "public_name",
        "group",
        "group__user_code",
        "group__name",
        "group__short_name",
        "group__public_name",
    ]

    @action(
        detail=False,
        methods=["get"],
        url_path="light",
        serializer_class=ResponsibleLightSerializer,
    )
    def list_light(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginator.post_paginate_queryset(queryset, request)
        serializer = self.get_serializer(page, many=True)

        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=["get"], url_path="attributes")
    def list_attributes(self, request, *args, **kwargs):
        items = [
            {
                "key": "name",
                "name": "Name",
                "value_type": 10,
            },
            {
                "key": "short_name",
                "name": "Short name",
                "value_type": 10,
            },
            {
                "key": "user_code",
                "name": "User code",
                "value_type": 10,
            },
            {
                "key": "public_name",
                "name": "Public name",
                "value_type": 10,
            },
            {
                "key": "notes",
                "name": "Notes",
                "value_type": 10,
            },
            {
                "key": "group",
                "name": "Group",
                "value_content_type": "counterparties.responsiblegroup",
                "value_entity": "responsible-group",
                "code": "user_code",
                "value_type": "field",
            },
            {
                "key": "portfolios",
                "name": "Portfolios",
                "value_content_type": "portfolios.portfolio",
                "value_entity": "portfolio",
                "code": "user_code",
                "value_type": "mc_field",
            },
        ]

        items += get_list_of_entity_attributes("counterparties.responsible")

        result = {
            "count": len(items),
            "next": None,
            "previous": None,
            "results": items,
        }

        return Response(result)
