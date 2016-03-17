# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import unicode_literals, division

import logging

from poms.reports.backends.base import BaseReportBuilder

_l = logging.getLogger('poms.reports')


class SimpleMultipliersReportBuilder(BaseReportBuilder):
    def __init__(self, *args, **kwargs):
        super(SimpleMultipliersReportBuilder, self).__init__(*args, **kwargs)
        self._filter_date_attr = 'accounting_date'

    def build(self):
        self.annotate_avco_multiplier()
        self.annotate_fifo_multiplier()
        self.instance.results = self.transactions
        return self.instance
