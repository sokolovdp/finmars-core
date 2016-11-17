from __future__ import unicode_literals

import pycountry
import pytz
from django.conf import settings
from django.contrib.auth.models import User, Permission
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy

from poms.common.models import NamedModel, FakeDeletableModel

AVAILABLE_APPS = ['accounts', 'counterparties', 'currencies', 'instruments', 'portfolios', 'strategies', 'transactions',
                  'reports', 'users']

LANGUAGE_MAX_LENGTH = 5
TIMEZONE_MAX_LENGTH = 20
TIMEZONE_CHOICES = sorted(list((k, k) for k in pytz.all_timezones))
TIMEZONE_COMMON_CHOICES = sorted(list((k, k) for k in pytz.common_timezones))


class MasterUserManager(models.Manager):
    def create_master_user(self, user=None, **kwargs):
        from poms.currencies.models import Currency
        from poms.accounts.models import AccountType, Account
        from poms.counterparties.models import Counterparty, CounterpartyGroup, Responsible, ResponsibleGroup
        from poms.portfolios.models import Portfolio
        from poms.instruments.models import InstrumentClass, InstrumentType, EventScheduleConfig, Instrument
        from poms.integrations.models import PricingAutomatedSchedule
        from poms.strategies.models import Strategy1Group, Strategy1Subgroup, Strategy1, Strategy2Group, \
            Strategy2Subgroup, Strategy2, Strategy3Group, Strategy3Subgroup, Strategy3
        from poms.chats.models import ThreadGroup
        from poms.obj_perms.utils import assign_perms3, get_change_perms

        obj = MasterUser(**kwargs)
        obj.save()

        EventScheduleConfig.objects.create(master_user=obj)
        PricingAutomatedSchedule.objects.create(master_user=obj, is_enabled=False)

        ccy = Currency.objects.create(master_user=obj, name='-')
        ccy_usd = Currency.objects.create(master_user=obj, name='USD')

        for c in pycountry.currencies:
            if c.alpha_3 != 'USD':
                Currency.objects.create(master_user=obj, user_code=c.alpha_3, name=c.name)

        account_type = AccountType.objects.create(master_user=obj, name='-')
        account = Account.objects.create(master_user=obj, type=account_type, name='-')

        counterparty_group = CounterpartyGroup.objects.create(master_user=obj, name='-')
        counterparty = Counterparty.objects.create(master_user=obj, group=counterparty_group, name='-')
        responsible_group = ResponsibleGroup.objects.create(master_user=obj, name='-')
        responsible = Responsible.objects.create(master_user=obj, group=responsible_group, name='-')

        portfolio = Portfolio.objects.create(master_user=obj, name='-')

        instrument_general_class = InstrumentClass.objects.get(pk=InstrumentClass.GENERAL)
        instrument_type = InstrumentType.objects.create(master_user=obj, instrument_class=instrument_general_class,
                                                        name='-')
        instrument = Instrument.objects.create(master_user=obj, instrument_type=instrument_type, pricing_currency=ccy,
                                               accrued_currency=ccy, name='-')

        strategy1_group = Strategy1Group.objects.create(master_user=obj, name='-')
        strategy1_subgroup = Strategy1Subgroup.objects.create(master_user=obj, group=strategy1_group, name='-')
        strategy1 = Strategy1.objects.create(master_user=obj, subgroup=strategy1_subgroup, name='-')

        strategy2_group = Strategy2Group.objects.create(master_user=obj, name='-')
        strategy2_subgroup = Strategy2Subgroup.objects.create(master_user=obj, group=strategy2_group, name='-')
        strategy2 = Strategy2.objects.create(master_user=obj, subgroup=strategy2_subgroup, name='-')

        strategy3_group = Strategy3Group.objects.create(master_user=obj, name='-')
        strategy3_subgroup = Strategy3Subgroup.objects.create(master_user=obj, group=strategy3_group, name='-')
        strategy3 = Strategy3.objects.create(master_user=obj, subgroup=strategy3_subgroup, name='-')

        thread_group = ThreadGroup.objects.create(master_user=obj, name='-')

        if user:
            Member.objects.create(user=user, master_user=obj, is_owner=True, is_admin=True)
        group = Group.objects.create(master_user=obj, name='%s' % ugettext_lazy('Default'))

        obj.system_currency = ccy_usd
        obj.currency = ccy
        obj.account_type = account_type
        obj.account = account
        obj.counterparty_group = counterparty_group
        obj.counterparty = counterparty
        obj.responsible_group = responsible_group
        obj.responsible = responsible
        obj.portfolio = portfolio
        obj.instrument_type = instrument_type
        obj.instrument = instrument
        obj.strategy1_group = strategy1_group
        obj.strategy1_subgroup = strategy1_subgroup
        obj.strategy1 = strategy1
        obj.strategy2_group = strategy2_group
        obj.strategy2_subgroup = strategy2_subgroup
        obj.strategy2 = strategy2
        obj.strategy3_group = strategy3_group
        obj.strategy3_subgroup = strategy3_subgroup
        obj.strategy3 = strategy3
        obj.thread_group = thread_group
        obj.save()

        for c in [account_type, account, counterparty_group, counterparty, responsible_group, responsible, portfolio,
                  instrument_type, instrument, strategy1_group, strategy1_subgroup, strategy1, strategy2_group,
                  strategy2_subgroup, strategy2, strategy3_group, strategy3_subgroup, strategy3, thread_group]:
            for p in get_change_perms(c):
                assign_perms3(c, perms=[{'group': group, 'permission': p}])

        return obj


