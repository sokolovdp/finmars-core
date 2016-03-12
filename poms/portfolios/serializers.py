from __future__ import unicode_literals

from rest_framework import serializers

from poms.api.fields import CurrentMasterUserDefault
from poms.portfolios.models import PortfolioClassifier, Portfolio


class PortfolioClassifierSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='portfolioclassifier-detail')
    master_user = serializers.HiddenField(default=CurrentMasterUserDefault())

    class Meta:
        model = PortfolioClassifier
        fields = ['url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'notes',
                  'parent', 'children', 'tree_id', 'level']


class PortfolioSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='portfolio-detail')
    master_user = serializers.HiddenField(default=CurrentMasterUserDefault())

    class Meta:
        model = Portfolio
        fields = ['url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'notes',
                  'classifiers']
