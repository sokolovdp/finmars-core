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
        queryset = queryset.prefetch_related('transaction_class', 'instrument')
        if self.instance:
            queryset = queryset.filter(master_user=self.instance.master_user)
            if self.instance.begin_date:
                queryset = queryset.filter(transaction_date__gte=self.instance.begin_date)
            if self.instance.end_date:
                queryset = queryset.filter(transaction_date__lte=self.instance.end_date)
            if self.instance.instruments:
                queryset = queryset.filter(instrument__in=self.instance.instruments)
        queryset = queryset.order_by('transaction_date', 'id')
        return list(queryset.all())
        # return Transaction.objects.none()

    def build(self):
        raise NotImplementedError('subclasses of BaseReportBuilder must provide an build() method')
