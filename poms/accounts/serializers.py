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
    tags = TagField(many=True, required=False, allow_null=True)

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
    attributes = AccountAttributeSerializer(many=True, required=False, allow_null=True)
    tags = TagField(many=True, required=False, allow_null=True)
    # type_public_name = serializers.SlugRelatedField(slug_field='public_name', read_only=True)
    type__public_name = serializers.SerializerMethodField()

    class Meta:
        model = Account
        fields = ['url', 'id', 'master_user', 'user_code', 'name', 'public_name', 'short_name', 'notes',
                  'type', 'type__public_name', 'tags', 'attributes', ]

    def get_type__public_name(self, obj):
        return obj.type.public_name if obj.type is not None else None

        # def validate_tags(self, tags):
        #     return tags
        #
        # def update(self, instance, validated_data):
        #     tags = validated_data.pop('tags', None)
        #
        #     instance = super(AccountSerializer, self).update(instance, validated_data)
        #
        #     if tags is not None:
        #         tags_field = self.fields['tags']
        #
        #         ctype = ContentType.objects.get_for_model(instance)
        #         tags_qs = Tag.objects.filter(master_user=instance.master_user, content_types__in=[ctype])
        #
        #         cur_tags = {t.id for t in instance.tags.all()}
        #         # print('cur_tags ->', cur_tags)
        #         cur_tags_with_perms = {t.id for t in tags_field.get_attribute(instance)}
        #         # print('cur_tags_with_perms ->', cur_tags_with_perms)
        #         hidden_tags = cur_tags - cur_tags_with_perms
        #         # print('hidden_tags ->', hidden_tags)
        #         new_tags = {t.id for t in tags}
        #         # print('new_tags ->', new_tags)
        #         tags = [t for t in tags_qs.all() if t.id in hidden_tags or t.id in new_tags]
        #         # print(tags)
        #
        #         instance.tags = tags
        #
        #     return instance
