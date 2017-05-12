from __future__ import unicode_literals

import json

from django.contrib.contenttypes.models import ContentType
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.utils.translation import ugettext_lazy

from poms.common.models import NamedModel, AbstractClassModel, EXPRESSION_FIELD_LENGTH
from poms.users.models import MasterUser


class CustomField(models.Model):
    master_user = models.ForeignKey(MasterUser, related_name='custom_fields', verbose_name=ugettext_lazy('master user'))
    name = models.CharField(max_length=255, verbose_name=ugettext_lazy('name'))
    expr = models.CharField(max_length=EXPRESSION_FIELD_LENGTH, verbose_name=ugettext_lazy('expression'))
    layout_json = models.TextField(null=True, blank=True, verbose_name=ugettext_lazy('layout json'))

    class Meta:
        verbose_name = ugettext_lazy('custom field')
        verbose_name_plural = ugettext_lazy('custom fields')
        unique_together = [
            ['master_user', 'name']
        ]

    def __str__(self):
        return self.name

    @property
    def layout(self):
        try:
            return json.loads(self.layout_json) if self.layout_json else None
        except (ValueError, TypeError):
            return None

    @layout.setter
    def layout(self, data):
        self.layout_json = json.dumps(data, cls=DjangoJSONEncoder, sort_keys=True) if data else None


class BalanceReport(models.Model):
    master_user = models.ForeignKey(MasterUser, related_name='balance_reports',
                                    verbose_name=ugettext_lazy('master user'))

    class Meta:
        verbose_name = ugettext_lazy('balance report')
        verbose_name_plural = ugettext_lazy('balance reports')


class PLReport(models.Model):
    master_user = models.ForeignKey(MasterUser, related_name='pl_reports', verbose_name=ugettext_lazy('master user'))

    class Meta:
        verbose_name = ugettext_lazy('p&l report')
        verbose_name_plural = ugettext_lazy('p&l report')


class PerformanceReport(models.Model):
    master_user = models.ForeignKey(MasterUser, related_name='performance_reports',
                                    verbose_name=ugettext_lazy('master user'))

    class Meta:
        verbose_name = ugettext_lazy('performance report')
        verbose_name_plural = ugettext_lazy('performance reports')


class CashFlowReport(models.Model):
    master_user = models.ForeignKey(MasterUser, related_name='cashflow_reports',
                                    verbose_name=ugettext_lazy('master user'))

    class Meta:
        verbose_name = ugettext_lazy('cash flow report')
        verbose_name_plural = ugettext_lazy('cash flow reports')


class TransactionReport(models.Model):
    master_user = models.ForeignKey(MasterUser, related_name='transaction_reports',
                                    verbose_name=ugettext_lazy('master user'))

    class Meta:
        verbose_name = ugettext_lazy('transaction report')
        verbose_name_plural = ugettext_lazy('transaction reports')
