from __future__ import unicode_literals

from rest_framework.relations import PrimaryKeyRelatedField

from poms.common.fields import PrimaryKeyRelatedFilteredField
from poms.integrations.models import InstrumentMapping, ProviderClass, FactorScheduleMethod, \
    AccrualCalculationScheduleMethod
from poms.users.filters import OwnerByMasterUserFilter


class InstrumentMappingField(PrimaryKeyRelatedFilteredField):
    queryset = InstrumentMapping.objects
    filter_backends = [OwnerByMasterUserFilter]


class ProviderClassField(PrimaryKeyRelatedField):
    queryset = ProviderClass.objects


class FactorScheduleMethodField(PrimaryKeyRelatedField):
    queryset = FactorScheduleMethod.objects


class AccrualCalculationScheduleMethodField(PrimaryKeyRelatedField):
    queryset = AccrualCalculationScheduleMethod.objects
