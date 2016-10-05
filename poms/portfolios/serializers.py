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
from poms.tags.serializers import TagViewSerializer
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
    accounts_object = serializers.PrimaryKeyRelatedField(source='accounts', many=True, read_only=True)
    responsibles = ResponsibleField(many=True)
    responsibles_object = serializers.PrimaryKeyRelatedField(source='responsibles', many=True, read_only=True)
    counterparties = CounterpartyField(many=True)
    counterparties_object = serializers.PrimaryKeyRelatedField(source='counterparties', many=True, read_only=True)
    transaction_types = TransactionTypeField(many=True)
    transaction_types_object = serializers.PrimaryKeyRelatedField(source='transaction_types', many=True, read_only=True)
    attributes = PortfolioAttributeSerializer(many=True, required=False, allow_null=True)
    tags = TagField(many=True, required=False, allow_null=True)
    tags_object = TagViewSerializer(source='tags', many=True, read_only=True)

    class Meta:
        model = Portfolio
        fields = [
            'url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'public_name', 'notes', 'is_default',
            'is_deleted', 'accounts', 'accounts_object', 'responsibles', 'responsibles_object', 'counterparties',
            'counterparties_object', 'transaction_types', 'transaction_types_object', 'attributes',
            'tags', 'tags_object',
        ]

    def __init__(self, *args, **kwargs):
        super(PortfolioSerializer, self).__init__(*args, **kwargs)

        from poms.accounts.serializers import AccountViewSerializer
        self.fields['accounts_object'] = AccountViewSerializer(source='accounts', many=True, read_only=True)

        from poms.counterparties.serializers import ResponsibleViewSerializer, CounterpartyViewSerializer
        self.fields['responsibles_object'] = ResponsibleViewSerializer(source='responsibles', many=True, read_only=True)
        self.fields['counterparties_object'] = CounterpartyViewSerializer(source='counterparties', many=True,
                                                                          read_only=True)

        from poms.accounts.serializers import AccountViewSerializer
        self.fields['accounts_object'] = AccountViewSerializer(source='accounts', many=True, read_only=True)

        from poms.transactions.serializers import TransactionTypeViewSerializer
        self.fields['transaction_types_object'] = TransactionTypeViewSerializer(source='transaction_types', many=True,
                                                                                read_only=True)


class PortfolioViewSerializer(ModelWithObjectPermissionSerializer):
    class Meta:
        model = Portfolio
        fields = [
            'url', 'id', 'user_code', 'name', 'short_name', 'public_name',
        ]
