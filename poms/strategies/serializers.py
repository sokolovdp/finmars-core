from __future__ import unicode_literals

from rest_framework import serializers

from poms.common.serializers import ClassifierSerializerBase, ClassifierNodeSerializerBase
from poms.strategies.models import Strategy
from poms.tags.fields import TagField


class StrategySerializer(ClassifierSerializerBase):
    tags = TagField(many=True)

    class Meta(ClassifierSerializerBase.Meta):
        model = Strategy
        fields = ClassifierSerializerBase.Meta.fields + ['tags']


class StrategyNodeSerializer(ClassifierNodeSerializerBase):
    url = serializers.HyperlinkedIdentityField(view_name='strategynode-detail')
    tags = TagField(many=True)

    class Meta(ClassifierNodeSerializerBase.Meta):
        model = Strategy
        fields = ClassifierNodeSerializerBase.Meta.fields + ['tags']
