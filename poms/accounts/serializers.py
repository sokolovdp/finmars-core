from __future__ import unicode_literals

from rest_framework import serializers

from poms.accounts.fields import AccountClassifierField, AccountAttributeTypeField, AccountTypeField
from poms.accounts.models import Account, AccountType, AccountClassifier, AccountAttributeType, AccountAttribute
from poms.common.serializers import ClassifierSerializerBase, ClassifierNodeSerializerBase, ModelWithUserCodeSerializer
from poms.obj_attrs.serializers import AbstractAttributeTypeSerializer, AbstractAttributeSerializer, \
    ModelWithAttributesSerializer
from poms.obj_perms.serializers import ModelWithObjectPermissionSerializer
from poms.portfolios.fields import PortfolioField
from poms.tags.fields import TagField
from poms.users.fields import MasterUserField


class AccountClassifierSerializer(ClassifierSerializerBase):
    class Meta(ClassifierSerializerBase.Meta):
        model = AccountClassifier


class AccountClassifierNodeSerializer(ClassifierNodeSerializerBase):
    url = serializers.HyperlinkedIdentityField(view_name='accountclassifiernode-detail')

    class Meta(ClassifierNodeSerializerBase.Meta):
        model = AccountClassifier


class AccountTypeSerializer(ModelWithObjectPermissionSerializer, ModelWithUserCodeSerializer):
    master_user = MasterUserField()
    tags = TagField(many=True, required=False, allow_null=True)

    class Meta:
        model = AccountType
        fields = ['url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'public_name', 'notes',
                  'show_transaction_details', 'transaction_details_expr', 'tags']


class AccountAttributeTypeSerializer(AbstractAttributeTypeSerializer):
    classifiers = AccountClassifierSerializer(required=False, allow_null=True, many=True)

    class Meta(AbstractAttributeTypeSerializer.Meta):
        model = AccountAttributeType
        fields = AbstractAttributeTypeSerializer.Meta.fields + ['classifiers']


class AccountAttributeSerializer(AbstractAttributeSerializer):
    attribute_type = AccountAttributeTypeField()
    classifier = AccountClassifierField(required=False, allow_null=True)

    class Meta(AbstractAttributeSerializer.Meta):
        model = AccountAttribute
        fields = AbstractAttributeSerializer.Meta.fields + ['attribute_type', 'classifier']


class AccountSerializer(ModelWithObjectPermissionSerializer, ModelWithAttributesSerializer,
                        ModelWithUserCodeSerializer):
    master_user = MasterUserField()
    type = AccountTypeField()
    portfolios = PortfolioField(many=True, required=False, allow_null=True)
    attributes = AccountAttributeSerializer(many=True, required=False, allow_null=True)
    tags = TagField(many=True, required=False, allow_null=True)

    class Meta:
        model = Account
        fields = ['url', 'id', 'master_user', 'type', 'user_code', 'name', 'short_name', 'public_name', 'notes',
                  'portfolios', 'tags', 'attributes', ]
