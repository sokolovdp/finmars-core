from __future__ import unicode_literals

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.utils.encoding import smart_text

from poms.common.fields import FilteredPrimaryKeyRelatedField, FilteredSlugRelatedField
from poms.tags.filters import TagContentTypeFilter
from poms.tags.models import Tag
from poms.users.filters import OwnerByMasterUserFilter


class TagContentTypeField(FilteredSlugRelatedField):
    queryset = ContentType.objects
    filter_backends = [TagContentTypeFilter]

    def __init__(self, **kwargs):
        kwargs['slug_field'] = 'model'
        super(TagContentTypeField, self).__init__(**kwargs)

    def to_internal_value(self, data):
        try:
            app_label, model = data.split('.')
            return self.get_queryset().get(app_label=app_label, model=model)
        except ObjectDoesNotExist:
            self.fail('does_not_exist', slug_name=self.slug_field, value=smart_text(data))
        except (TypeError, ValueError):
            self.fail('invalid')

    def to_representation(self, obj):
        return '%s.%s' % (obj.app_label, obj.model)


class TagField(FilteredPrimaryKeyRelatedField):
    queryset = Tag.objects
    filter_backends = [
        OwnerByMasterUserFilter,
    ]

    def get_queryset(self):
        # ctype = ContentType.objects.get_for_model(self.parent.parent.Meta.model)
        ctype = ContentType.objects.get_for_model(self.root.Meta.model)
        queryset = super(TagField, self).get_queryset()
        return queryset.filter(content_types__in=[ctype.pk])
