from __future__ import unicode_literals

from django.apps import AppConfig
from django.db import DEFAULT_DB_ALIAS
from django.db.models.signals import post_migrate
from django.utils.translation import ugettext_lazy


class ReportsConfig(AppConfig):
    name = 'poms.reports'
    # label = 'poms_reports'
    verbose_name = ugettext_lazy('Reports')

    def ready(self):
        post_migrate.connect(self.update_transaction_classes, sender=self)

    def update_transaction_classes(self, app_config, verbosity=2, using=DEFAULT_DB_ALIAS, **kwargs):
        from poms.common.utils import db_class_check_data
        from poms.reports.models import ReportClass

        db_class_check_data(ReportClass, verbosity, using)
