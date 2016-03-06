from __future__ import unicode_literals

import logging
import random

from poms.reports.backends.base import BaseReportBuilder
from poms.reports.models import BalanceReportItem

_l = logging.getLogger('poms.reports')


class BalanceReportBuilder(BaseReportBuilder):
    def build(self):
        self.instance.items = []
        self.instance.items.append(BalanceReportItem(1, random.randint(0, 100)))
        self.instance.items.append(BalanceReportItem(2, random.randint(0, 100)))
        return self.instance
