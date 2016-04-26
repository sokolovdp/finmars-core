from __future__ import unicode_literals

from rest_framework import serializers

from poms.accounts.fields import AccountClassifierField, AccountClassifierRootField, AccountAttributeTypeField
from poms.accounts.models import Account, AccountType, AccountClassifier, AccountAttributeType, AccountAttribute
from poms.common.serializers import ClassifierSerializerBase, ClassifierRecursiveField
from poms.obj_attrs.serializers import AttributeTypeSerializerBase, AttributeSerializerBase, \
    ModelWithAttributesSerializer
from poms.obj_perms.serializers import ObjectPermissionSerializer, ModelWithObjectPermissionSerializer
from poms.users.fields import MasterUserField


class AccountClassifierSerializer(ClassifierSerializerBase):
    # parent = AccountClassifierField(required=False, allow_null=True)
    # children = AccountClassifierField(many=True, required=False, read_only=False)
    # children = ClassifierRecursiveField(many=True)

    class Meta(ClassifierSerializerBase.Meta):
        model = AccountClassifier


class AccountTypeSerializer(serializers.ModelSerializer):
    master_user = MasterUserField()

    class Meta:
        model = AccountType
        fields = ['url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'notes',
                  'show_transaction_details', 'transaction_details_expr']


class AccountAttributeTypeSerializer(AttributeTypeSerializerBase):
    classifier_root = AccountClassifierRootField(required=False, allow_null=True)

    class Meta(AttributeTypeSerializerBase.Meta):
        model = AccountAttributeType
        fields = AttributeTypeSerializerBase.Meta.fields + ['classifier_root']
        update_read_only_fields = AttributeTypeSerializerBase.Meta.update_read_only_fields + ['classifier_root']


class AccountAttributeSerializer(AttributeSerializerBase):
    attribute_type = AccountAttributeTypeField()
    classifier = AccountClassifierField(required=False, allow_null=True)

    class Meta(AttributeSerializerBase.Meta):
        model = AccountAttribute
        fields = AttributeSerializerBase.Meta.fields + ['attribute_type', 'classifier']


class AccountSerializer(ModelWithAttributesSerializer, ModelWithObjectPermissionSerializer):
    master_user = MasterUserField()
    attributes = AccountAttributeSerializer(many=True)
    object_permission = ObjectPermissionSerializer()

    class Meta:
        model = Account
        fields = ['url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'type', 'notes',
                  'attributes', 'object_permission']
