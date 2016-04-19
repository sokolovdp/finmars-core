from __future__ import unicode_literals

import six
from rest_framework import serializers

from poms.users.fields import MasterUserField


class AttributeTypeSerializerBase(serializers.ModelSerializer):
    master_user = MasterUserField()

    class Meta:
        fields = ['url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'notes', 'value_type', 'order']


class AttributeSerializerBase(serializers.ModelSerializer):
    class Meta:
        fields = ['id', 'value_string', 'value_float', 'value_date']


class ModelWithAttributesSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        attributes = validated_data.pop('attributes')
        instance = super(ModelWithAttributesSerializer, self).create(validated_data)
        self.save_attributes(instance, attributes, True)
        return instance

    def update(self, instance, validated_data):
        attributes = validated_data.pop('attributes')
        instance = super(ModelWithAttributesSerializer, self).update(instance, validated_data)
        self.save_attributes(instance, attributes, False)
        return instance

    def save_attributes(self, instance, attributes, created):
        attributes_field = instance._meta.get_field('attributes')
        attributes_model = attributes_field.related_model

        attributes_map = {a['attribute_type'].id: a for a in attributes}

        # TODO: add code for object level permission...
        attributes_cur_map = {a.attribute_type_id: a for a in instance.attributes.all()}

        for a in attributes:
            attribute_type_id = a['attribute_type'].id
            if attribute_type_id not in attributes_cur_map:
                attributes_model(content_object=instance, **a).save()
            else:
                attr = attributes_cur_map[attribute_type_id]
                for k, v in six.iteritems(a):
                    if k not in ['id', 'attribute_type']:
                        setattr(attr, k, v)
                attr.save()

        for attr in six.itervalues(attributes_cur_map):
            if attr.attribute_type_id not in attributes_map:
                attr.delete()
