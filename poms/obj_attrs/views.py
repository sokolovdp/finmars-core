from rest_framework.filters import DjangoFilterBackend, OrderingFilter, SearchFilter

from poms.common.views import PomsViewSetBase
from poms.users.filters import OwnerByMasterUserFilter


class AttributeTypeViewSetBase(PomsViewSetBase):
    filter_backends = [OwnerByMasterUserFilter, DjangoFilterBackend, OrderingFilter, SearchFilter]
    ordering_fields = ['user_code', 'name', 'short_name', 'order', ]
    search_fields = ['user_code', 'name', 'short_name']

    def get_queryset(self):
        qs = super(AttributeTypeViewSetBase, self).get_queryset()
        return qs.prefetch_related('options')
