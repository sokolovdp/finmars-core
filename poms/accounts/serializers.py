from __future__ import unicode_literals

from rest_framework import serializers

from poms.accounts.models import Account
from poms.api.fields import CurrentMasterUserDefault


class AccountSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='account-detail')
    master_user = serializers.HiddenField(default=CurrentMasterUserDefault())

    class Meta:
        model = Account
        fields = ['url', 'master_user', 'id', 'user_code', 'name', 'short_name']

