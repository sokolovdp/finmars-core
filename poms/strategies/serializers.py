from __future__ import unicode_literals

from rest_framework import serializers

from poms.strategies.fields import StrategyField
from poms.strategies.models import Strategy
from poms.users.fields import MasterUserField


class StrategySerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='strategy-detail')
    master_user = MasterUserField()
    parent = StrategyField(required=False, allow_null=True)
    children = StrategyField(many=True, required=False, read_only=False)

    class Meta:
        model = Strategy
        fields = ['url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'notes',
                  'parent', 'children', 'tree_id', 'level']
