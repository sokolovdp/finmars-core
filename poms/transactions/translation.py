from modeltranslation.translator import translator

from poms.common.translation import ClassModelTranslationOptions
from poms.transactions.models import TransactionClass, ActionClass, EventClass, NotificationClass, PeriodicityGroup

translator.register(TransactionClass, ClassModelTranslationOptions)
translator.register(ActionClass, ClassModelTranslationOptions)
translator.register(EventClass, ClassModelTranslationOptions)
translator.register(NotificationClass, ClassModelTranslationOptions)
translator.register(PeriodicityGroup, ClassModelTranslationOptions)
