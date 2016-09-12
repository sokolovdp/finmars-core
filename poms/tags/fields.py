from __future__ import unicode_literals

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.utils.encoding import smart_text

from poms.common.fields import SlugRelatedFilteredField
from poms.obj_perms.fields import PrimaryKeyRelatedFilteredWithObjectPermissionField
from poms.tags.filters import TagContentTypeFilterBackend
from poms.tags.models import Tag
from poms.users.filters import OwnerByMasterUserFilter


class TagContentTypeField(SlugRelatedFilteredField):
    queryset = ContentType.objects
    filter_backends = [
        TagContentTypeFilterBackend
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


# class TagManyRelatedField(ManyRelatedField):
#     def to_representation(self, iterable):
#         member = self.context['request'].user.member
#         iterable = obj_perms_filter_object_list_for_view(member, iterable)
#         return super(TagManyRelatedField, self).to_representation(iterable)
#
#     def to_internal_value(self, data):
#         res = super(TagManyRelatedField, self).to_internal_value(data)
#         if data is None:
#             return res
#         data = set(data)
#         instance = self.root.instance
#         member = self.context['request'].user.member
#         if not member.is_superuser and instance:
#             # add not visible for current member tag to list...
#             # hidden_tags = []
#
#             for t in perms_prefetch(self.get_attribute(instance)):
#                 if not has_view_perms(member, t) and t.id not in data:
#                     data.add(t.id)
#                     res.append(t)
#         return res
#
#
# class TagField(FilteredPrimaryKeyRelatedField):
#     queryset = Tag.objects
#     filter_backends = [
#         OwnerByMasterUserFilter,
#     ]
#
#     def __new__(cls, *args, **kwargs):
#         if kwargs.pop('many', False):
#             return cls.tag_many_init(*args, **kwargs)
#         return super(TagField, cls).__new__(cls, *args, **kwargs)
#
#     @classmethod
#     def tag_many_init(cls, *args, **kwargs):
#         list_kwargs = {'child_relation': cls(*args, **kwargs)}
#         for key in kwargs.keys():
#             if key in MANY_RELATION_KWARGS:
#                 list_kwargs[key] = kwargs[key]
#         return TagManyRelatedField(**list_kwargs)
#
#     def get_queryset(self):
#         ctype = ContentType.objects.get_for_model(self.root.Meta.model)
#         queryset = super(TagField, self).get_queryset()
#         queryset = queryset.filter(content_types__in=[ctype.pk])
#
#         member = self.context['request'].user.member
#         queryset = obj_perms_filter_objects_for_view(member, queryset)
#         # queryset = ObjectPermissionFilter().simple_filter_queryset(member, queryset)
#         return queryset


class TagField(PrimaryKeyRelatedFilteredWithObjectPermissionField):
    queryset = Tag.objects
    filter_backends = [
        OwnerByMasterUserFilter,
    ]

    def get_queryset(self):
        queryset = super(PrimaryKeyRelatedFilteredWithObjectPermissionField, self).get_queryset()
        ctype = ContentType.objects.get_for_model(self.root.Meta.model)
        queryset = queryset.filter(content_types__in=[ctype])
        return queryset