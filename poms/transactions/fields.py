from __future__ import unicode_literals

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.utils.encoding import smart_text

from poms.common.fields import FilteredPrimaryKeyRelatedField, FilteredSlugRelatedField
from poms.obj_perms.filters import ObjectPermissionPrefetchFilter, ObjectPermissionFilter
from poms.transactions.filters import TransactionTypeInputContentTypeFilter
from poms.transactions.models import TransactionType, TransactionAttributeType
from poms.users.filters import OwnerByMasterUserFilter


class TransactionTypeField(FilteredPrimaryKeyRelatedField):
    queryset = TransactionType.objects
    filter_backends = [
        OwnerByMasterUserFilter,
        ObjectPermissionPrefetchFilter,
        ObjectPermissionFilter,
    ]


class TransactionAttributeTypeField(FilteredPrimaryKeyRelatedField):
    queryset = TransactionAttributeType.objects
    filter_backends = [
        OwnerByMasterUserFilter,
        ObjectPermissionPrefetchFilter,
        ObjectPermissionFilter,
    ]


class TransactionTypeInputContentTypeField(FilteredSlugRelatedField):
    queryset = ContentType.objects
    filter_backends = [
        TransactionTypeInputContentTypeFilter
    ]

    def __init__(self, **kwargs):
        kwargs['slug_field'] = 'model'
        super(TransactionTypeInputContentTypeField, self).__init__(**kwargs)

    def to_internal_value(self, data):
        try:
            app_label, model = data.split('.')
            return self.get_queryset().get(app_label=app_label, model=model)
        except ObjectDoesNotExist:
            self.fail('does_not_exist', slug_name=self.slug_field, value=smart_text(data))
        except (TypeError, ValueError):
            self.fail('invalid')

    def to_representation(self, obj):
        return '%s.%s' % (obj.app_label, obj.model)
