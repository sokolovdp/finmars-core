from __future__ import unicode_literals

from poms.common.filters import ClassifierFilterSetBase
from poms.common.views import ClassifierViewSetBase, ClassifierNodeViewSetBase
from poms.obj_perms.filters import ObjectPermissionFilter, ObjectPermissionPrefetchFilter, AllFakeFilter
from poms.obj_perms.permissions import ObjectPermissionBase
from poms.strategies.models import Strategy1, Strategy2, Strategy3
from poms.strategies.serializers import Strategy1Serializer, \
    Strategy1NodeSerializer, Strategy2Serializer, Strategy2NodeSerializer, Strategy3Serializer, Strategy3NodeSerializer
from poms.tags.filters import TagFakeFilter, TagFilterBackend


class StrategyClassifierBaseFilterSet(ClassifierFilterSetBase):
    all = AllFakeFilter()
    tags = TagFakeFilter()

    class Meta(ClassifierFilterSetBase.Meta):
        model = Strategy1
        fields = ClassifierFilterSetBase.Meta.fields + ['all', 'tags', ]


class StrategyBaseViewSet(ClassifierViewSetBase):
    filter_backends = ClassifierViewSetBase.filter_backends + [
        TagFilterBackend,
        ObjectPermissionPrefetchFilter,
        ObjectPermissionFilter,
    ]
    permission_classes = ClassifierNodeViewSetBase.permission_classes + [
        ObjectPermissionBase
    ]


class StrategyBaseNodeViewSet(ClassifierNodeViewSetBase):
    filter_backends = ClassifierNodeViewSetBase.filter_backends + [
        TagFilterBackend,
        ObjectPermissionPrefetchFilter,
        ObjectPermissionFilter,
    ]
    permission_classes = ClassifierNodeViewSetBase.permission_classes + [
        ObjectPermissionBase
    ]


class Strategy1ClassifierFilterSet(StrategyClassifierBaseFilterSet):
    class Meta(StrategyClassifierBaseFilterSet.Meta):
        model = Strategy1


class Strategy1ViewSet(StrategyBaseViewSet):
    queryset = Strategy1.objects
    serializer_class = Strategy1Serializer
    filter_class = Strategy1ClassifierFilterSet


class Strategy1NodeViewSet(StrategyBaseNodeViewSet):
    queryset = Strategy1.objects
    serializer_class = Strategy1NodeSerializer
    filter_class = Strategy1ClassifierFilterSet


class Strategy2ClassifierFilterSet(StrategyClassifierBaseFilterSet):
    class Meta(StrategyClassifierBaseFilterSet.Meta):
        model = Strategy2


class Strategy2ViewSet(StrategyBaseViewSet):
    queryset = Strategy2.objects
    serializer_class = Strategy2Serializer
    filter_class = Strategy2ClassifierFilterSet


class Strategy2NodeViewSet(StrategyBaseNodeViewSet):
    queryset = Strategy2.objects
    serializer_class = Strategy2NodeSerializer
    filter_class = Strategy2ClassifierFilterSet


class Strategy3ClassifierFilterSet(StrategyClassifierBaseFilterSet):
    class Meta(StrategyClassifierBaseFilterSet.Meta):
        model = Strategy3


class Strategy3ViewSet(StrategyBaseViewSet):
    queryset = Strategy3.objects
    serializer_class = Strategy3Serializer
    filter_class = Strategy3ClassifierFilterSet


class Strategy3NodeViewSet(StrategyBaseNodeViewSet):
    queryset = Strategy3.objects
    serializer_class = Strategy3NodeSerializer
    filter_class = Strategy3ClassifierFilterSet
