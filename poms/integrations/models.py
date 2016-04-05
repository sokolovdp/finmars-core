from django.db import models
from django.utils.translation import ugettext_lazy as _

from poms.common.models import NamedModel
from poms.users.models import MasterUser


class PricingPolicy(NamedModel):
    DISABLED = 0
    BLOOMBERG = 1
    TYPES = (
        (DISABLED, _('Disabled')),
        (BLOOMBERG, _('Bloomberg')),
    )

    master_user = models.ForeignKey(MasterUser, related_name='pricing_policies', verbose_name=_('master user'))
    type = models.PositiveIntegerField(default=DISABLED, choices=TYPES)

    class Meta:
        verbose_name = _('pricing policy')
        verbose_name_plural = _('pricing policies')
        unique_together = [
            ['master_user', 'user_code']
        ]


class PricingPolicyAttr(models.Model):
    pricing_policy = models.ForeignKey(PricingPolicy)
    name = models.CharField(max_length=255)
    value = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = [
            ['pricing_policy', 'name']
        ]
