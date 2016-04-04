from __future__ import unicode_literals

from rest_framework import serializers

from poms.accounts.fields import AccountClassifierField
from poms.accounts.models import Account, AccountType, AccountClassifier
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


# granted_permission = GrantedPermissionField()
class AccountSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='account-detail')
    master_user = MasterUserField()
    classifiers = AccountClassifierField(many=True, read_only=False)
    granted_permissions = serializers.SerializerMethodField()

    class Meta:
        model = Account
        fields = ['url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'type', 'classifiers', 'notes',
                  'granted_permissions']

    def get_granted_permissions(self, obj):
        user = self.context['request'].user
        return user.get_all_permissions(obj)
