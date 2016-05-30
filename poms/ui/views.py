# Create your views here.
from rest_framework.filters import FilterSet, DjangoFilterBackend, OrderingFilter, SearchFilter

from poms.common.views import PomsViewSetBase
from poms.ui.models import TemplateListLayout, TemplateEditLayout, ListLayout, EditLayout
from poms.ui.serializers import TemplateListLayoutSerializer, ListLayoutSerializer, TemplateEditLayoutSerializer, \
    EditLayoutSerializer
from poms.users.filters import OwnerByMasterUserFilter, OwnerByMemberFilter
from poms.users.permissions import SuperUserOnly


class TemplateListLayoutFilterSet(FilterSet):
    class Meta:
        model = TemplateListLayout
        fields = ['name']


class TemplateListLayoutViewSet(PomsViewSetBase):
    queryset = TemplateListLayout.objects.prefetch_related('master_user', 'content_type')
    serializer_class = TemplateListLayoutSerializer
    filter_backends = [
        OwnerByMasterUserFilter,
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    ]
    filter_class = TemplateListLayoutFilterSet
    permission_classes = PomsViewSetBase.permission_classes + [
        SuperUserOnly
    ]
    ordering_fields = ['name']
    search_fields = ['name']


class TemplateEditLayoutViewSet(PomsViewSetBase):
    queryset = TemplateEditLayout.objects.prefetch_related('master_user', 'content_type')
    serializer_class = TemplateEditLayoutSerializer
    filter_backends = [
        OwnerByMasterUserFilter,
        OrderingFilter,
        SearchFilter,
    ]
    permission_classes = PomsViewSetBase.permission_classes + [
        SuperUserOnly
    ]
    ordering_fields = []
    search_fields = []


class ListLayoutViewSet(PomsViewSetBase):
    queryset = ListLayout.objects.prefetch_related('member', 'content_type')
    serializer_class = ListLayoutSerializer
    filter_backends = [
        OwnerByMemberFilter,
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    ]
    ordering_fields = ['name']
    search_fields = ['name']


class EditLayoutViewSet(PomsViewSetBase):
    queryset = EditLayout.objects.prefetch_related('member', 'content_type')
    serializer_class = EditLayoutSerializer
    filter_backends = [
        OwnerByMemberFilter,
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    ]
    ordering_fields = []
    search_fields = []

