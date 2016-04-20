from __future__ import unicode_literals

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from poms.audit import history
from poms.common.models import NamedModel
from poms.obj_perms.models import UserObjectPermissionBase, GroupObjectPermissionBase
from poms.users.models import MasterUser


@python_2_unicode_compatible
class Currency(NamedModel):
    master_user = models.ForeignKey(MasterUser, related_name='currencies',
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


class CurrencyUserObjectPermission(UserObjectPermissionBase):
    content_object = models.ForeignKey(Currency, related_name='user_object_permissions',
                                       verbose_name=_('content object'))

    class Meta:
        verbose_name = _('counterparties - user permission')
        verbose_name_plural = _('counterparties - user permissions')


class CurrencyGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(Currency, related_name='group_object_permissions',
                                       verbose_name=_('content object'))

    class Meta:
        verbose_name = _('counterparties - group permission')
        verbose_name_plural = _('counterparties - group permissions')


# EUR -> USD
# RUB -> USD
# ...
@python_2_unicode_compatible
class CurrencyHistory(models.Model):
    currency = models.ForeignKey(Currency, related_name='histories',
                                 verbose_name=_('currency'))
    pricing_policy = models.ForeignKey('integrations.PricingPolicy', on_delete=models.PROTECT, null=True, blank=True,
                                       verbose_name=_('pricing policy'))
    date = models.DateField(db_index=True, default=timezone.now,
                            verbose_name=_('date'))
    fx_rate = models.FloatField(default=0.,
                                verbose_name=_('fx rate'))

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


history.register(Currency)
history.register(CurrencyHistory)
