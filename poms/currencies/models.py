from __future__ import unicode_literals

from django.conf import settings
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from poms.common.models import NamedModel
from poms.common.utils import date_now
from poms.instruments.models import PriceDownloadMode
from poms.obj_perms.models import AbstractUserObjectPermission, AbstractGroupObjectPermission
from poms.users.models import MasterUser


@python_2_unicode_compatible
class Currency(NamedModel):
    master_user = models.ForeignKey(MasterUser, related_name='currencies', verbose_name=_('master user'))
    isin = models.CharField(max_length=100, blank=True, default='', verbose_name=_('ISIN'))
    history_download_mode = models.ForeignKey(PriceDownloadMode, default=PriceDownloadMode.MANUAL)

    class Meta(NamedModel.Meta):
        verbose_name = _('currency')
        verbose_name_plural = _('currencies')
        permissions = [
            ('view_currency', 'Can view currency'),
            ('manage_currency', 'Can manage currency'),
        ]

    def __str__(self):
        return self.name

    @property
    def is_system(self):
        return self.user_code == settings.CURRENCY_CODE

    @property
    def is_default(self):
        return self.master_user.currency_id == self.id if self.master_user_id else False


class CurrencyUserObjectPermission(AbstractUserObjectPermission):
    content_object = models.ForeignKey(Currency, related_name='user_object_permissions',
                                       verbose_name=_('content object'))

    class Meta(AbstractUserObjectPermission.Meta):
        verbose_name = _('currencies - user permission')
        verbose_name_plural = _('currencies - user permissions')


class CurrencyGroupObjectPermission(AbstractGroupObjectPermission):
    content_object = models.ForeignKey(Currency, related_name='group_object_permissions',
                                       verbose_name=_('content object'))

    class Meta(AbstractGroupObjectPermission.Meta):
        verbose_name = _('currencies - group permission')
        verbose_name_plural = _('currencies - group permissions')


# EUR -> USD
# RUB -> USD
# ...
@python_2_unicode_compatible
class CurrencyHistory(models.Model):
    currency = models.ForeignKey(Currency, related_name='histories',
                                 verbose_name=_('currency'))
    pricing_policy = models.ForeignKey('instruments.PricingPolicy', on_delete=models.PROTECT, null=True, blank=True,
                                       verbose_name=_('pricing policy'))
    date = models.DateField(db_index=True, default=date_now,
                            verbose_name=_('date'))
    fx_rate = models.FloatField(default=0.,
                                verbose_name=_('fx rate'))

    class Meta:
        verbose_name = _('currency history')
        verbose_name_plural = _('currency histories')
        unique_together = (
            ('currency', 'pricing_policy', 'date',)
        )
        ordering = ['-date']

    def __str__(self):
        return '%s/%s@%s,%s' % (self.currency, self.pricing_policy, self.date, self.fx_rate)
