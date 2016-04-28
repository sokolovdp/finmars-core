from __future__ import unicode_literals

from poms.common.filters import ClassifierFilterSetBase
from poms.common.views import ClassifierViewSetBase, ClassifierNodeViewSetBase
from poms.strategies.models import Strategy
from poms.strategies.serializers import StrategySerializer, StrategyNodeSerializer
from poms.tags.filters import TagPrefetchFilter


class StrategyClassifierFilterSet(ClassifierFilterSetBase):
    class Meta(ClassifierFilterSetBase.Meta):
        model = Strategy


class StrategyViewSet(ClassifierViewSetBase):
    queryset = Strategy.objects.all()
    serializer_class = StrategySerializer
    filter_backends = [TagPrefetchFilter] + ClassifierViewSetBase.filter_backends
    filter_class = StrategyClassifierFilterSet


class StrategyNodeViewSet(ClassifierNodeViewSetBase):
    queryset = Strategy.objects.all()
    serializer_class = StrategyNodeSerializer
    filter_backends = [TagPrefetchFilter] + ClassifierNodeViewSetBase.filter_backends
    filter_class = StrategyClassifierFilterSet
