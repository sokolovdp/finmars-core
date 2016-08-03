from __future__ import unicode_literals

from rest_framework import serializers

from poms.accounts.fields import AccountField
from poms.common.serializers import AbstractClassifierSerializer, AbstractClassifierNodeSerializer, \
    ModelWithUserCodeSerializer
from poms.counterparties.fields import ResponsibleField, CounterpartyField
from poms.obj_attrs.serializers import AbstractAttributeTypeSerializer, AbstractAttributeSerializer, \
    ModelWithAttributesSerializer
from poms.obj_perms.serializers import ModelWithObjectPermissionSerializer
from poms.portfolios.fields import PortfolioClassifierField, PortfolioAttributeTypeField
from poms.portfolios.models import PortfolioClassifier, Portfolio, PortfolioAttributeType, PortfolioAttribute
from poms.tags.fields import TagField
from poms.transactions.fields import TransactionTypeField
from poms.users.fields import MasterUserField


class PortfolioClassifierSerializer(AbstractClassifierSerializer):
    class Meta(AbstractClassifierSerializer.Meta):
        model = PortfolioClassifier


class PortfolioClassifierNodeSerializer(AbstractClassifierNodeSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='portfolioclassifiernode-detail')

    class Meta(AbstractClassifierNodeSerializer.Meta):
        model = PortfolioClassifier


class PortfolioAttributeTypeSerializer(AbstractAttributeTypeSerializer):
    classifiers = PortfolioClassifierSerializer(required=False, allow_null=True, many=True)

    class Meta(AbstractAttributeTypeSerializer.Meta):
        model = PortfolioAttributeType
        fields = AbstractAttributeTypeSerializer.Meta.fields + ['classifiers']


class PortfolioAttributeSerializer(AbstractAttributeSerializer):
    attribute_type = PortfolioAttributeTypeField()
    classifier = PortfolioClassifierField(required=False, allow_null=True)

    class Meta(AbstractAttributeSerializer.Meta):
        model = PortfolioAttribute
        fields = AbstractAttributeSerializer.Meta.fields + ['attribute_type', 'classifier']


class PortfolioSerializer(ModelWithObjectPermissionSerializer, ModelWithAttributesSerializer,
                          ModelWithUserCodeSerializer):
    master_user = MasterUserField()
    accounts = AccountField(many=True)
    responsibles = ResponsibleField(many=True)
    counterparties = CounterpartyField(many=True)
    transaction_types = TransactionTypeField(many=True)
    attributes = PortfolioAttributeSerializer(many=True, required=False, allow_null=True)
    tags = TagField(many=True, required=False, allow_null=True)

    class Meta:
        model = Portfolio
        fields = ['url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'public_name', 'notes', 'is_default',
                  'accounts', 'responsibles', 'counterparties', 'transaction_types', 'attributes', 'tags']
