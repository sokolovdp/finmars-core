from __future__ import unicode_literals

from rest_framework import serializers

from poms.accounts.fields import AccountClassifierField, AccountAttributeTypeField
from poms.accounts.models import Account, AccountType, AccountClassifier, AccountAttributeType, AccountAttribute
from poms.common.serializers import ClassifierSerializerBase, ClassifierNodeSerializerBase
from poms.obj_attrs.serializers import AttributeTypeSerializerBase, AttributeSerializerBase, \
    ModelWithAttributesSerializer
from poms.obj_perms.serializers import ModelWithObjectPermissionSerializer
from poms.tags.fields import TagField
from poms.users.fields import MasterUserField


class AccountClassifierSerializer(ClassifierSerializerBase):
    class Meta(ClassifierSerializerBase.Meta):
        model = AccountClassifier


class AccountClassifierNodeSerializer(ClassifierNodeSerializerBase):
    url = serializers.HyperlinkedIdentityField(view_name='accountclassifiernode-detail')

    class Meta(ClassifierNodeSerializerBase.Meta):
        model = AccountClassifier


class AccountTypeSerializer(ModelWithObjectPermissionSerializer):
    master_user = MasterUserField()
    tags = TagField(many=True)

    class Meta:
        model = AccountType
        fields = ['url', 'id', 'master_user', 'user_code', 'name', 'public_name', 'short_name', 'notes',
                  'show_transaction_details', 'transaction_details_expr', 'tags']


class AccountAttributeTypeSerializer(AttributeTypeSerializerBase, ModelWithObjectPermissionSerializer):
    # classifier_root = AccountClassifierRootField(required=False, allow_null=True)
    # classifiers = AccountClassifierSerializer2(required=False, allow_null=True, many=True)
    classifiers = AccountClassifierSerializer(required=False, allow_null=True, many=True)

    class Meta(AttributeTypeSerializerBase.Meta):
        model = AccountAttributeType
        fields = AttributeTypeSerializerBase.Meta.fields + ['classifiers']
        # update_read_only_fields = AttributeTypeSerializerBase.Meta.update_read_only_fields + ['classifiers']


class AccountAttributeSerializer(AttributeSerializerBase):
    attribute_type = AccountAttributeTypeField()
    classifier = AccountClassifierField(required=False, allow_null=True)

    class Meta(AttributeSerializerBase.Meta):
        model = AccountAttribute
        fields = AttributeSerializerBase.Meta.fields + ['attribute_type', 'classifier']


class AccountSerializer(ModelWithAttributesSerializer, ModelWithObjectPermissionSerializer):
    master_user = MasterUserField()
    attributes = AccountAttributeSerializer(many=True)
    tags = TagField(many=True)
    # type_public_name = serializers.SlugRelatedField(slug_field='public_name', read_only=True)
    type__public_name = serializers.SerializerMethodField()

    class Meta:
        model = Account
        fields = ['url', 'id', 'master_user', 'user_code', 'name', 'public_name', 'short_name', 'notes',
                  'type', 'type__public_name', 'tags', 'attributes', ]

    def get_type__public_name(self, obj):
        return obj.type.public_name if obj.type is not None else None