@python_2_unicode_compatible
class MasterUser(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True,
                            verbose_name=ugettext_lazy('name'))
    language = models.CharField(max_length=LANGUAGE_MAX_LENGTH, default=settings.LANGUAGE_CODE,
                                verbose_name=ugettext_lazy('language'))
    timezone = models.CharField(max_length=TIMEZONE_MAX_LENGTH, default=settings.TIME_ZONE,
                                verbose_name=ugettext_lazy('timezone'))
    system_currency = models.ForeignKey('currencies.Currency', null=True, blank=True, on_delete=models.PROTECT,
                                        related_name='+',
                                        verbose_name=ugettext_lazy('system currency'))

    account_type = models.ForeignKey('accounts.AccountType', null=True, blank=True, on_delete=models.PROTECT)
    account = models.ForeignKey('accounts.Account', null=True, blank=True, on_delete=models.PROTECT)

    currency = models.ForeignKey('currencies.Currency', null=True, blank=True, on_delete=models.PROTECT,
                                 verbose_name=ugettext_lazy('currency'))
    counterparty_group = models.ForeignKey('counterparties.CounterpartyGroup', null=True, blank=True,
                                           on_delete=models.PROTECT)
    counterparty = models.ForeignKey('counterparties.Counterparty', null=True, blank=True, on_delete=models.PROTECT)
    responsible_group = models.ForeignKey('counterparties.ResponsibleGroup', null=True, blank=True,
                                          on_delete=models.PROTECT)
    responsible = models.ForeignKey('counterparties.Responsible', null=True, blank=True, on_delete=models.PROTECT)

    instrument_type = models.ForeignKey('instruments.InstrumentType', null=True, blank=True, on_delete=models.PROTECT)
    instrument = models.ForeignKey('instruments.Instrument', null=True, blank=True, on_delete=models.PROTECT)

    portfolio = models.ForeignKey('portfolios.Portfolio', null=True, blank=True, on_delete=models.PROTECT)

    strategy1_group = models.ForeignKey('strategies.Strategy1Group', null=True, blank=True, on_delete=models.PROTECT,
                                        related_name='master_user_strategy1_group')
    strategy1_subgroup = models.ForeignKey('strategies.Strategy1Subgroup', null=True, blank=True,
                                           on_delete=models.PROTECT, related_name='master_user_strategy1_subgroup')
    strategy1 = models.ForeignKey('strategies.Strategy1', null=True, blank=True, on_delete=models.PROTECT,
                                  related_name='master_user_strategy1')

    strategy2_group = models.ForeignKey('strategies.Strategy2Group', null=True, blank=True, on_delete=models.PROTECT,
                                        related_name='master_user_strategy2_group')
    strategy2_subgroup = models.ForeignKey('strategies.Strategy2Subgroup', null=True, blank=True,
                                           on_delete=models.PROTECT, related_name='master_user_strategy2_subgroup')
    strategy2 = models.ForeignKey('strategies.Strategy2', null=True, blank=True, on_delete=models.PROTECT,
                                  related_name='master_user_strategy2')

    strategy3_group = models.ForeignKey('strategies.Strategy3Group', null=True, blank=True, on_delete=models.PROTECT,
                                        related_name='master_user_strategy3_group')
    strategy3_subgroup = models.ForeignKey('strategies.Strategy3Subgroup', null=True, blank=True,
                                           on_delete=models.PROTECT, related_name='master_user_strategy3_subgroup')
    strategy3 = models.ForeignKey('strategies.Strategy3', null=True, blank=True, on_delete=models.PROTECT,
                                  related_name='master_user_strategy3')

    thread_group = models.ForeignKey('chats.ThreadGroup', null=True, blank=True, on_delete=models.PROTECT,
                                     related_name='master_user_thread_group')

    # TODO: what is notification_business_days
    notification_business_days = models.IntegerField(default=0)

    objects = MasterUserManager()

    class Meta:
        verbose_name = ugettext_lazy('master user')
        verbose_name_plural = ugettext_lazy('master users')
        ordering = ['name']

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Member(FakeDeletableModel):
    master_user = models.ForeignKey(MasterUser, related_name='members', verbose_name=ugettext_lazy('master user'))
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                             related_name='members', verbose_name=ugettext_lazy('user'), )

    username = models.CharField(max_length=255, blank=True, default='', editable=False)
    first_name = models.CharField(max_length=30, blank=True, default='', editable=False)
    last_name = models.CharField(max_length=30, blank=True, default='', editable=False)
    email = models.EmailField(blank=True, default='', editable=False)

    join_date = models.DateTimeField(auto_now_add=True, verbose_name=ugettext_lazy('join date'))
    is_owner = models.BooleanField(default=False, verbose_name=ugettext_lazy('is owner'))
    is_admin = models.BooleanField(default=False, verbose_name=ugettext_lazy('is admin'))

    groups = models.ManyToManyField('Group', blank=True, related_name='members', verbose_name=ugettext_lazy('groups'))

    # permissions = models.ManyToManyField(Permission, blank=True)

    class Meta(FakeDeletableModel.Meta):
        verbose_name = ugettext_lazy('member')
        verbose_name_plural = ugettext_lazy('members')
        unique_together = [
            ['master_user', 'user']
        ]
        ordering = ['username']

    def __str__(self):
        return self.username

    def fake_delete(self):
        self.user = None
        self.is_deleted = True
        self.save(update_fields=['user', 'is_deleted'])

    @property
    def is_superuser(self):
        return self.is_owner or self.is_admin

    @property
    def display_name(self):
        if self.first_name or self.last_name:
            return ' '.join([self.first_name, self.last_name])
        else:
            return self.username


