from __future__ import unicode_literals

from rest_framework import serializers

from poms.api.fields import CurrentMasterUserDefault, FilteredPrimaryKeyRelatedField
from poms.api.filters import IsOwnerByMasterUserFilter
from poms.strategies.models import Strategy


class StrategyField(FilteredPrimaryKeyRelatedField):
    queryset = Strategy.objects
    filter_backends = [IsOwnerByMasterUserFilter]


class StrategySerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='strategy-detail')
    master_user = serializers.HiddenField(default=CurrentMasterUserDefault())
    parent = StrategyField(required=False, allow_null=True)
    children = StrategyField(many=True, required=False, read_only=False)

    class Meta:
        model = Strategy
        fields = ['url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'notes',
                  'parent', 'children', 'tree_id', 'level']
