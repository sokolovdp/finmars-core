from __future__ import unicode_literals

import six
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from poms.common.serializers import ModelWithUserCodeSerializer
from poms.obj_attrs.models import AttributeTypeBase
from poms.obj_attrs.utils import get_attr_type_model, get_attr_type_view_perms
from poms.obj_perms.serializers import ModelWithObjectPermissionSerializer
from poms.obj_perms.utils import obj_perms_filter_objects, has_view_perms
from poms.users.fields import MasterUserField


class AttributeTypeOptionIsHiddenField(serializers.BooleanField):
    def __init__(self, **kwargs):
        kwargs['required'] = False
        kwargs['default'] = False
        # kwargs['allow_null'] = True
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


class AttributeTypeSerializerBase(ModelWithObjectPermissionSerializer, ModelWithUserCodeSerializer):
    master_user = MasterUserField()
    is_hidden = AttributeTypeOptionIsHiddenField()

    class Meta:
        fields = ['url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'public_name', 'notes', 'value_type',
                  'order', 'is_hidden']
        update_read_only_fields = ['value_type']

    def __init__(self, *args, **kwargs):
        super(AttributeTypeSerializerBase, self).__init__(*args, **kwargs)

        request = self.context.get('request', None)
        if request and request.method in ['PUT', 'PATCH']:
            update_read_only_fields = getattr(self.Meta, 'update_read_only_fields', None)
            for name, field in six.iteritems(self.fields):
                if name in update_read_only_fields:
                    field.read_only = True

    def validate(self, attrs):
        attrs = super(AttributeTypeSerializerBase, self).validate(attrs)
        classifiers = attrs.get('classifiers', None)
        if classifiers:
            self._validate_classifiers(classifiers, id_set=set(), user_code_set=set())
        return attrs

    def _validate_classifiers(self, classifiers, id_set, user_code_set):
        for c in classifiers:
            c_id = c.get('id', None)
            c_user_code = c.get('user_code', None)
            if c_id and c_id in id_set:
                raise ValidationError("non unique id")
            if c_user_code and c_user_code in user_code_set:
                raise ValidationError("non unique user_code")
            if c_id:
                id_set.add(c_id)
            if c_user_code:
                user_code_set.add(c_user_code)
            children = c.get('get_children', c.pop('children', []))
            self._validate_classifiers(children, id_set, user_code_set)

    def create(self, validated_data):
        member = self.context['request'].user.member
        is_hidden = validated_data.pop('is_hidden', False)
        classifiers = validated_data.pop('classifiers', None)
        instance = super(AttributeTypeSerializerBase, self).create(validated_data)
        instance.options.create(member=member, is_hidden=is_hidden)
        self.save_classifiers(instance, classifiers)
        return instance

    def update(self, instance, validated_data):
        member = self.context['request'].user.member
        is_hidden = validated_data.pop('is_hidden', False)
        classifiers = validated_data.pop('classifiers', None)
        instance = super(AttributeTypeSerializerBase, self).update(instance, validated_data)
        instance.options.update_or_create(member=member, defaults={'is_hidden': is_hidden})
        self.save_classifiers(instance, classifiers)
        return instance

    def save_classifiers(self, instance, classifier_tree):
        if instance.value_type != AttributeTypeBase.CLASSIFIER:
            return
        if classifier_tree is None:
            return
        if len(classifier_tree) == 0:
            instance.classifiers.all().delete()
            return

        classifier_model = instance._meta.get_field('classifiers').related_model

        processed = set()
        for node in classifier_tree:
            self.save_classifier(instance, node, None, processed, classifier_model)

        instance.classifiers.exclude(pk__in=processed).delete()

    def save_classifier(self, instance, node, parent, processed, classifier_model):
        if 'id' in node:
            try:
                o = instance.classifiers.get(pk=node.pop('id'))
            except ObjectDoesNotExist:
                o = classifier_model()
        else:
            o = classifier_model()
        o.parent = parent
        o.attribute_type = instance
        children = node.pop('get_children', node.pop('children', []))
        for k, v in six.iteritems(node):
            setattr(o, k, v)
        o.save()
        processed.add(o.id)

        for c in children:
            self.save_classifier(instance, c, o, processed, classifier_model)


