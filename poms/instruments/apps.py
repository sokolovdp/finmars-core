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
        from .models import InstrumentClass, DailyPricingModel, AccrualCalculationModel, PaymentFrequency, CostMethod

        if not isinstance(app_config, InstrumentsConfig):
            return

        self.create_data(InstrumentClass, verbosity, using)
        self.create_data(DailyPricingModel, verbosity, using)
        self.create_data(AccrualCalculationModel, verbosity, using)
        self.create_data(PaymentFrequency, verbosity, using)
        self.create_data(CostMethod, verbosity, using)

        # exists = set(InstrumentClass.objects.using(using).values_list('pk', flat=True))
        #
        # if verbosity >= 2:
        #     print('existed transaction classes -> %s' % exists)
        #
        # for id, name in InstrumentClass.CLASSES:
        #     if id not in exists:
        #         if verbosity >= 2:
        #             print('create instrument class -> %s:%s' % (id, name))
        #         InstrumentClass.objects.using(using).create(pk=id, system_code=name, name=name, description=name)

    def create_data(self, model, verbosity, using):
        exists = set(model.objects.using(using).values_list('pk', flat=True))

        if verbosity >= 2:
            print('existed transaction classes -> %s' % exists)

        for id, name in model.CLASSES:
            if id not in exists:
                if verbosity >= 2:
                    print('create %s class -> %s:%s' % (model._meta.verbose_name, id, name))
                model.objects.using(using).create(pk=id, system_code=name, name=name, description=name)
