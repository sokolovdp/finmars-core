from __future__ import unicode_literals

import logging
import random

from poms.reports.backends.base import BaseReportBuilder
from poms.reports.models import BalanceReportItem
from poms.transactions.models import TransactionClass

_l = logging.getLogger('poms.reports')


class SimpleMultipliersReportBuilder(BaseReportBuilder):

    def build(self):
        self.annotate_avco_multiplier()
        self.annotate_fifo_multiplier()
        self.instance.results = self.transactions
        return self.instance
