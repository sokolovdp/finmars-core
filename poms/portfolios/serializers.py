from __future__ import unicode_literals

from rest_framework import serializers

from poms.common.serializers import ClassifierSerializerBase
from poms.obj_attrs.serializers import AttributeTypeSerializerBase, AttributeSerializerBase
from poms.portfolios.fields import PortfolioClassifierField, PortfolioClassifierRootField, PortfolioAttributeTypeField
from poms.portfolios.models import PortfolioClassifier, Portfolio, PortfolioAttributeType, PortfolioAttribute
from poms.users.fields import MasterUserField


class PortfolioClassifierSerializer(ClassifierSerializerBase):
    # parent = PortfolioClassifierField(required=False, allow_null=True)
    # children = PortfolioClassifierField(many=True, required=False, read_only=False)

    class Meta(ClassifierSerializerBase.Meta):
        model = PortfolioClassifier


class PortfolioAttributeTypeSerializer(AttributeTypeSerializerBase):
    classifier_root = PortfolioClassifierRootField(required=False, allow_null=True)

    class Meta(AttributeTypeSerializerBase.Meta):
        model = PortfolioAttributeType
        fields = AttributeTypeSerializerBase.Meta.fields + ['classifier_root']
        update_read_only_fields = AttributeTypeSerializerBase.Meta.update_read_only_fields + ['classifier_root']


class PortfolioAttributeSerializer(AttributeSerializerBase):
    attribute_type = PortfolioAttributeTypeField()
    classifier = PortfolioClassifierField(required=False, allow_null=True)

    class Meta(AttributeSerializerBase.Meta):
        model = PortfolioAttribute
        fields = AttributeSerializerBase.Meta.fields + ['attribute_type', 'classifier']


class PortfolioSerializer(serializers.ModelSerializer):
    master_user = MasterUserField()
    attributes = PortfolioAttributeSerializer(many=True)

    class Meta:
        model = Portfolio
        fields = ['url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'notes',
                  'attributes']
