from __future__ import unicode_literals

from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class TransactionsConfig(AppConfig):
    name = 'poms.transactions'
    # label = 'poms'
    verbose_name = _('Transactions')
