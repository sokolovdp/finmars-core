from __future__ import unicode_literals

from django.utils.functional import cached_property

from poms.transactions.models import Transaction


class BaseReportBuilder(object):
    def __init__(self, instance=None, queryset=None):
        self.instance = instance
        self.queryset = queryset

    @cached_property
    def transactions(self):
        if self.queryset is None:
            queryset = Transaction.objects
        else:
            queryset = self.queryset
        if self.instance:
            if self.instance.begin_date:
                queryset = queryset.filter(date__gte=self.instance.begin_date)
            if self.instance.end_date:
                queryset = queryset.filter(date__lte=self.instance.end_date)
        queryset = queryset.order_by('date', 'id')
        return list(queryset.all())
        # return Transaction.objects.none()

    def build(self):
        raise NotImplementedError('subclasses of BaseReportBuilder must provide an build() method')
