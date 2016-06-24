from __future__ import unicode_literals

from rest_framework import serializers

from poms.common.serializers import ClassifierSerializerBase, ClassifierNodeSerializerBase, ModelWithUserCodeSerializer
from poms.obj_attrs.serializers import AttributeTypeSerializerBase, AttributeSerializerBase, \
    ModelWithAttributesSerializer
from poms.obj_perms.serializers import ModelWithObjectPermissionSerializer
from poms.portfolios.fields import PortfolioClassifierField, PortfolioAttributeTypeField
from poms.portfolios.models import PortfolioClassifier, Portfolio, PortfolioAttributeType, PortfolioAttribute
from poms.tags.fields import TagField
from poms.users.fields import MasterUserField


class PortfolioClassifierSerializer(ClassifierSerializerBase):
    class Meta(ClassifierSerializerBase.Meta):
        model = PortfolioClassifier


class PortfolioClassifierNodeSerializer(ClassifierNodeSerializerBase):
    url = serializers.HyperlinkedIdentityField(view_name='portfolioclassifiernode-detail')

    class Meta(ClassifierNodeSerializerBase.Meta):
        model = PortfolioClassifier


class PortfolioAttributeTypeSerializer(AttributeTypeSerializerBase):
    classifiers = PortfolioClassifierSerializer(required=False, allow_null=True, many=True)

    class Meta(AttributeTypeSerializerBase.Meta):
        model = PortfolioAttributeType
        fields = AttributeTypeSerializerBase.Meta.fields + ['classifiers']


class PortfolioAttributeSerializer(AttributeSerializerBase):
    attribute_type = PortfolioAttributeTypeField()
    classifier = PortfolioClassifierField(required=False, allow_null=True)

    class Meta(AttributeSerializerBase.Meta):
        model = PortfolioAttribute
        fields = AttributeSerializerBase.Meta.fields + ['attribute_type', 'classifier']


class PortfolioSerializer(ModelWithObjectPermissionSerializer, ModelWithAttributesSerializer,
                          ModelWithUserCodeSerializer):
    master_user = MasterUserField()
    attributes = PortfolioAttributeSerializer(many=True, required=False, allow_null=True)
    tags = TagField(many=True, required=False, allow_null=True)

    class Meta:
        model = Portfolio
        fields = ['url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'notes', 'attributes', 'tags']
