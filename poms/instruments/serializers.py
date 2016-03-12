from __future__ import unicode_literals

from rest_framework import serializers

from poms.api.fields import CurrentMasterUserDefault
from poms.instruments.models import InstrumentClassifier, Instrument, PriceHistory


class InstrumentClassifierSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='instrumentclassifier-detail')
    master_user = serializers.HiddenField(default=CurrentMasterUserDefault())

    class Meta:
        model = InstrumentClassifier
        fields = ['url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'notes',
                  'parent', 'children', 'tree_id', 'level']


class InstrumentSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='instrument-detail')
    master_user = serializers.HiddenField(default=CurrentMasterUserDefault())

    class Meta:
        model = Instrument
        fields = ['url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'notes', 'is_active',
                  'pricing_currency', 'price_multiplier', 'accrued_currency', 'accrued_multiplier',
                  'classifiers']


class PriceHistorySerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='pricehistory-detail')

    class Meta:
        model = PriceHistory
        fields = ['url', 'id', 'instrument', 'date', 'principal_price', 'accrued_price', 'factor']
