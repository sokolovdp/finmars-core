from __future__ import unicode_literals

from rest_framework import serializers

from poms.api.fields import CurrentMasterUserDefault
from poms.instruments.models import InstrumentClassifier


class InstrumentClassifierSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='instrumentclassifier-detail')
    master_user = serializers.HiddenField(default=CurrentMasterUserDefault())

    class Meta:
        model = InstrumentClassifier
        fields = ['url', 'master_user', 'id', 'name', 'parent', 'children',
                  'lft', 'rght', 'tree_id', 'level']
