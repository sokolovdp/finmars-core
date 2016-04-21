from __future__ import unicode_literals

from rest_framework.filters import DjangoFilterBackend, OrderingFilter, SearchFilter

from poms.common.views import PomsViewSetBase
from poms.tags.models import Tag
from poms.tags.serializers import TagSerializer
from poms.users.filters import OwnerByMasterUserFilter


class TagViewSet(PomsViewSetBase):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    filter_backends = [OwnerByMasterUserFilter, DjangoFilterBackend, OrderingFilter, SearchFilter]
    ordering_fields = ['user_code', 'name', 'short_name']
    search_fields = ['user_code', 'name', 'short_name']
