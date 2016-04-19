from __future__ import unicode_literals

from rest_framework import serializers

from poms.accounts.fields import AccountClassifierField, AccountClassifierRootField, AttributeTypeField
from poms.accounts.models import Account, AccountType, AccountClassifier, AccountAttributeType, AccountAttribute
from poms.obj_attrs.serializers import AttributeTypeSerializerBase, AttributeSerializerBase, \
    ModelWithAttributesSerializer
from poms.obj_perms.fields import GrantedPermissionField
from poms.users.fields import MasterUserField


class AccountTypeSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='accounttype-detail')
    master_user = MasterUserField()

    class Meta:
        model = AccountType
        fields = ['url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'notes',
                  'show_transaction_details', 'transaction_details_expr']


class AccountClassifierSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='accountclassifier-detail')
    master_user = MasterUserField()
    parent = AccountClassifierField(required=False, allow_null=True)
    children = AccountClassifierField(many=True, required=False, read_only=False)

    class Meta:
        model = AccountClassifier
        fields = ['url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'notes',
                  'parent', 'children', 'tree_id', 'level']


class AccountAttributeTypeSerializer(AttributeTypeSerializerBase):
    url = serializers.HyperlinkedIdentityField(view_name='accountattributetype-detail')
    classifier_root = AccountClassifierRootField()

    class Meta(AttributeTypeSerializerBase.Meta):
        model = AccountAttributeType
        fields = AttributeTypeSerializerBase.Meta.fields + ['classifier_root']


class AccountAttributeSerializer(AttributeSerializerBase):
    attribute_type = AttributeTypeField()
    classifier = AccountClassifierField(required=False, allow_null=True)

    class Meta(AttributeSerializerBase.Meta):
        model = AccountAttribute
        fields = AttributeSerializerBase.Meta.fields + ['attribute_type', 'classifier']


class AccountSerializer(ModelWithAttributesSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='account-detail')
    master_user = MasterUserField()
    attributes = AccountAttributeSerializer(many=True)
    granted_permissions = GrantedPermissionField()

    class Meta:
        model = Account
        fields = ['url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'type', 'notes',
                  'attributes', 'granted_permissions']
