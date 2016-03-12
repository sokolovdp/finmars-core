from __future__ import unicode_literals

from rest_framework import serializers

from poms.api.fields import CurrentMasterUserDefault
from poms.strategies.models import Strategy


class StrategySerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='strategy-detail')
    master_user = serializers.HiddenField(default=CurrentMasterUserDefault())

    class Meta:
        model = Strategy
        fields = ['url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'notes',
                  'parent', 'children', 'tree_id', 'level']
