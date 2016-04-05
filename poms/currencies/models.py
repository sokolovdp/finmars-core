from __future__ import unicode_literals

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from poms.audit import history
from poms.common.models import NamedModel
from poms.users.models import MasterUser


# @python_2_unicode_compatible
# class CurrencySource(models.Model):
#     code = models.CharField(max_length=50, verbose_name=_('internal code'), unique=True)
#     name = models.CharField(max_length=255, verbose_name=_('name'))
#
#     class Meta:
#         verbose_name = _('currency source')
#         verbose_name_plural = _('currency sources')
#
#     def __str__(self):
#         return '%s' % (self.name,)


@python_2_unicode_compatible
class Currency(NamedModel):
    master_user = models.ForeignKey(MasterUser, null=True, blank=True, related_name='currencies',
                                    verbose_name=_('master user'))

    class Meta:
        verbose_name = _('currency')
        verbose_name_plural = _('currencies')
        unique_together = [
            ['master_user', 'user_code']
        ]
        permissions = [
            ('view_currency', 'Can view currency')
        ]

    def __str__(self):
        return self.name

    @property
    def is_global(self):
        return self.master_user_id is None

    @property
    def is_system(self):
        return self.is_global and self.user_code == settings.CURRENCY_CODE


# EUR -> USD
# RUB -> USD
# ...
@python_2_unicode_compatible
class CurrencyHistory(models.Model):
    master_user = models.ForeignKey(MasterUser, null=True, blank=True, related_name='fx_rates',
                                    verbose_name=_('master user'))
    currency = models.ForeignKey(Currency, related_name='histories')
    pricing_policy = models.ForeignKey('integrations.PricingPolicy', null=True, blank=True)
    # date = models.DateTimeField(db_index=True, default=timezone.now)
    date = models.DateField(db_index=True, default=timezone.now)
    fx_rate = models.FloatField(default=0., verbose_name=_('fx rate'))

    class Meta:
        verbose_name = _('currency history')
        verbose_name_plural = _('currency histories')
        index_together = [
            ['currency', 'date']
        ]
        ordering = ['-date']
        permissions = [
            ('view_currencyhistory', 'Can view currency history')
        ]

    def __str__(self):
        return '%s @ %s - %s' % (self.currency, self.date, self.fx_rate,)

    @property
    def is_global(self):
        return self.master_user_id is None


history.register(Currency)
history.register(CurrencyHistory)
