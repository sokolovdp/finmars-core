from __future__ import unicode_literals, division

from datetime import date

from poms.reports.backends.pl import PLReport2Builder
from poms.reports.models import PLReport
from poms.reports.tests.base import BaseReportTestCase, n
from poms.transactions.models import Transaction


class YTMTestCase(BaseReportTestCase):
    def setUp(self):
        super(YTMTestCase, self).setUp()