@python_2_unicode_compatible
class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='profile',
                                verbose_name=ugettext_lazy('user'))
    language = models.CharField(max_length=LANGUAGE_MAX_LENGTH, default=settings.LANGUAGE_CODE,
                                verbose_name=ugettext_lazy('language'))
    timezone = models.CharField(max_length=TIMEZONE_MAX_LENGTH, default=settings.TIME_ZONE,
                                verbose_name=ugettext_lazy('timezone'))

    class Meta:
        verbose_name = ugettext_lazy('profile')
        verbose_name_plural = ugettext_lazy('profiles')

    def __str__(self):
        return self.user.username


@python_2_unicode_compatible
class Group(models.Model):
    master_user = models.ForeignKey(MasterUser, related_name='groups',
                                    verbose_name=ugettext_lazy('master user'), )
    name = models.CharField(max_length=80,
                            verbose_name=ugettext_lazy('name'))

    # permissions = models.ManyToManyField(Permission, verbose_name=ugettext_lazy('permissions'), blank=True,
    #                                      related_name='poms_groups')

    class Meta:
        verbose_name = ugettext_lazy('group')
        verbose_name_plural = ugettext_lazy('groups')
        unique_together = [
            ['master_user', 'name']
        ]
        ordering = ['name']
        # permissions = [
        #     ('view_group', 'Can view group')
        # ]

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class FakeSequence(models.Model):
    master_user = models.ForeignKey(MasterUser, related_name='fake_sequences',
                                    verbose_name=ugettext_lazy('master user'), )
    name = models.CharField(max_length=80)
    value = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = ugettext_lazy('fake sequence')
        verbose_name_plural = ugettext_lazy('fake sequences')
        unique_together = [
            ['master_user', 'name']
        ]
        ordering = ['name']
        # permissions = [
        #     ('view_group', 'Can view group')
        # ]

    def __str__(self):
        return "%s: %s" % (self.name, self.value)

    # @staticmethod
    # def inc1(master_user, name):
    #     for i in range(20):
    #         seq = SimpleSequence.objects.get_or_create(master_user=master_user, name=name)
    #         newval = seq.value + 1
    #         updated = SimpleSequence.objects.filter(id=seq.id, value=seq.value).update(value=newval)
    #         if updated == 1:
    #             return newval
    #     return RuntimeError('simple sequence optimistic lock error')

    @classmethod
    def next_value(cls, master_user, name, count=0):
        # seq = SimpleSequence.objects.select_for_update().get_or_create(master_user=master_user, name=name)
        # seq = SimpleSequence.objects.select_for_update().get(master_user=master_user, name=name)
        seq, _ = cls.objects.get_or_create(master_user=master_user, name=name)
        newval = seq.value + 1
        seq.value = newval + count
        seq.save(update_fields=['value'])
        return newval


@receiver(post_save, dispatch_uid='create_profile', sender=settings.AUTH_USER_MODEL)
def create_profile(sender, instance=None, created=None, **kwargs):
    if created:
        UserProfile.objects.create(
            user=instance,
            language=settings.LANGUAGE_CODE,
            timezone=settings.TIME_ZONE,
        )


@receiver(post_save, dispatch_uid='update_member_when_member_created', sender=Member)
def update_member_when_member_created(sender, instance=None, created=None, **kwargs):
    if created:
        instance.username = instance.user.username
        instance.first_name = instance.user.first_name
        instance.last_name = instance.user.last_name
        instance.email = instance.user.email
        instance.save(update_fields=['username', 'first_name', 'last_name', 'email'])


@receiver(post_save, dispatch_uid='update_member_when_user_updated', sender=settings.AUTH_USER_MODEL)
def update_member_when_user_updated(sender, instance=None, created=None, **kwargs):
    if not created:
        instance.members.all().update(
            username=instance.username,
            first_name=instance.first_name,
            last_name=instance.last_name,
            email=instance.email
        )
