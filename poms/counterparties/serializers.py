from __future__ import unicode_literals

from rest_framework import serializers

from poms.common.serializers import ClassifierSerializerBase, ClassifierNodeSerializerBase, ModelWithUserCodeSerializer
from poms.counterparties.fields import ResponsibleClassifierField, \
    CounterpartyAttributeTypeField, ResponsibleAttributeTypeField
from poms.counterparties.models import CounterpartyClassifier, Counterparty, Responsible, ResponsibleClassifier, \
    CounterpartyAttributeType, CounterpartyAttribute, ResponsibleAttributeType
from poms.obj_attrs.serializers import AttributeTypeSerializerBase, AttributeSerializerBase, \
    ModelWithAttributesSerializer
from poms.tags.fields import TagField
from poms.users.fields import MasterUserField


class CounterpartyClassifierSerializer(ClassifierSerializerBase):
    class Meta(ClassifierSerializerBase.Meta):
        model = CounterpartyClassifier


class CounterpartyClassifierNodeSerializer(ClassifierNodeSerializerBase):
    url = serializers.HyperlinkedIdentityField(view_name='counterpartyclassifiernode-detail')

    class Meta(ClassifierNodeSerializerBase.Meta):
        model = CounterpartyClassifier


class CounterpartyAttributeTypeSerializer(AttributeTypeSerializerBase):
    classifiers = CounterpartyClassifierSerializer(required=False, allow_null=True, many=True)

    class Meta(AttributeTypeSerializerBase.Meta):
        model = CounterpartyAttributeType
        fields = AttributeTypeSerializerBase.Meta.fields + ['classifiers']


class CounterpartyAttributeSerializer(AttributeSerializerBase):
    attribute_type = CounterpartyAttributeTypeField()
    classifier = ResponsibleClassifierField(required=False, allow_null=True)

    class Meta(AttributeSerializerBase.Meta):
        model = CounterpartyAttribute
        fields = AttributeSerializerBase.Meta.fields + ['attribute_type', 'classifier']


class CounterpartySerializer(ModelWithAttributesSerializer, ModelWithUserCodeSerializer):
    master_user = MasterUserField()
    attributes = CounterpartyAttributeSerializer(many=True, required=False, allow_null=True)
    tags = TagField(many=True, required=False, allow_null=True)

    class Meta:
        model = Counterparty
        fields = ['url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'notes', 'attributes', 'tags']


class ResponsibleClassifierSerializer(ClassifierSerializerBase):
    class Meta(ClassifierSerializerBase.Meta):
        model = ResponsibleClassifier


class ResponsibleClassifierNodeSerializer(ClassifierNodeSerializerBase):
    url = serializers.HyperlinkedIdentityField(view_name='responsibleclassifiernode-detail')

    class Meta(ClassifierNodeSerializerBase.Meta):
        model = ResponsibleClassifier


class ResponsibleAttributeTypeSerializer(AttributeTypeSerializerBase):
    classifiers = ResponsibleClassifierSerializer(required=False, allow_null=True, many=True)

    class Meta(AttributeTypeSerializerBase.Meta):
        model = ResponsibleAttributeType
        fields = AttributeTypeSerializerBase.Meta.fields + ['classifiers']


class ResponsibleAttributeSerializer(AttributeSerializerBase):
    attribute_type = ResponsibleAttributeTypeField()
    classifier = ResponsibleClassifierField(required=False, allow_null=True)

    class Meta(AttributeSerializerBase.Meta):
        model = CounterpartyAttribute
        fields = AttributeSerializerBase.Meta.fields + ['attribute_type', 'classifier']


class ResponsibleSerializer(ModelWithAttributesSerializer, ModelWithUserCodeSerializer):
    master_user = MasterUserField()
    attributes = ResponsibleAttributeSerializer(many=True, required=False, allow_null=True)
    tags = TagField(many=True, required=False, allow_null=True)

    class Meta:
        model = Responsible
        fields = ['url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'notes', 'attributes', 'tags']
