from __future__ import unicode_literals

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import ugettext_lazy as _
from mptt.fields import TreeManyToManyField

from poms.audit import history
from poms.common.models import NamedModel
from poms.obj_perms.models import AbstractGroupObjectPermission, AbstractUserObjectPermission


class Tag(NamedModel):
    master_user = models.ForeignKey(
        'users.MasterUser',
        related_name='tags',
        verbose_name=_('master user')
    )
    content_types = models.ManyToManyField(
        ContentType,
        related_name='tags',
        blank=True,
        verbose_name=_('content types')
    )

    account_types = models.ManyToManyField(
        'accounts.AccountType',
        related_name='tags',
        blank=True,
        verbose_name=_('account types')
    )
    accounts = models.ManyToManyField(
        'accounts.Account',
        related_name='tags',
        blank=True,
        verbose_name=_('accounts')
    )
    currencies = models.ManyToManyField(
        'currencies.Currency',
        related_name='tags',
        blank=True,
        verbose_name=_('currencies')
    )
    instrument_types = models.ManyToManyField(
        'instruments.InstrumentType',
        related_name='tags',
        blank=True,
        verbose_name=_('instrument types')
    )
    instruments = models.ManyToManyField(
        'instruments.Instrument',
        related_name='tags',
        blank=True,
        verbose_name=_('instruments')
    )
    counterparties = models.ManyToManyField(
        'counterparties.Counterparty',
        related_name='tags',
        blank=True,
        verbose_name=_('counterparties')
    )
    responsibles = models.ManyToManyField(
        'counterparties.Responsible',
        related_name='tags',
        blank=True,
        verbose_name=_('responsibles')
    )
    portfolios = models.ManyToManyField(
        'portfolios.Portfolio',
        related_name='tags',
        blank=True,
        verbose_name=_('portfolios')
    )
    transaction_types = models.ManyToManyField(
        'transactions.TransactionType',
        related_name='tags',
        blank=True,
        verbose_name=_('transaction types')
    )
    # strategies = TreeManyToManyField(
    #     'strategies.Strategy',
    #     related_name='tags',
    #     blank=True,
    #     verbose_name=_('strategies')
    # )
    strategies1 = TreeManyToManyField(
        'strategies.Strategy1',
        related_name='tags',
        blank=True,
        verbose_name=_('strategies 1')
    )
    strategies2 = TreeManyToManyField(
        'strategies.Strategy2',
        related_name='tags',
        blank=True,
        verbose_name=_('strategies 2')
    )
    strategies3 = TreeManyToManyField(
        'strategies.Strategy3',
        related_name='tags',
        blank=True,
        verbose_name=_('strategies 3')
    )

    class Meta(NamedModel.Meta):
        verbose_name = _('tag')
        verbose_name_plural = _('tags')
        permissions = [
            ('view_tag', 'Can view tag'),
            ('manage_tag', 'Can manage tag'),
        ]


class TagUserObjectPermission(AbstractUserObjectPermission):
    content_object = models.ForeignKey(
        Tag,
        related_name='user_object_permissions',
        verbose_name=_('content object')
    )

    class Meta(AbstractUserObjectPermission.Meta):
        verbose_name = _('tags - user permission')
        verbose_name_plural = _('tags - user permissions')


class TagGroupObjectPermission(AbstractGroupObjectPermission):
    content_object = models.ForeignKey(
        Tag,
        related_name='group_object_permissions',
        verbose_name=_('content object')
    )

    class Meta(AbstractGroupObjectPermission.Meta):
        verbose_name = _('tags - group permission')
        verbose_name_plural = _('tags - group permissions')


history.register(Tag, follow=['user_object_permissions', 'group_object_permissions'])
history.register(TagUserObjectPermission)
history.register(TagGroupObjectPermission)
