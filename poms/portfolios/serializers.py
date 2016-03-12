from __future__ import unicode_literals

from rest_framework import serializers

from poms.api.fields import CurrentMasterUserDefault, FilteredPrimaryKeyRelatedField
from poms.api.filters import IsOwnerByMasterUserFilter
from poms.portfolios.models import PortfolioClassifier, Portfolio


class PortfolioClassifierField(FilteredPrimaryKeyRelatedField):
    queryset = PortfolioClassifier.objects
    filter_backends = [IsOwnerByMasterUserFilter]


class PortfolioField(FilteredPrimaryKeyRelatedField):
    queryset = Portfolio.objects
    filter_backends = [IsOwnerByMasterUserFilter]


class PortfolioClassifierSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='portfolioclassifier-detail')
    master_user = serializers.HiddenField(default=CurrentMasterUserDefault())
    parent = PortfolioClassifierField(required=False, allow_null=True)
    children = PortfolioClassifierField(many=True, required=False, read_only=False)

    class Meta:
        model = PortfolioClassifier
        fields = ['url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'notes',
                  'parent', 'children', 'tree_id', 'level']


class PortfolioSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='portfolio-detail')
    master_user = serializers.HiddenField(default=CurrentMasterUserDefault())
    classifiers = PortfolioClassifierField(many=True, read_only=False)

    class Meta:
        model = Portfolio
        fields = ['url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'notes',
                  'classifiers']
