from __future__ import unicode_literals

from poms.common.serializers import AbstractClassifierSerializer, AbstractClassifierNodeSerializer, \
    ModelWithUserCodeSerializer
from poms.counterparties.fields import ResponsibleClassifierField, \
    CounterpartyAttributeTypeField, ResponsibleAttributeTypeField, CounterpartyClassifierField, CounterpartyGroupField, \
    ResponsibleGroupField
from poms.counterparties.models import CounterpartyClassifier, Counterparty, Responsible, ResponsibleClassifier, \
    CounterpartyAttributeType, CounterpartyAttribute, ResponsibleAttributeType, ResponsibleAttribute, CounterpartyGroup, \
    ResponsibleGroup
from poms.obj_attrs.serializers import AbstractAttributeTypeSerializer, AbstractAttributeSerializer, \
    ModelWithAttributesSerializer
from poms.obj_perms.serializers import ModelWithObjectPermissionSerializer
from poms.portfolios.fields import PortfolioField
from poms.tags.fields import TagField
from poms.users.fields import MasterUserField


class CounterpartyClassifierSerializer(AbstractClassifierSerializer):
    class Meta(AbstractClassifierSerializer.Meta):
        model = CounterpartyClassifier


class CounterpartyClassifierNodeSerializer(AbstractClassifierNodeSerializer):
    # url = serializers.HyperlinkedIdentityField(view_name='counterpartyclassifiernode-detail')

    class Meta(AbstractClassifierNodeSerializer.Meta):
        model = CounterpartyClassifier


class CounterpartyAttributeTypeSerializer(AbstractAttributeTypeSerializer):
    classifiers = CounterpartyClassifierSerializer(required=False, allow_null=True, many=True)

    class Meta(AbstractAttributeTypeSerializer.Meta):
        model = CounterpartyAttributeType
        fields = AbstractAttributeTypeSerializer.Meta.fields + ['classifiers']


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
        fields = ['url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'public_name', 'notes', 'is_default',
                  'tags', ]


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
                  'is_default', 'is_valid_for_all_portfolios', 'portfolios', 'attributes', 'tags']


# ----

class ResponsibleClassifierSerializer(AbstractClassifierSerializer):
    class Meta(AbstractClassifierSerializer.Meta):
        model = ResponsibleClassifier


class ResponsibleClassifierNodeSerializer(AbstractClassifierNodeSerializer):
    # url = serializers.HyperlinkedIdentityField(view_name='responsibleclassifiernode-detail')

    class Meta(AbstractClassifierNodeSerializer.Meta):
        model = ResponsibleClassifier


class ResponsibleAttributeTypeSerializer(AbstractAttributeTypeSerializer):
    classifiers = ResponsibleClassifierSerializer(required=False, allow_null=True, many=True)

    class Meta(AbstractAttributeTypeSerializer.Meta):
        model = ResponsibleAttributeType
        fields = AbstractAttributeTypeSerializer.Meta.fields + ['classifiers']


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
        fields = ['url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'public_name', 'notes', 'is_default',
                  'tags', ]


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
                  'is_default', 'is_valid_for_all_portfolios', 'portfolios', 'attributes', 'tags']
