import django_filters
from django.contrib.contenttypes.models import ContentType
from rest_framework.filters import BaseFilterBackend

from poms.audit.history import get_history_model_list


class HistoryFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        master_user = request.user.master_user
        return queryset.filter(info__master_user=master_user)


class ObjectHistoryContentTypeFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        ctypes = [ContentType.objects.get_for_model(model).pk for model in get_history_model_list()]
        return queryset.filter(pk__in=ctypes)


class ObjectHistoryContentTypeMultipleChoiceFilter(django_filters.MultipleChoiceFilter):
    def __init__(self, *args, **kwargs):
        queryset = ContentType.objects.all().order_by('app_label', 'model')
        queryset = ObjectHistoryContentTypeFilter().filter_queryset(None, queryset, None)
        kwargs['choices'] = [
            ('%s.%s' % (c.app_label, c.model), c.model_class()._meta.verbose_name)
            for c in queryset
            ]
        super(ObjectHistoryContentTypeMultipleChoiceFilter, self).__init__(*args, **kwargs)

    def filter(self, qs, value):
        value = value or tuple()
        cvalue = []
        for v in value:
            ctype = v.split('.')
            ctype = ContentType.objects.get_by_natural_key(*ctype)
            cvalue.append(ctype.id)
        return super(ObjectHistoryContentTypeMultipleChoiceFilter, self).filter(qs, cvalue)


class ObjectHistory4ContentTypeMultipleChoiceFilter(django_filters.MultipleChoiceFilter):
    def __init__(self, *args, **kwargs):
        queryset = ContentType.objects.all().order_by('app_label', 'model')
        queryset = ObjectHistoryContentTypeFilter().filter_queryset(None, queryset, None)
        kwargs['choices'] = [
            ('%s.%s' % (c.app_label, c.model), c.model_class()._meta.verbose_name)
            for c in queryset
            ]
        super(ObjectHistory4ContentTypeMultipleChoiceFilter, self).__init__(*args, **kwargs)

    def filter(self, qs, value):
        value = value or tuple()
        cvalue = []
        for v in value:
            ctype = v.split('.')
            ctype = ContentType.objects.get_by_natural_key(*ctype)
            cvalue.append(ctype.id)
        return super(ObjectHistory4ContentTypeMultipleChoiceFilter, self).filter(qs, cvalue)
