from __future__ import unicode_literals

from poms.common.fields import FilteredPrimaryKeyRelatedField
from poms.instruments.models import InstrumentClassifier, Instrument, InstrumentAttributeType, InstrumentType, \
    PricingPolicy
from poms.obj_attrs.filters import AttributeClassifierBaseField
from poms.obj_perms.filters import FieldObjectPermissionBackend
from poms.users.filters import OwnerByMasterUserFilter


class InstrumentClassifierField(AttributeClassifierBaseField):
    queryset = InstrumentClassifier.objects


# class InstrumentClassifierRootField(FilteredPrimaryKeyRelatedField):
#     queryset = InstrumentClassifier.objects.filter(parent__isnull=True)
#     filter_backends = [OwnerByMasterUserFilter]


class InstrumentAttributeTypeField(FilteredPrimaryKeyRelatedField):
    queryset = InstrumentAttributeType.objects
    filter_backends = [
        OwnerByMasterUserFilter,
        FieldObjectPermissionBackend,
    ]


class InstrumentTypeField(FilteredPrimaryKeyRelatedField):
    queryset = InstrumentType.objects
    filter_backends = [
        OwnerByMasterUserFilter,
        FieldObjectPermissionBackend,
    ]


class InstrumentField(FilteredPrimaryKeyRelatedField):
    queryset = Instrument.objects
    filter_backends = [
        OwnerByMasterUserFilter,
        FieldObjectPermissionBackend,
    ]


class PricingPolicyField(FilteredPrimaryKeyRelatedField):
    queryset = PricingPolicy.objects
    filter_backends = [
        OwnerByMasterUserFilter,
    ]
