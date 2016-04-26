from __future__ import unicode_literals

from poms.common.serializers import ClassifierSerializerBase
from poms.strategies.fields import StrategyField
from poms.strategies.models import Strategy
from poms.tags.fields import TagField


class StrategySerializer(ClassifierSerializerBase):
    # parent = StrategyField(required=False, allow_null=True)
    # children = StrategyField(many=True, required=False, read_only=False)
    tags = TagField(many=True)

    class Meta(ClassifierSerializerBase.Meta):
        model = Strategy
        fields = ClassifierSerializerBase.Meta.fields + ['tags']
