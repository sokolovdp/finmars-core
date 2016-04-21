from __future__ import unicode_literals

from poms.common.filters import ClassifierFilterSetBase
from poms.common.views import ClassifierViewSetBase
from poms.strategies.models import Strategy
from poms.strategies.serializers import StrategySerializer


class AccountClassifierFilterSet(ClassifierFilterSetBase):
    class Meta(ClassifierFilterSetBase.Meta):
        model = Strategy


class StrategyViewSet(ClassifierViewSetBase):
    queryset = Strategy.objects.all()
    serializer_class = StrategySerializer
    filter_class = AccountClassifierFilterSet
