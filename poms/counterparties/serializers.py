from __future__ import unicode_literals

from rest_framework import serializers

from poms.api.fields import CurrentMasterUserDefault
from poms.counterparties.models import CounterpartyClassifier, Counterparty, Responsible


class CounterpartyClassifierSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='counterpartyclassifier-detail')
    master_user = serializers.HiddenField(default=CurrentMasterUserDefault())

    class Meta:
        model = CounterpartyClassifier
        fields = ['url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'notes',
                  'parent', 'children', 'tree_id', 'level']


class CounterpartySerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='counterparty-detail')
    master_user = serializers.HiddenField(default=CurrentMasterUserDefault())

    class Meta:
        model = Counterparty
        fields = ['url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'classifiers']


class ResponsibleSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='responsible-detail')
    master_user = serializers.HiddenField(default=CurrentMasterUserDefault())

    class Meta:
        model = Responsible
        fields = ['url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'notes']
