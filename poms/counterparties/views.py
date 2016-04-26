from __future__ import unicode_literals

from rest_framework.filters import DjangoFilterBackend, OrderingFilter, SearchFilter

from poms.common.filters import ClassifierFilterSetBase
from poms.common.views import ClassifierViewSetBase, PomsViewSetBase
from poms.counterparties.models import CounterpartyClassifier, Counterparty, Responsible, ResponsibleClassifier, \
    CounterpartyAttributeType, ResponsibleAttributeType
from poms.counterparties.serializers import CounterpartySerializer, ResponsibleSerializer, \
    CounterpartyClassifierSerializer, ResponsibleClassifierSerializer, CounterpartyAttributeTypeSerializer, \
    ResponsibleAttributeTypeSerializer
from poms.obj_attrs.filters import AttributePrefetchFilter
from poms.obj_attrs.views import AttributeTypeViewSetBase
from poms.tags.filters import TagPrefetchFilter
from poms.users.filters import OwnerByMasterUserFilter


class CounterpartyClassifierFilterSet(ClassifierFilterSetBase):
    class Meta(ClassifierFilterSetBase.Meta):
        model = CounterpartyClassifier


class CounterpartyClassifierViewSet(ClassifierViewSetBase):
    queryset = CounterpartyClassifier.objects.all()
    serializer_class = CounterpartyClassifierSerializer
    filter_class = CounterpartyClassifierFilterSet


class CounterpartyAttributeTypeViewSet(AttributeTypeViewSetBase):
    queryset = CounterpartyAttributeType.objects.all()
    serializer_class = CounterpartyAttributeTypeSerializer


class CounterpartyViewSet(PomsViewSetBase):
    queryset = Counterparty.objects.all()
    serializer_class = CounterpartySerializer
    filter_backends = [OwnerByMasterUserFilter, AttributePrefetchFilter, TagPrefetchFilter,
                       DjangoFilterBackend, OrderingFilter, SearchFilter]
    ordering_fields = ['user_code', 'name', 'short_name']
    search_fields = ['user_code', 'name', 'short_name']


class ResponsibleClassifierFilterSet(ClassifierFilterSetBase):
    class Meta(ClassifierFilterSetBase.Meta):
        model = ResponsibleClassifier


class ResponsibleClassifierViewSet(ClassifierViewSetBase):
    queryset = ResponsibleClassifier.objects.all()
    serializer_class = ResponsibleClassifierSerializer
    filter_class = ResponsibleClassifierFilterSet


class ResponsibleAttributeTypeViewSet(AttributeTypeViewSetBase):
    queryset = ResponsibleAttributeType.objects.all()
    serializer_class = ResponsibleAttributeTypeSerializer


class ResponsibleViewSet(PomsViewSetBase):
    queryset = Responsible.objects.all()
    serializer_class = ResponsibleSerializer
    filter_backends = [OwnerByMasterUserFilter, AttributePrefetchFilter, TagPrefetchFilter,
                       DjangoFilterBackend, OrderingFilter, SearchFilter]
    ordering_fields = ['user_code', 'name', 'short_name']
    search_fields = ['user_code', 'name', 'short_name']
