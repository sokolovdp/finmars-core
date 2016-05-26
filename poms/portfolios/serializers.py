from __future__ import unicode_literals

from rest_framework import serializers

from poms.common.serializers import ClassifierSerializerBase, ClassifierNodeSerializerBase
from poms.obj_attrs.serializers import AttributeTypeSerializerBase, AttributeSerializerBase, \
    ModelWithAttributesSerializer
from poms.portfolios.fields import PortfolioClassifierField, PortfolioClassifierRootField, PortfolioAttributeTypeField
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
    # classifier_root = PortfolioClassifierRootField(required=False, allow_null=True)
    classifiers = PortfolioClassifierSerializer(required=False, allow_null=True, many=True)

    class Meta(AttributeTypeSerializerBase.Meta):
        model = PortfolioAttributeType
        fields = AttributeTypeSerializerBase.Meta.fields + ['classifiers']
        # update_read_only_fields = AttributeTypeSerializerBase.Meta.update_read_only_fields + ['classifier_root']


class PortfolioAttributeSerializer(AttributeSerializerBase):
    attribute_type = PortfolioAttributeTypeField()
    classifier = PortfolioClassifierField(required=False, allow_null=True)

    class Meta(AttributeSerializerBase.Meta):
        model = PortfolioAttribute
        fields = AttributeSerializerBase.Meta.fields + ['attribute_type', 'classifier']


class PortfolioSerializer(ModelWithAttributesSerializer):
    master_user = MasterUserField()
    attributes = PortfolioAttributeSerializer(many=True)
    tags = TagField(many=True)

    class Meta:
        model = Portfolio
        fields = ['url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'notes', 'attributes', 'tags']
