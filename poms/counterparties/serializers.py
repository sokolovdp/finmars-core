from __future__ import unicode_literals

from rest_framework import serializers

from poms.counterparties.fields import CounterpartyClassifierField
from poms.counterparties.models import CounterpartyClassifier, Counterparty, Responsible
from poms.users.fields import MasterUserField


class CounterpartyClassifierSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='counterpartyclassifier-detail')
    master_user = MasterUserField()
    parent = CounterpartyClassifierField(required=False, allow_null=True)
    children = CounterpartyClassifierField(many=True, required=False, read_only=False)

    class Meta:
        model = CounterpartyClassifier
        fields = ['url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'notes',
                  'parent', 'children', 'tree_id', 'level']


class CounterpartySerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='counterparty-detail')
    master_user = MasterUserField()
    classifiers = CounterpartyClassifierField(many=True, read_only=False)

    class Meta:
        model = Counterparty
        fields = ['url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'classifiers', 'notes']


class ResponsibleSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='responsible-detail')
    master_user = MasterUserField()

    class Meta:
        model = Responsible
        fields = ['url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'notes']
