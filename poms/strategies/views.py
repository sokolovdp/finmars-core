from __future__ import unicode_literals

from poms.common.filters import ClassifierFilterSetBase
from poms.common.views import ClassifierViewSetBase, ClassifierNodeViewSetBase
from poms.strategies.models import Strategy, Strategy1, Strategy2, Strategy3
from poms.strategies.serializers import StrategySerializer, StrategyNodeSerializer, Strategy1Serializer, \
    Strategy1NodeSerializer, Strategy2Serializer, Strategy2NodeSerializer, Strategy3Serializer, Strategy3NodeSerializer
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


class Strategy1ClassifierFilterSet(ClassifierFilterSetBase):
    class Meta(ClassifierFilterSetBase.Meta):
        model = Strategy1


class Strategy1ViewSet(ClassifierViewSetBase):
    queryset = Strategy1.objects.all()
    serializer_class = Strategy1Serializer
    filter_backends = [TagPrefetchFilter] + ClassifierViewSetBase.filter_backends
    filter_class = Strategy1ClassifierFilterSet


class Strategy1NodeViewSet(ClassifierNodeViewSetBase):
    queryset = Strategy1.objects.all()
    serializer_class = Strategy1NodeSerializer
    filter_backends = [TagPrefetchFilter] + ClassifierNodeViewSetBase.filter_backends
    filter_class = Strategy1ClassifierFilterSet


class Strategy2ClassifierFilterSet(ClassifierFilterSetBase):
    class Meta(ClassifierFilterSetBase.Meta):
        model = Strategy2


class Strategy2ViewSet(ClassifierViewSetBase):
    queryset = Strategy2.objects.all()
    serializer_class = Strategy2Serializer
    filter_backends = [TagPrefetchFilter] + ClassifierViewSetBase.filter_backends
    filter_class = Strategy2ClassifierFilterSet


class Strategy2NodeViewSet(ClassifierNodeViewSetBase):
    queryset = Strategy2.objects.all()
    serializer_class = Strategy2NodeSerializer
    filter_backends = [TagPrefetchFilter] + ClassifierNodeViewSetBase.filter_backends
    filter_class = Strategy2ClassifierFilterSet


class Strategy3ClassifierFilterSet(ClassifierFilterSetBase):
    class Meta(ClassifierFilterSetBase.Meta):
        model = Strategy3


class Strategy3ViewSet(ClassifierViewSetBase):
    queryset = Strategy3.objects.all()
    serializer_class = Strategy3Serializer
    filter_backends = [TagPrefetchFilter] + ClassifierViewSetBase.filter_backends
    filter_class = Strategy3ClassifierFilterSet


class Strategy3NodeViewSet(ClassifierNodeViewSetBase):
    queryset = Strategy3.objects.all()
    serializer_class = Strategy3NodeSerializer
    filter_backends = [TagPrefetchFilter] + ClassifierNodeViewSetBase.filter_backends
    filter_class = Strategy3ClassifierFilterSet
