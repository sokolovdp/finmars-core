from __future__ import unicode_literals

from poms.common.serializers import ClassifierSerializerBase
from poms.counterparties.fields import CounterpartyClassifierField, ResponsibleClassifierField, \
    CounterpartyClassifierRootField, CounterpartyAttributeTypeField, ResponsibleClassifierRootField, \
    ResponsibleAttributeTypeField
from poms.counterparties.models import CounterpartyClassifier, Counterparty, Responsible, ResponsibleClassifier, \
    CounterpartyAttributeType, CounterpartyAttribute, ResponsibleAttributeType
from poms.obj_attrs.serializers import AttributeTypeSerializerBase, AttributeSerializerBase, \
    ModelWithAttributesSerializer
from poms.users.fields import MasterUserField


class CounterpartyClassifierSerializer(ClassifierSerializerBase):
    # parent = CounterpartyClassifierField(required=False, allow_null=True)
    # children = CounterpartyClassifierField(many=True, required=False, read_only=False)

    class Meta(ClassifierSerializerBase.Meta):
        model = CounterpartyClassifier


class CounterpartyAttributeTypeSerializer(AttributeTypeSerializerBase):
    classifier_root = CounterpartyClassifierRootField(required=False, allow_null=True)

    class Meta(AttributeTypeSerializerBase.Meta):
        model = CounterpartyAttributeType
        fields = AttributeTypeSerializerBase.Meta.fields + ['classifier_root']
        update_read_only_fields = AttributeTypeSerializerBase.Meta.update_read_only_fields + ['classifier_root']


class CounterpartyAttributeSerializer(AttributeSerializerBase):
    attribute_type = CounterpartyAttributeTypeField()
    classifier = ResponsibleClassifierField(required=False, allow_null=True)

    class Meta(AttributeSerializerBase.Meta):
        model = CounterpartyAttribute
        fields = AttributeSerializerBase.Meta.fields + ['attribute_type', 'classifier']


class CounterpartySerializer(ModelWithAttributesSerializer):
    master_user = MasterUserField()
    attributes = CounterpartyAttributeSerializer(many=True)

    class Meta:
        model = Counterparty
        fields = ['url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'notes', 'attributes']


class ResponsibleClassifierSerializer(ClassifierSerializerBase):
    # parent = ResponsibleClassifierField(required=False, allow_null=True)
    # children = ResponsibleClassifierField(many=True, required=False, read_only=False)

    class Meta(ClassifierSerializerBase.Meta):
        model = ResponsibleClassifier


class ResponsibleAttributeTypeSerializer(AttributeTypeSerializerBase):
    classifier_root = ResponsibleClassifierRootField(required=False, allow_null=True)

    class Meta(AttributeTypeSerializerBase.Meta):
        model = ResponsibleAttributeType
        fields = AttributeTypeSerializerBase.Meta.fields + ['classifier_root']
        update_read_only_fields = AttributeTypeSerializerBase.Meta.update_read_only_fields + ['classifier_root']


class ResponsibleAttributeSerializer(AttributeSerializerBase):
    attribute_type = ResponsibleAttributeTypeField()
    classifier = ResponsibleClassifierField(required=False, allow_null=True)

    class Meta(AttributeSerializerBase.Meta):
        model = CounterpartyAttribute
        fields = AttributeSerializerBase.Meta.fields + ['attribute_type', 'classifier']


class ResponsibleSerializer(ModelWithAttributesSerializer):
    master_user = MasterUserField()
    attributes = ResponsibleAttributeSerializer(many=True)

    class Meta:
        model = Responsible
        fields = ['url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'notes', 'attributes']
