from __future__ import unicode_literals

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

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
class Currency(models.Model):
    master_user = models.ForeignKey(MasterUser, null=True, blank=True, related_name='currencies',
                                    verbose_name=_('master user'))
    user_code = models.CharField(max_length=25, null=True, blank=True, help_text=_('Some code, for example ISO 4217'))
    name = models.CharField(max_length=255, verbose_name=_('name'))
    short_name = models.CharField(max_length=50, null=True, blank=True, verbose_name=_('short name'))
    notes = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = _('currency')
        verbose_name_plural = _('currencies')
        unique_together = [
            ['master_user', 'user_code']
        ]

    def __str__(self):
        if self.is_global:
            return '%s (Global)' % (self.user_code,)
        else:
            return '%s (%s)' % (self.user_code, self.master_user.user.username)

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
    currency = models.ForeignKey(Currency, related_name='histories')
    # date = models.DateTimeField(db_index=True, default=timezone.now)
    date = models.DateField(null=False, blank=False, db_index=True, default=timezone.now)
    fx_rate = models.FloatField(verbose_name=_('fx rate'))

    class Meta:
        verbose_name = _('currency')
        verbose_name_plural = _('currency histories')
        index_together = [
            ['currency', 'date']
        ]
        ordering = ['-date']

    def __str__(self):
        return '%s @ %s - %s' % (self.currency, self.date, self.fx_rate,)
