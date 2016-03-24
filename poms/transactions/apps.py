from __future__ import unicode_literals

from django.apps import AppConfig
from django.db import DEFAULT_DB_ALIAS
from django.utils.translation import ugettext_lazy as _


class TransactionsConfig(AppConfig):
    name = 'poms.transactions'
    # label = 'poms'
    verbose_name = _('Transactions')

    def ready(self):
        from django.db.models.signals import post_migrate
        post_migrate.connect(self.update_transaction_classes)
        pass

    def update_transaction_classes(self, app_config, verbosity=2, using=DEFAULT_DB_ALIAS, **kwargs):
        from .models import TransactionClass

        if not isinstance(app_config, TransactionsConfig):
            return

        exists = set(TransactionClass.objects.using(using).values_list('pk', flat=True))

        if verbosity >= 2:
            print('existed transaction classes -> %s' % exists)

        for id, name in TransactionClass.CLASSES:
            if id not in exists:
                if verbosity >= 2:
                    print('create transaction class -> %s:%s' % (id, name))
                TransactionClass.objects.using(using).create(pk=id, system_code=name, name=name, description=name)
