from __future__ import unicode_literals

from poms.common.filters import AbstractClassifierFilterSet
from poms.common.views import AbstractClassifierViewSet, AbstractClassifierNodeViewSet
from poms.obj_perms.views import AbstractWithObjectPermissionViewSet
from poms.strategies.models import Strategy1, Strategy2, Strategy3
from poms.strategies.serializers import Strategy1Serializer, Strategy1NodeSerializer, Strategy2Serializer, \
    Strategy2NodeSerializer, Strategy3Serializer, Strategy3NodeSerializer
from poms.tags.filters import TagFilterBackend, TagFilter


class AbstractStrategyFilterSet(AbstractClassifierFilterSet):
    class Meta(AbstractClassifierFilterSet.Meta):
        fields = AbstractClassifierFilterSet.Meta.fields + ['tag', ]


class AbstractStrategyViewSet(AbstractWithObjectPermissionViewSet, AbstractClassifierViewSet):
    filter_backends = AbstractClassifierViewSet.filter_backends + [
        TagFilterBackend,
    ]

    def get_serializer(self, *args, **kwargs):
        kwargs['show_children'] = (self.action != 'list')
        return super(AbstractStrategyViewSet, self).get_serializer(*args, **kwargs)


class AbstractStrategyNodeViewSet(AbstractWithObjectPermissionViewSet, AbstractClassifierNodeViewSet):
    filter_backends = AbstractClassifierNodeViewSet.filter_backends + [
        TagFilterBackend,
    ]


# Strategy1


class Strategy1ClassifierFilterSet(AbstractStrategyFilterSet):
    tag = TagFilter(model=Strategy1)

    class Meta(AbstractStrategyFilterSet.Meta):
        model = Strategy1


class Strategy1ViewSet(AbstractStrategyViewSet):
    queryset = Strategy1.objects
    serializer_class = Strategy1Serializer
    filter_class = Strategy1ClassifierFilterSet


class Strategy1NodeViewSet(AbstractStrategyNodeViewSet):
    queryset = Strategy1.objects
    serializer_class = Strategy1NodeSerializer
    filter_class = Strategy1ClassifierFilterSet


# Strategy2

class Strategy2ClassifierFilterSet(AbstractStrategyFilterSet):
    tag = TagFilter(model=Strategy2)

    class Meta(AbstractStrategyFilterSet.Meta):
        model = Strategy2


class Strategy2ViewSet(AbstractStrategyViewSet):
    queryset = Strategy2.objects
    serializer_class = Strategy2Serializer
    filter_class = Strategy2ClassifierFilterSet


class Strategy2NodeViewSet(AbstractStrategyNodeViewSet):
    queryset = Strategy2.objects
    serializer_class = Strategy2NodeSerializer
    filter_class = Strategy2ClassifierFilterSet


# Strategy3

class Strategy3ClassifierFilterSet(AbstractStrategyFilterSet):
    tag = TagFilter(model=Strategy3)

    class Meta(AbstractStrategyFilterSet.Meta):
        model = Strategy3


class Strategy3ViewSet(AbstractStrategyViewSet):
    queryset = Strategy3.objects
    serializer_class = Strategy3Serializer
    filter_class = Strategy3ClassifierFilterSet


class Strategy3NodeViewSet(AbstractStrategyNodeViewSet):
    queryset = Strategy3.objects
    serializer_class = Strategy3NodeSerializer
    filter_class = Strategy3ClassifierFilterSet
