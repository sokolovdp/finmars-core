from __future__ import unicode_literals

from django.apps import AppConfig
from django.utils.translation import ugettext_lazy


class AccountsConfig(AppConfig):
    name = 'poms.accounts'
    # label = 'poms'
    verbose_name = ugettext_lazy('Accounts')
