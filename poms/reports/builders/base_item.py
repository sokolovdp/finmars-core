import copy
import csv
import logging
from io import StringIO

from poms.common.utils import isclose
from poms.reports.utils import sprint_table

_l = logging.getLogger('poms.reports')


class BaseReportItem:
    is_cloned = False
    report = None
    pricing_provider = None
    fx_rate_provider = None

    dump_columns = []

    def __init__(self, report, pricing_provider, fx_rate_provider):
        self.report = report
        self.pricing_provider = pricing_provider
        self.fx_rate_provider = fx_rate_provider

    def clone(self):
        ret = copy.copy(self)
        ret.is_cloned = True
        return ret

    @classmethod
    def dump_values(cls, obj, columns=None):
        if columns is None:
            columns = cls.dump_columns
        row = []
        for f in columns:
            v = getattr(obj, f)
            if isinstance(v, float):
                if isclose(v, 0.0):
                    v = 0.0
            row.append(v)
        return row

    @classmethod
    def transpose(cls, columns, data):
        ncols = ['attr']
        nrows = [[c] for c in columns]
        for irow, row in enumerate(data):
            ncols.append('%s' % irow)
            for icol, col in enumerate(row):
                nrows[icol].append(col)
        return ncols, nrows

    @classmethod
    def sdumps(cls, items, columns=None, filter=None, in_csv=False, transpose=False, showindex=None):
        if columns is None:
            columns = cls.dump_columns

        data = []
        for item in items:
            if filter and callable(filter):
                if filter(item):
                    pass
                else:
                    continue
            data.append(cls.dump_values(item, columns=columns))

        if in_csv:
            si = StringIO()
            cw = csv.writer(si)
            cw.writerow(columns)
            for r in data:
                cw.writerow(r)
            return si.getvalue()
        if transpose:
            columns, data = cls.transpose(columns=columns, data=data)
        return sprint_table(data, columns, showindex=showindex)

    @classmethod
    def dumps(cls, items, columns=None, trn_filter=None, in_csv=None):
        _l.debug('\n%s', cls.sdumps(items, columns=columns, filter=trn_filter, in_csv=in_csv))
