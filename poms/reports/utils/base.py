from __future__ import unicode_literals, division

import logging

_l = logging.getLogger('poms.reports')


class AbstractReport(object):
    def __init__(self, transactions=None):
        self._transactions = transactions

    def load(self):
        self._transactions = None

    def dump_transactions(self):
        if not self._transactions:
            _l.info('transactions is empty')
            return

        try:
            import pandas as pd
        except ImportError:
            _l.info('-' * 79)
            _l.info('transactions')
            for i, t in enumerate(self._transactions):
                _l.info('%s - %s', t)
            return

        index = ['instrument_id', 'instrument', 'position_size_with_sign', 'principal_with_sign']
        data = []
        for t in self._transactions:
            data.append([1, 'Газпром', 20., -30.])
        df = pd.DataFrame(data=data, columns=index)
        _l.info('transactions\n%s', df)
        _l.info('transactions\n%s', df.to_html())
