from __future__ import unicode_literals

from rest_framework import serializers

from poms.api.fields import CurrentMasterUserDefault
from poms.currencies.models import Currency, CurrencyHistory


class CurrencySerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='currency-detail')
    master_user = serializers.HiddenField(default=CurrentMasterUserDefault())

    class Meta:
        model = Currency
        fields = ['url', 'id', 'master_user', 'code', 'name', 'is_global']
        readonly_fields = ['is_global']


class CurrencyHistorySerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='currencyhistory-detail')

    class Meta:
        model = CurrencyHistory
        fields = ['url', 'id', 'currency', 'date', 'fx_rate']

