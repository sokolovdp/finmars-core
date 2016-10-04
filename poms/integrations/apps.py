from __future__ import unicode_literals, print_function

from django.apps import AppConfig
from django.db import DEFAULT_DB_ALIAS
from django.db.models.signals import post_migrate
from django.utils.translation import ugettext_lazy


class IntegrationsConfig(AppConfig):
    name = 'poms.integrations'
    verbose_name = ugettext_lazy('Integrations')

    def ready(self):
        post_migrate.connect(self.update_transaction_classes, sender=self)

        # noinspection PyUnresolvedReferences
        import poms.integrations.handlers

    def update_transaction_classes(self, app_config, verbosity=2, using=DEFAULT_DB_ALIAS, **kwargs):
        from poms.common.utils import db_class_check_data
        from .models import ProviderClass, FactorScheduleDownloadMethod, AccrualScheduleDownloadMethod

        # if not isinstance(app_config, IntegrationsConfig):
        #     return

        db_class_check_data(ProviderClass, verbosity, using)
        db_class_check_data(FactorScheduleDownloadMethod, verbosity, using)
        db_class_check_data(AccrualScheduleDownloadMethod, verbosity, using)
