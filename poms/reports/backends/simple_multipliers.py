# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import unicode_literals, division

import logging

from poms.reports.backends.base import BaseReportBuilder

_l = logging.getLogger('poms.reports')


class SimpleMultipliersReportBuilder(BaseReportBuilder):
    def build(self):
        self.annotate_avco_multiplier()
        self.annotate_fifo_multiplier()
        self.instance.results = self.transactions
        return self.instance
