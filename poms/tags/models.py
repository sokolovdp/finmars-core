from __future__ import unicode_literals

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import ugettext_lazy as _
from mptt.fields import TreeManyToManyField

from poms.audit import history
from poms.common.models import TagModelBase
from poms.obj_perms.models import UserObjectPermissionBase, GroupObjectPermissionBase


class Tag(TagModelBase):
    master_user = models.ForeignKey('users.MasterUser', related_name='tags', verbose_name=_('master user'))
    content_type = models.ManyToManyField(ContentType, blank=True, related_name='+')

    # available_for_account = models.BooleanField(default=True)
    # available_for_currency = models.BooleanField(default=True)
    # available_for_instrument_type = models.BooleanField(default=True)
    # available_for_instrument = models.BooleanField(default=True)
    # available_for_counterparty = models.BooleanField(default=True)
    # available_for_responsible = models.BooleanField(default=True)
    # available_for_portfolio = models.BooleanField(default=True)
    # available_for_transaction_type = models.BooleanField(default=True)

    accounts = models.ManyToManyField('accounts.Account', blank=True, related_name='tags')
    currencies = models.ManyToManyField('currencies.Currency', blank=True, related_name='tags')
    instrument_types = models.ManyToManyField('instruments.InstrumentType', blank=True, related_name='tags')
    instruments = models.ManyToManyField('instruments.Instrument', blank=True, related_name='tags')
    counterparties = models.ManyToManyField('counterparties.Counterparty', blank=True, related_name='tags')
    responsibles = models.ManyToManyField('counterparties.Responsible', blank=True, related_name='tags')
    strategies = TreeManyToManyField('strategies.Strategy', blank=True, related_name='tags')
    portfolios = models.ManyToManyField('portfolios.Portfolio', blank=True, related_name='tags')
    transaction_types = models.ManyToManyField('transactions.TransactionType', blank=True, related_name='tags')

    class Meta:
        verbose_name = _('tag')
        verbose_name_plural = _('tags')
        permissions = [
            ('view_tag', 'Can view tag'),
            ('manage_tag', 'Can manage tag'),
        ]


class TagUserObjectPermission(UserObjectPermissionBase):
    content_object = models.ForeignKey(Tag, related_name='user_object_permissions')

    class Meta:
        verbose_name = _('tags - user permission')
        verbose_name_plural = _('tags - user permissions')


class TagGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(Tag, related_name='group_object_permissions')

    class Meta:
        verbose_name = _('tags - group permission')
        verbose_name_plural = _('tags - group permissions')


history.register(Tag)
