from __future__ import unicode_literals

from poms.accounts.fields import AccountField
from poms.common.serializers import AbstractClassifierSerializer, AbstractClassifierNodeSerializer, \
    ModelWithUserCodeSerializer
from poms.counterparties.fields import ResponsibleField, CounterpartyField
from poms.obj_attrs.serializers import AbstractAttributeTypeSerializer, AbstractAttributeSerializer, \
    ModelWithAttributesSerializer
from poms.obj_perms.serializers import ModelWithObjectPermissionSerializer, \
    ReadonlyNamedModelWithObjectPermissionSerializer
from poms.portfolios.fields import PortfolioClassifierField, PortfolioAttributeTypeField
from poms.portfolios.models import PortfolioClassifier, Portfolio, PortfolioAttributeType, PortfolioAttribute
from poms.tags.fields import TagField
from poms.transactions.fields import TransactionTypeField
from poms.users.fields import MasterUserField


class PortfolioClassifierSerializer(AbstractClassifierSerializer):
    class Meta(AbstractClassifierSerializer.Meta):
        model = PortfolioClassifier


class PortfolioClassifierNodeSerializer(AbstractClassifierNodeSerializer):
    class Meta(AbstractClassifierNodeSerializer.Meta):
        model = PortfolioClassifier


class PortfolioAttributeTypeSerializer(AbstractAttributeTypeSerializer):
    classifiers = PortfolioClassifierSerializer(required=False, allow_null=True, many=True)

    class Meta(AbstractAttributeTypeSerializer.Meta):
        model = PortfolioAttributeType
        fields = AbstractAttributeTypeSerializer.Meta.fields + ['classifiers']


# class PortfolioAttributeTypeBulkObjectPermissionSerializer(AbstractBulkObjectPermissionSerializer):
#     content_objects = PortfolioAttributeTypeField(many=True, allow_null=False, allow_empty=False)
#
#     class Meta:
#         model = PortfolioAttributeType


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
    accounts_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='accounts', many=True)
    responsibles = ResponsibleField(many=True)
    responsibles_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='responsibles', many=True)
    counterparties = CounterpartyField(many=True)
    counterparties_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='counterparties', many=True)
    transaction_types = TransactionTypeField(many=True)
    transaction_types_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='transaction_types', many=True)
    attributes = PortfolioAttributeSerializer(many=True, required=False, allow_null=True)
    tags = TagField(many=True, required=False, allow_null=True)
    tags_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='tags', many=True)

    class Meta:
        model = Portfolio
        fields = [
            'url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'public_name', 'notes', 'is_default',
            'is_deleted', 'accounts', 'accounts_object', 'responsibles', 'responsibles_object', 'counterparties',
            'counterparties_object', 'transaction_types', 'transaction_types_object', 'attributes',
            'tags', 'tags_object',
        ]

# class PortfolioBulkObjectPermissionSerializer(AbstractBulkObjectPermissionSerializer):
#     content_objects = PortfolioField(many=True, allow_null=False, allow_empty=False)
#
#     class Meta:
#         model = Portfolio
