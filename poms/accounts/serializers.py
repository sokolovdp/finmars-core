from __future__ import unicode_literals

from poms.accounts.fields import AccountClassifierField, AccountAttributeTypeField, AccountTypeField, \
    AccountTypeDefault, \
    AccountField
from poms.accounts.models import Account, AccountType, AccountClassifier, AccountAttributeType, AccountAttribute
from poms.common.serializers import AbstractClassifierSerializer, AbstractClassifierNodeSerializer, \
    ModelWithUserCodeSerializer
from poms.obj_attrs.serializers import AbstractAttributeTypeSerializer, AbstractAttributeSerializer, \
    ModelWithAttributesSerializer
from poms.obj_perms.serializers import ModelWithObjectPermissionSerializer, AbstractBulkObjectPermissionSerializer
from poms.portfolios.fields import PortfolioField
from poms.tags.fields import TagField
from poms.users.fields import MasterUserField


class AccountClassifierSerializer(AbstractClassifierSerializer):
    class Meta(AbstractClassifierSerializer.Meta):
        model = AccountClassifier


class AccountClassifierNodeSerializer(AbstractClassifierNodeSerializer):
    class Meta(AbstractClassifierNodeSerializer.Meta):
        model = AccountClassifier


class AccountTypeSerializer(ModelWithObjectPermissionSerializer, ModelWithUserCodeSerializer):
    master_user = MasterUserField()
    tags = TagField(many=True, required=False, allow_null=True)

    class Meta:
        model = AccountType
        fields = ['url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'public_name', 'notes',
                  'show_transaction_details', 'transaction_details_expr', 'is_default', 'is_deleted', 'tags']


class AccountTypeBulkObjectPermissionSerializer(AbstractBulkObjectPermissionSerializer):
    content_objects = AccountTypeField(many=True, allow_null=False, allow_empty=False)

    class Meta:
        model = AccountType


class AccountAttributeTypeSerializer(AbstractAttributeTypeSerializer):
    classifiers = AccountClassifierSerializer(required=False, allow_null=True, many=True)

    class Meta(AbstractAttributeTypeSerializer.Meta):
        model = AccountAttributeType
        fields = AbstractAttributeTypeSerializer.Meta.fields + ['classifiers']


class AccountAttributeTypeBulkObjectPermissionSerializer(AbstractBulkObjectPermissionSerializer):
    content_objects = AccountAttributeTypeField(many=True, allow_null=False, allow_empty=False)

    class Meta:
        model = AccountAttributeType


class AccountAttributeSerializer(AbstractAttributeSerializer):
    attribute_type = AccountAttributeTypeField()
    classifier = AccountClassifierField(required=False, allow_null=True)

    class Meta(AbstractAttributeSerializer.Meta):
        model = AccountAttribute
        fields = AbstractAttributeSerializer.Meta.fields + ['attribute_type', 'classifier']


class AccountSerializer(ModelWithObjectPermissionSerializer, ModelWithAttributesSerializer,
                        ModelWithUserCodeSerializer):
    master_user = MasterUserField()
    type = AccountTypeField(default=AccountTypeDefault())
    portfolios = PortfolioField(many=True, required=False, allow_null=True)
    attributes = AccountAttributeSerializer(many=True, required=False, allow_null=True)
    tags = TagField(many=True, required=False, allow_null=True)

    class Meta:
        model = Account
        fields = ['url', 'id', 'master_user', 'type', 'user_code', 'name', 'short_name', 'public_name', 'notes',
                  'is_default', 'is_valid_for_all_portfolios', 'is_deleted', 'portfolios', 'tags', 'attributes', ]


class AccountBulkObjectPermissionSerializer(AbstractBulkObjectPermissionSerializer):
    content_objects = AccountField(many=True, allow_null=False, allow_empty=False)

    class Meta:
        model = Account
