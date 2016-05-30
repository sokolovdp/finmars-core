from __future__ import unicode_literals

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.utils.encoding import smart_text
from rest_framework.relations import MANY_RELATION_KWARGS, ManyRelatedField

from poms.common.fields import FilteredPrimaryKeyRelatedField, FilteredSlugRelatedField
from poms.obj_perms.utils import obj_perms_filter_objects_for_view, \
    obj_perms_filter_object_list_for_view, has_view_perms, perms_prefetch
from poms.tags.filters import TagContentTypeFilter
from poms.tags.models import Tag
from poms.users.filters import OwnerByMasterUserFilter


class TagContentTypeField(FilteredSlugRelatedField):
    queryset = ContentType.objects
    filter_backends = [
        TagContentTypeFilter
    ]

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


class TagManyRelatedField(ManyRelatedField):
    # def get_attribute(self, instance):
    #     res = super(TagManyRelatedField, self).get_attribute(instance)
    #     member = self.context['request'].user.member
    #     res = obj_perms_filter_object_list(member, ['change_tag'], res)
    #     return res

    def to_representation(self, iterable):
        member = self.context['request'].user.member
        iterable = obj_perms_filter_object_list_for_view(member, iterable)
        return super(TagManyRelatedField, self).to_representation(iterable)

    def to_internal_value(self, data):
        res = super(TagManyRelatedField, self).to_internal_value(data)
        if data is None:
            return res

        data = set(data)
        print('1: ', data, res)
        instance = self.root.instance
        member = self.context['request'].user.member
        if not member.is_superuser and instance:
            # add not visible for current member tag to list...
            hidden_tags = []
            for t in perms_prefetch(instance.tags).all():
                if not has_view_perms(member, t) and t.id not in data:
                    data.add(t.id)
                    res.append(t)
        print('2: ', data, res)
        return res


class TagField(FilteredPrimaryKeyRelatedField):
    queryset = Tag.objects
    filter_backends = [
        OwnerByMasterUserFilter,
    ]

    def __new__(cls, *args, **kwargs):
        if kwargs.pop('many', False):
            return cls.tag_many_init(*args, **kwargs)
        return super(TagField, cls).__new__(cls, *args, **kwargs)

    @classmethod
    def tag_many_init(cls, *args, **kwargs):
        list_kwargs = {'child_relation': cls(*args, **kwargs)}
        for key in kwargs.keys():
            if key in MANY_RELATION_KWARGS:
                list_kwargs[key] = kwargs[key]
        return TagManyRelatedField(**list_kwargs)

    def get_queryset(self):
        ctype = ContentType.objects.get_for_model(self.root.Meta.model)
        queryset = super(TagField, self).get_queryset()
        queryset = queryset.filter(content_types__in=[ctype.pk])

        member = self.context['request'].user.member
        queryset = obj_perms_filter_objects_for_view(member, queryset)
        # queryset = ObjectPermissionFilter().simple_filter_queryset(member, queryset)
        return queryset
