from __future__ import unicode_literals

import uuid

from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import python_2_unicode_compatible

from poms.users.models import MasterUser


# @python_2_unicode_compatible
# class ReportType(models.Model):
#     code = models.CharField(max_length=50, verbose_name=_('code'))
#     name = models.CharField(max_length=255, verbose_name=_('name'))
#     description = models.TextField(null=True, blank=True, default='', verbose_name=_('description'))
#
#     class Meta:
#         verbose_name = _('report type')
#         verbose_name_plural = _('report types')
#
#     def __str__(self):
#         return '%s' % (self.name,)
#
#
# @python_2_unicode_compatible
# class Mapping(models.Model):
#     master_user = models.ForeignKey(MasterUser, related_name='report_mappings', verbose_name=_('master user'))
#     content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
#     object_id = models.CharField(max_length=255)
#     content_object = GenericForeignKey('content_type', 'object_id')
#     name = models.CharField(max_length=255, verbose_name=_('object attribute'))
#     expr = models.TextField(null=True, blank=True, verbose_name=_('expression'))
#
#     class Meta:
#         verbose_name = _('mapping')
#         verbose_name_plural = _('mappings')
#
#     def __str__(self):
#         return '%s #%s - %s' % (self.content_type, self.object_id, self.name)

@python_2_unicode_compatible
class BaseReportItem(object):
    def __init__(self, pk=None):
        self.pk = pk or uuid.uuid1()

    def __str__(self):
        return "%s #%s" % (self.__class__.__name__, self.pk,)


@python_2_unicode_compatible
class BaseReport(object):
    def __init__(self, master_user=None, begin_date=None, end_date=None, instruments=None, results=None):
        self.master_user = master_user
        self.begin_date = begin_date
        self.end_date = end_date
        self.instruments = instruments
        self.results = results

    def __str__(self):
        return "%s for %s (%s, %s)" % (self.__class__.__name__, self.master_user, self.begin_date, self.end_date)

    @property
    def count(self):
        return len(self.results) if self.results else 0


@python_2_unicode_compatible
class BalanceReportItem(BaseReportItem):
    def __init__(self, instrument=None, currency=None, position_size_with_sign=0., *args, **kwargs):
        super(BalanceReportItem, self).__init__(*args, **kwargs)
        self.instrument = instrument
        self.currency = currency
        self.position_size_with_sign = position_size_with_sign

    def __str__(self):
        if self.instrument:
            return "%s - %s" % (self.instrument, self.position_size_with_sign)
        else:
            return "%s - %s" % (self.currency, self.position_size_with_sign)


@python_2_unicode_compatible
class BalanceReportSummary(object):
    def __init__(self, invested_value=0., current_value=0., p_and_l=0.):
        self.invested_value = invested_value
        self.current_value = current_value
        self.p_and_l = p_and_l

    def __str__(self):
        return "%s: invested=%s, current=%s, p_and_l=%s" % \
               (self.currency, self.invested_value, self.current_value, self.p_and_l)


# @python_2_unicode_compatible
class BalanceReport(BaseReport):
    def __init__(self, currency=None, summary=None, *args, **kwargs):
        super(BalanceReport, self).__init__(*args, **kwargs)
        self.currency = currency
        self.summary = summary
