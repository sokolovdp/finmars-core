import django_filters
import six
from django_filters.fields import Lookup
from rest_framework.filters import FilterSet

from poms.common.views import AbstractModelViewSet
from poms.ui.models import TemplateListLayout, TemplateEditLayout, ListLayout, EditLayout
from poms.ui.serializers import TemplateListLayoutSerializer, ListLayoutSerializer, TemplateEditLayoutSerializer, \
    EditLayoutSerializer
from poms.users.filters import OwnerByMasterUserFilter, OwnerByMemberFilter
from poms.users.permissions import SuperUserOnly


class LayoutContentTypeFilter(django_filters.CharFilter):
    def filter(self, qs, value):
        if isinstance(value, Lookup):
            lookup = six.text_type(value.lookup_type)
            value = value.value
        else:
            lookup = self.lookup_expr
        if value in ([], (), {}, None, ''):
            return qs
        if self.distinct:
            qs = qs.distinct()

        app_label, model = value.split('.')
        qs = self.get_method(qs)(**{
            'content_type__app_label': app_label,
            'content_type__model__%s' % (lookup): model,
        })
        return qs


class TemplateListLayoutFilterSet(FilterSet):
    content_type = LayoutContentTypeFilter()

    class Meta:
        model = TemplateListLayout
        fields = ['name', 'content_type']


class TemplateListLayoutViewSet(AbstractModelViewSet):
    queryset = TemplateListLayout.objects.prefetch_related('master_user', 'content_type')
    serializer_class = TemplateListLayoutSerializer
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMasterUserFilter,
    ]
    filter_class = TemplateListLayoutFilterSet
    permission_classes = AbstractModelViewSet.permission_classes + [
        SuperUserOnly
    ]
    ordering_fields = ['name']
    search_fields = ['name']


class TemplateEditLayoutFilterSet(FilterSet):
    content_type = LayoutContentTypeFilter()

    class Meta:
        model = TemplateEditLayout
        fields = ['content_type']


class TemplateEditLayoutViewSet(AbstractModelViewSet):
    queryset = TemplateEditLayout.objects.prefetch_related('master_user', 'content_type')
    serializer_class = TemplateEditLayoutSerializer
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMasterUserFilter,
    ]
    permission_classes = AbstractModelViewSet.permission_classes + [
        SuperUserOnly
    ]
    filter_class = TemplateEditLayoutFilterSet
    ordering_fields = []
    search_fields = []


class ListLayoutFilterSet(FilterSet):
    content_type = LayoutContentTypeFilter()

    class Meta:
        model = ListLayout
        fields = ['name', 'content_type']


class ListLayoutViewSet(AbstractModelViewSet):
    queryset = ListLayout.objects.prefetch_related('member', 'content_type')
    serializer_class = ListLayoutSerializer
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMemberFilter,
    ]
    filter_class = ListLayoutFilterSet
    ordering_fields = ['name']
    search_fields = ['name']


class EditLayoutFilterSet(FilterSet):
    content_type = LayoutContentTypeFilter()

    class Meta:
        model = EditLayout
        fields = ['content_type']


class EditLayoutViewSet(AbstractModelViewSet):
    queryset = EditLayout.objects.select_related('member', 'content_type')
    serializer_class = EditLayoutSerializer
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMemberFilter,
    ]
    filter_class = EditLayoutFilterSet
    ordering_fields = []
    search_fields = []
