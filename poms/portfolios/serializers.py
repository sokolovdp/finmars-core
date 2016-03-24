from __future__ import unicode_literals

from rest_framework import serializers

from poms.portfolios.fields import PortfolioClassifierField
from poms.portfolios.models import PortfolioClassifier, Portfolio
from poms.users.fields import CurrentMasterUserDefault, MasterUserField


class PortfolioClassifierSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='portfolioclassifier-detail')
    master_user = MasterUserField()
    parent = PortfolioClassifierField(required=False, allow_null=True)
    children = PortfolioClassifierField(many=True, required=False, read_only=False)

    class Meta:
        model = PortfolioClassifier
        fields = ['url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'notes',
                  'parent', 'children', 'tree_id', 'level']


class PortfolioSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='portfolio-detail')
    master_user = MasterUserField()
    classifiers = PortfolioClassifierField(many=True, read_only=False)

    class Meta:
        model = Portfolio
        fields = ['url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'notes',
                  'classifiers']
