from __future__ import unicode_literals

from rest_framework import serializers

from poms.accounts.models import Account, AccountType, AccountClassifier
from poms.api.fields import CurrentMasterUserDefault, FilteredPrimaryKeyRelatedField
from poms.api.filters import IsOwnerByMasterUserFilter


class AccountClassifierField(FilteredPrimaryKeyRelatedField):
    queryset = AccountClassifier.objects
    filter_backends = [IsOwnerByMasterUserFilter]


class AccountField(FilteredPrimaryKeyRelatedField):
    queryset = Account.objects
    filter_backends = [IsOwnerByMasterUserFilter]


class AccountTypeSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='accounttype-detail')

    class Meta:
        model = AccountType
        fields = ['url', 'id', 'code', 'name']


class AccountClassifierSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='accountclassifier-detail')
    master_user = serializers.HiddenField(default=CurrentMasterUserDefault())
    parent = AccountClassifierField(required=False, allow_null=True)
    children = AccountClassifierField(many=True, required=False, read_only=False)

    class Meta:
        model = AccountClassifier
        fields = ['url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'notes',
                  'parent', 'children', 'tree_id', 'level']


class AccountSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='account-detail')
    master_user = serializers.HiddenField(default=CurrentMasterUserDefault())
    classifiers = AccountClassifierField(many=True, read_only=False)

    class Meta:
        model = Account
        fields = ['url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'type', 'classifiers']