class AttributeListSerializer(serializers.ListSerializer):
    def get_attribute(self, instance):
        member = self.context['request'].user.member
        if member.is_superuser:
            return instance.attributes
        master_user = self.context['request'].user.master_user
        attr_type_model = get_attr_type_model(instance)
        attr_types = attr_type_model.objects.filter(master_user=master_user)
        attr_types = obj_perms_filter_objects(member, get_attr_type_view_perms(attr_type_model), attr_types)
        return instance.attributes.filter(attribute_type__in=attr_types)


class AttributeSerializerBase(serializers.ModelSerializer):
    class Meta:
        list_serializer_class = AttributeListSerializer
        fields = ['value_string', 'value_float', 'value_date']

    def validate(self, attrs):
        attribute_type = attrs['attribute_type']
        if attribute_type.value_type == AttributeTypeBase.CLASSIFIER:
            classifier = attrs.get('classifier', None)
            if classifier is None:
                raise ValidationError({'classifier': _('This field may not be null.')})
            if classifier.attribute_type_id != attribute_type.id:
                raise ValidationError(
                    {'classifier': _('Invalid pk "%(pk)s" - object does not exist.') % {'pk': classifier.id}})
        return attrs


class ModelWithAttributesSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        attributes = validated_data.pop('attributes', None)
        instance = super(ModelWithAttributesSerializer, self).create(validated_data)
        self.save_attributes(instance, attributes, True)
        return instance

    def update(self, instance, validated_data):
        attributes = validated_data.pop('attributes', None)
        instance = super(ModelWithAttributesSerializer, self).update(instance, validated_data)
        self.save_attributes(instance, attributes, False)
        return instance

    def save_attributes(self, instance, attributes, created):
        if attributes is None:
            return

        member = self.context['request'].user.member
        cur_attrs = {a.attribute_type_id: a
                     for a in instance.attributes.select_related('attribute_type').all()}
        processed = set()

        for attr in attributes:
            attr_type = attr['attribute_type']
            if has_view_perms(member, attr_type):
                if attr_type.id in processed:
                    raise ValidationError("Duplicated attribute type %s" % attr_type.id)
                processed.add(attr_type.id)

                if attr_type.id in cur_attrs:
                    cur_attr = cur_attrs[attr_type.id]
                    # verify value_ and classifier -> DONE in AttributeSerializerBase
                    for k, v in six.iteritems(attr):
                        if k not in ['id', 'attribute_type']:
                            setattr(cur_attr, k, v)
                    cur_attr.save()
                else:
                    # verify value_ and classifier -> DONE in AttributeSerializerBase
                    instance.attributes.create(**attr)
            else:
                # perms error...
                pass

        for attr in six.itervalues(cur_attrs):
            # add attrs that not visible for current member
            attr_type = attr.attribute_type
            if not has_view_perms(member, attr_type):
                processed.add(attr_type.id)

        instance.attributes.exclude(attribute_type_id__in=processed).delete()

        # cur_attrs = {a.attribute_type_id: a for a in instance.attributes.all()}
        # new_attrs = {a['attribute_type'].id: a for a in attributes}
        #
        # has_changes = False
        #
        # processed = set()
        # for new_attr in attributes:
        #     attribute_type_id = new_attr['attribute_type'].id
        #     if attribute_type_id in processed:
        #         raise ValidationError("Duplicated attribute type %s" % attribute_type_id)
        #     processed.add(attribute_type_id)
        #     if attribute_type_id in cur_attrs:
        #         cur_attr = cur_attrs[attribute_type_id]
        #         # TODO: verify value_ and classifier
        #         for k, v in six.iteritems(new_attr):
        #             if k not in ['id', 'attribute_type']:
        #                 setattr(cur_attr, k, v)
        #         cur_attr.save()
        #     else:
        #         has_changes = True
        #         instance.attributes.create(**new_attr)
        #
        # for k, v in six.iteritems(cur_attrs):
        #     if k not in new_attrs:
        #         has_changes = True
        #         instance.attributes.exclude(attribute_type_id__in=processed).delete()

        # TODO: invalidate cache for instance.attributes, how prefetch related?
        # need only on add and delete operation
        instance.attributes.update()
