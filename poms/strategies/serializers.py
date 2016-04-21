from __future__ import unicode_literals

from poms.common.serializers import ClassifierSerializerBase
from poms.strategies.fields import StrategyField
from poms.strategies.models import Strategy


class StrategySerializer(ClassifierSerializerBase):
    parent = StrategyField(required=False, allow_null=True)
    children = StrategyField(many=True, required=False, read_only=False)

    class Meta(ClassifierSerializerBase.Meta):
        model = Strategy
