from __future__ import unicode_literals

from django.apps import AppConfig
from django.db import DEFAULT_DB_ALIAS
from django.utils.translation import ugettext_lazy as _


class InstrumentsConfig(AppConfig):
    name = 'poms.instruments'
    # label = 'poms'
    verbose_name = _('Instruments')

    def ready(self):
        from django.db.models.signals import post_migrate
        post_migrate.connect(self.update_transaction_classes)
        pass

    def update_transaction_classes(self, app_config, verbosity=2, using=DEFAULT_DB_ALIAS, **kwargs):
        from poms.common.utils import db_class_check_data
        from .models import InstrumentClass, DailyPricingModel, AccrualCalculationModel, PeriodicityPeriod, CostMethod, \
            PaymentSizeDetail

        if not isinstance(app_config, InstrumentsConfig):
            return

        db_class_check_data(InstrumentClass, verbosity, using)
        db_class_check_data(DailyPricingModel, verbosity, using)
        db_class_check_data(AccrualCalculationModel, verbosity, using)
        db_class_check_data(PeriodicityPeriod, verbosity, using)
        db_class_check_data(CostMethod, verbosity, using)
        db_class_check_data(PaymentSizeDetail, verbosity, using)
