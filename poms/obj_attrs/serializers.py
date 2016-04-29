from __future__ import unicode_literals

import six
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from poms.users.fields import MasterUserField


class AttributeTypeOptionIsHiddenField(serializers.BooleanField):
    def __init__(self, **kwargs):
        super(AttributeTypeOptionIsHiddenField, self).__init__(**kwargs)

    def get_attribute(self, obj):
        return obj

    def to_representation(self, value):
        # some "optimization" to use preloaded data through prefetch_related
        member = self.context['request'].user.member
        for o in value.options.all():
            if o.member_id == member.id:
                return o.is_hidden
        return False


class AttributeTypeSerializerBase(serializers.ModelSerializer):
    master_user = MasterUserField()
    is_hidden = AttributeTypeOptionIsHiddenField()

    class Meta:
        fields = ['url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'notes', 'value_type', 'order',
                  'is_hidden']
        update_read_only_fields = ['value_type']

    def get_fields(self):
        fields = super(AttributeTypeSerializerBase, self).get_fields()

        request = self.context.get('request', None)
        if request and request.method in ['PUT', 'PATCH']:
            update_read_only_fields = getattr(self.Meta, 'update_read_only_fields', None)
            for name, field in six.iteritems(fields):
                if name in update_read_only_fields:
                    field.read_only = True

        return fields

    def create(self, validated_data):
        is_hidden = validated_data.pop('is_hidden', False)
        instance = super(AttributeTypeSerializerBase, self).create(validated_data)
        member = self.context['request'].user.member
        instance.options.create(member=member, is_hidden=is_hidden)
        return instance

    def update(self, instance, validated_data):
        is_hidden = validated_data.pop('is_hidden', False)
        instance = super(AttributeTypeSerializerBase, self).update(instance, validated_data)
        member = self.context['request'].user.member
        instance.options.update_or_create(member=member, defaults={'is_hidden': is_hidden})
        return instance


# class AttributeListSerializer(serializers.ListSerializer):
#     def get_attribute(self, instance):
#         member = self.context['request'].user.member
#         master_user = self.context['request'].user.master_user
#         attr_type_model = get_attr_type_model(instance)
#         attr_types = attr_type_model.objects.filter(master_user=master_user)
#         attr_types = obj_perms_filter_objects(member, get_attr_type_view_perms(attr_type_model), attr_types)
#         return instance.attributes.filter(attribute_type__in=attr_types)


class AttributeSerializerBase(serializers.ModelSerializer):
    class Meta:
        # list_serializer_class = AttributeListSerializer
        fields = ['value_string', 'value_float', 'value_date']


class ModelWithAttributesSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        attributes = validated_data.pop('attributes', None)
        instance = super(ModelWithAttributesSerializer, self).create(validated_data)
        if attributes:
            self.save_attributes(instance, attributes, True)
        return instance

    def update(self, instance, validated_data):
        attributes = validated_data.pop('attributes', None)
        instance = super(ModelWithAttributesSerializer, self).update(instance, validated_data)
        if attributes is not None:
            self.save_attributes(instance, attributes, False)
        return instance

    def save_attributes(self, instance, attributes, created):
        cur_attrs = {a.attribute_type_id: a for a in instance.attributes.all()}

        processed = set()
        for new_attr in attributes:
            attribute_type_id = new_attr['attribute_type'].id
            if attribute_type_id in processed:
                raise ValidationError("Duplicated attribute type %s" % attribute_type_id)
            processed.add(attribute_type_id)
            if attribute_type_id in cur_attrs:
                cur_attr = cur_attrs[attribute_type_id]
                # TODO: verify value_ and classifier
                for k, v in six.iteritems(new_attr):
                    if k not in ['id', 'attribute_type']:
                        setattr(cur_attr, k, v)
                cur_attr.save()
            else:
                instance.attributes.create(**new_attr)
        instance.attributes.exclude(attribute_type_id__in=processed).delete()

        # TODO: invalidate cache for instance.attributes, how prefetch related?
        instance.attributes.update()
        # instance.attributes.select_related('attribute_type').all()
