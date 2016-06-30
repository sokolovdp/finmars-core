from modeltranslation.translator import translator

from poms.common.translation import ClassModelTranslationOptions
from poms.instruments.models import InstrumentClass, DailyPricingModel, AccrualCalculationModel, PaymentSizeDetail, \
    PeriodicityPeriod, CostMethod

translator.register(InstrumentClass, ClassModelTranslationOptions)
translator.register(DailyPricingModel, ClassModelTranslationOptions)
translator.register(AccrualCalculationModel, ClassModelTranslationOptions)
translator.register(PaymentSizeDetail, ClassModelTranslationOptions)
translator.register(PeriodicityPeriod, ClassModelTranslationOptions)
translator.register(CostMethod, ClassModelTranslationOptions)
