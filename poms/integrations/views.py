from __future__ import unicode_literals, print_function

from rest_framework.filters import FilterSet, DjangoFilterBackend, OrderingFilter, SearchFilter
from rest_framework.response import Response

from poms.common.filters import CharFilter
from poms.common.views import AbstractViewSet, AbstractModelViewSet
from poms.integrations.models import InstrumentMapping, BloombergConfig
from poms.integrations.serializers import InstrumentBloombergImportSerializer, InstrumentFileImportSerializer, \
    InstrumentMappingSerializer, BloombergConfigSerializer
from poms.users.filters import OwnerByMasterUserFilter
from poms.users.permissions import SuperUserOrReadOnly, SuperUserOnly


class InstrumentMappingFilterSet(FilterSet):
    mapping_name = CharFilter()

    class Meta:
        model = InstrumentMapping
        fields = ['mapping_name', ]


class InstrumentMappingViewSet(AbstractModelViewSet):
    queryset = InstrumentMapping.objects.prefetch_related('attributes', 'attributes__attribute_type')
    serializer_class = InstrumentMappingSerializer
    permission_classes = AbstractModelViewSet.permission_classes + [
        SuperUserOrReadOnly,
    ]
    filter_backends = [
        OwnerByMasterUserFilter,
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    ]
    filter_class = InstrumentMappingFilterSet
    ordering_fields = ['mapping_name']
    search_fields = ['mapping_name']


class BloombergConfigViewSet(AbstractModelViewSet):
    queryset = BloombergConfig.objects
    serializer_class = BloombergConfigSerializer
    permission_classes = AbstractModelViewSet.permission_classes + [
        SuperUserOnly,
    ]
    filter_backends = [
        OwnerByMasterUserFilter,
    ]


class AbstractIntegrationViewSet(AbstractViewSet):
    serializer_class = None

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        kwargs['context'] = self.get_serializer_context()
        return serializer_class(*args, **kwargs)

    def get_serializer_class(self):
        return self.serializer_class

    def get_serializer_context(self):
        return {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self
        }


class InstrumentFileImportViewSet(AbstractIntegrationViewSet):
    serializer_class = InstrumentFileImportSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class InstrumentBloombergImportViewSet(AbstractIntegrationViewSet):
    serializer_class = InstrumentBloombergImportSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
