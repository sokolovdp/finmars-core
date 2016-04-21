from __future__ import unicode_literals

from django.contrib.contenttypes.models import ContentType

from poms.api.fields import FilteredPrimaryKeyRelatedField
from poms.tags.filters import TagContentTypeFilter
from poms.tags.models import Tag
from poms.users.filters import OwnerByMasterUserFilter


class TagContentTypeField(FilteredPrimaryKeyRelatedField):
    queryset = ContentType.objects
    filter_backends = [TagContentTypeFilter]


class TagField(FilteredPrimaryKeyRelatedField):
    queryset = Tag.objects
    filter_backends = [OwnerByMasterUserFilter]
