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
    expr = models.TextField(default='')

    class Meta:
        verbose_name = _('pricing policy')
        verbose_name_plural = _('pricing policies')
        unique_together = [
            ['master_user', 'user_code']
        ]


class AccessData(models.Model):
    master_user = models.ForeignKey(MasterUser, related_name='access_datas', verbose_name=_('master user'))
    pricing_policy = models.ManyToManyField(PricingPolicy)
    username = models.CharField(max_length=255, blank=True)
    password = models.CharField(max_length=255, blank=True)
    data = models.TextField(blank=True)

    # pricing_policy = models.ForeignKey(PricingPolicy)
    # class Meta:
    #     unique_together = [
    #         ['pricing_policy', 'name']
    #     ]

# class AccessDataAttr(models.Model):
#     # pricing_policy = models.ForeignKey(PricingPolicy)
#     access_data = models.ForeignKey(AccessData)
#     name = models.CharField(max_length=255)
#     value = models.CharField(max_length=255, blank=True)
#
#     class Meta:
#         unique_together = [
#             ['pricing_policy', 'name']
#         ]
