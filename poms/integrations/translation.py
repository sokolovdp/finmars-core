from modeltranslation.translator import translator

from poms.common.translation import AbstractClassModelOptions
from poms.integrations.models import (
    AccrualScheduleDownloadMethod,
    FactorScheduleDownloadMethod,
    ProviderClass,
)

translator.register(ProviderClass, AbstractClassModelOptions)
translator.register(FactorScheduleDownloadMethod, AbstractClassModelOptions)
translator.register(AccrualScheduleDownloadMethod, AbstractClassModelOptions)
