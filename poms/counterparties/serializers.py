from __future__ import unicode_literals

from poms.common.serializers import AbstractClassifierSerializer, AbstractClassifierNodeSerializer, \
    ModelWithUserCodeSerializer
from poms.counterparties.fields import ResponsibleClassifierField, \
    CounterpartyAttributeTypeField, ResponsibleAttributeTypeField, CounterpartyClassifierField, CounterpartyGroupField, \
    ResponsibleGroupField, CounterpartyField, ResponsibleField
from poms.counterparties.models import CounterpartyClassifier, Counterparty, Responsible, ResponsibleClassifier, \
    CounterpartyAttributeType, CounterpartyAttribute, ResponsibleAttributeType, ResponsibleAttribute, CounterpartyGroup, \
    ResponsibleGroup
from poms.obj_attrs.serializers import AbstractAttributeTypeSerializer, AbstractAttributeSerializer, \
    ModelWithAttributesSerializer
from poms.obj_perms.serializers import ModelWithObjectPermissionSerializer, AbstractBulkObjectPermissionSerializer
from poms.portfolios.fields import PortfolioField
from poms.tags.fields import TagField
from poms.users.fields import MasterUserField


class CounterpartyClassifierSerializer(AbstractClassifierSerializer):
    class Meta(AbstractClassifierSerializer.Meta):
        model = CounterpartyClassifier


class CounterpartyClassifierNodeSerializer(AbstractClassifierNodeSerializer):
    class Meta(AbstractClassifierNodeSerializer.Meta):
        model = CounterpartyClassifier


class CounterpartyAttributeTypeSerializer(AbstractAttributeTypeSerializer):
    classifiers = CounterpartyClassifierSerializer(required=False, allow_null=True, many=True)

    class Meta(AbstractAttributeTypeSerializer.Meta):
        model = CounterpartyAttributeType
        fields = AbstractAttributeTypeSerializer.Meta.fields + ['classifiers']


class CounterpartyAttributeTypeBulkObjectPermissionSerializer(AbstractBulkObjectPermissionSerializer):
    content_objects = CounterpartyAttributeTypeField(many=True, allow_null=False, allow_empty=False)

    class Meta:
        model = CounterpartyAttributeType


class CounterpartyAttributeSerializer(AbstractAttributeSerializer):
    attribute_type = CounterpartyAttributeTypeField()
    classifier = CounterpartyClassifierField(required=False, allow_null=True)

    class Meta(AbstractAttributeSerializer.Meta):
        model = CounterpartyAttribute
        fields = AbstractAttributeSerializer.Meta.fields + ['attribute_type', 'classifier']


class CounterpartyGroupSerializer(ModelWithObjectPermissionSerializer, ModelWithUserCodeSerializer):
    master_user = MasterUserField()
    tags = TagField(many=True, required=False, allow_null=True)

    class Meta:
        model = CounterpartyGroup
        fields = ['url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'public_name', 'notes',
                  'is_default', 'is_deleted', 'tags', ]


class CounterpartyGroupBulkObjectPermissionSerializer(AbstractBulkObjectPermissionSerializer):
    content_objects = CounterpartyGroupField(many=True, allow_null=False, allow_empty=False)

    class Meta:
        model = CounterpartyGroup


class CounterpartySerializer(ModelWithObjectPermissionSerializer, ModelWithAttributesSerializer,
                             ModelWithUserCodeSerializer):
    master_user = MasterUserField()
    group = CounterpartyGroupField()
    portfolios = PortfolioField(many=True, required=False, allow_null=True)
    attributes = CounterpartyAttributeSerializer(many=True, required=False, allow_null=True)
    tags = TagField(many=True, required=False, allow_null=True)

    class Meta:
        model = Counterparty
        fields = ['url', 'id', 'master_user', 'group', 'user_code', 'name', 'short_name', 'public_name', 'notes',
                  'is_default', 'is_valid_for_all_portfolios', 'is_deleted', 'portfolios', 'attributes', 'tags']


class CounterpartyBulkObjectPermissionSerializer(AbstractBulkObjectPermissionSerializer):
    content_objects = CounterpartyField(many=True, allow_null=False, allow_empty=False)

    class Meta:
        model = Counterparty


# ----

class ResponsibleClassifierSerializer(AbstractClassifierSerializer):
    class Meta(AbstractClassifierSerializer.Meta):
        model = ResponsibleClassifier


class ResponsibleClassifierNodeSerializer(AbstractClassifierNodeSerializer):
    class Meta(AbstractClassifierNodeSerializer.Meta):
        model = ResponsibleClassifier


class ResponsibleAttributeTypeSerializer(AbstractAttributeTypeSerializer):
    classifiers = ResponsibleClassifierSerializer(required=False, allow_null=True, many=True)

    class Meta(AbstractAttributeTypeSerializer.Meta):
        model = ResponsibleAttributeType
        fields = AbstractAttributeTypeSerializer.Meta.fields + ['classifiers']


class ResponsibleAttributeTypeBulkObjectPermissionSerializer(AbstractBulkObjectPermissionSerializer):
    content_objects = ResponsibleAttributeTypeField(many=True, allow_null=False, allow_empty=False)

    class Meta:
        model = ResponsibleAttributeType


class ResponsibleAttributeSerializer(AbstractAttributeSerializer):
    attribute_type = ResponsibleAttributeTypeField()
    classifier = ResponsibleClassifierField(required=False, allow_null=True)

    class Meta(AbstractAttributeSerializer.Meta):
        model = ResponsibleAttribute
        fields = AbstractAttributeSerializer.Meta.fields + ['attribute_type', 'classifier']


class ResponsibleGroupSerializer(ModelWithObjectPermissionSerializer, ModelWithUserCodeSerializer):
    master_user = MasterUserField()
    tags = TagField(many=True, required=False, allow_null=True)

    class Meta:
        model = ResponsibleGroup
        fields = [
            'url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'public_name', 'notes', 'is_default',
            'is_deleted', 'tags',
        ]


class ResponsibleGroupBulkObjectPermissionSerializer(AbstractBulkObjectPermissionSerializer):
    content_objects = ResponsibleGroupField(many=True, allow_null=False, allow_empty=False)

    class Meta:
        model = ResponsibleGroup


class ResponsibleSerializer(ModelWithObjectPermissionSerializer, ModelWithAttributesSerializer,
                            ModelWithUserCodeSerializer):
    master_user = MasterUserField()
    group = ResponsibleGroupField()
    portfolios = PortfolioField(many=True, required=False, allow_null=True)
    attributes = ResponsibleAttributeSerializer(many=True, required=False, allow_null=True)
    tags = TagField(many=True, required=False, allow_null=True)

    class Meta:
        model = Responsible
        fields = ['url', 'id', 'master_user', 'group', 'user_code', 'name', 'short_name', 'public_name', 'notes',
                  'is_default', 'is_valid_for_all_portfolios', 'is_deleted', 'portfolios', 'attributes', 'tags']


class ResponsibleBulkObjectPermissionSerializer(AbstractBulkObjectPermissionSerializer):
    content_objects = ResponsibleField(many=True, allow_null=False, allow_empty=False)

    class Meta:
        model = Responsible
