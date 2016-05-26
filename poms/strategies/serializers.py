from __future__ import unicode_literals

from rest_framework import serializers

from poms.common.serializers import ClassifierSerializerBase, ClassifierNodeSerializerBase
from poms.strategies.models import Strategy, Strategy1, Strategy2, Strategy3
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


class Strategy1Serializer(ClassifierSerializerBase):
    tags = TagField(many=True)

    class Meta(ClassifierSerializerBase.Meta):
        model = Strategy1
        fields = ClassifierSerializerBase.Meta.fields + ['tags']


class Strategy1NodeSerializer(ClassifierNodeSerializerBase):
    url = serializers.HyperlinkedIdentityField(view_name='strategy1node-detail')
    tags = TagField(many=True)

    class Meta(ClassifierNodeSerializerBase.Meta):
        model = Strategy1
        fields = ClassifierNodeSerializerBase.Meta.fields + ['tags']


class Strategy2Serializer(ClassifierSerializerBase):
    tags = TagField(many=True)

    class Meta(ClassifierSerializerBase.Meta):
        model = Strategy2
        fields = ClassifierSerializerBase.Meta.fields + ['tags']


class Strategy2NodeSerializer(ClassifierNodeSerializerBase):
    url = serializers.HyperlinkedIdentityField(view_name='strategynode-detail')
    tags = TagField(many=True)

    class Meta(ClassifierNodeSerializerBase.Meta):
        model = Strategy2
        fields = ClassifierNodeSerializerBase.Meta.fields + ['tags']


class Strategy3Serializer(ClassifierSerializerBase):
    tags = TagField(many=True)

    class Meta(ClassifierSerializerBase.Meta):
        model = Strategy3
        fields = ClassifierSerializerBase.Meta.fields + ['tags']


class Strategy3NodeSerializer(ClassifierNodeSerializerBase):
    url = serializers.HyperlinkedIdentityField(view_name='strategynode-detail')
    tags = TagField(many=True)

    class Meta(ClassifierNodeSerializerBase.Meta):
        model = Strategy3
        fields = ClassifierNodeSerializerBase.Meta.fields + ['tags']
