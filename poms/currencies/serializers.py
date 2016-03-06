from __future__ import unicode_literals

from rest_framework import serializers

from poms.api.fields import CurrentMasterUserDefault
from poms.currencies.models import Currency


class CurrencySerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='currency-detail')
    master_user = serializers.HiddenField(default=CurrentMasterUserDefault())

    class Meta:
        model = Currency
        fields = ['url', 'master_user', 'id', 'code', 'name', 'is_global']
        readonly_fields = ['is_global']
