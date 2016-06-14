from __future__ import unicode_literals

import pytz
from django.conf import settings
from django.contrib.auth.models import User, Permission
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from poms.audit import history
from poms.common.models import NamedModel

AVAILABLE_APPS = ['accounts', 'counterparties', 'currencies', 'instruments', 'portfolios', 'strategies', 'transactions',
                  'reports', 'users']

LANGUAGE_MAX_LENGTH = 5
TIMEZONE_MAX_LENGTH = 20
TIMEZONE_CHOICES = sorted(list((k, k) for k in pytz.all_timezones))
TIMEZONE_COMMON_CHOICES = sorted(list((k, k) for k in pytz.common_timezones))


class MasterUserManager(models.Manager):
    def create(self, **kwargs):
        from poms.currencies.models import Currency
        from poms.accounts.models import AccountType, Account
        from poms.counterparties.models import Counterparty, Responsible
        from poms.portfolios.models import Portfolio
        from poms.instruments.models import InstrumentClass, InstrumentType, Instrument

        obj = super(MasterUserManager, self).create(kwargs)

        ccy = Currency.objects.create(master_user=obj, name='-')
        Currency.objects.create(master_user=obj, name=settings.CURRENCY_CODE)
        obj.currency = ccy
        obj.save(update_fields=['currency'])

        acc_t = AccountType.objects.create(master_user=obj, name='-')
        acc = Account.objects.create(master_user=obj, type=acc_t, name='-')

        Counterparty.objects.create(master_user=obj, name='-')
        Responsible.objects.create(master_user=obj, name='-')

        Portfolio.objects.create(master_user=obj, name='-')

        instr_cls = InstrumentClass.objects.get(pk=InstrumentClass.GENERAL)
        instr_t = InstrumentType.objects.create(master_user=obj, instrument_class=instr_cls, name='-')
        instr = Instrument.objects.create(master_user=obj, type=instr_t, pricing_currency=acc, accrued_currency=acc,
                                          name='-')

        return obj


@python_2_unicode_compatible
class MasterUser(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True,
                            verbose_name=_('name'))
    currency = models.ForeignKey('currencies.Currency', null=True, blank=True, on_delete=models.PROTECT,
                                 verbose_name=_('currency'))
    language = models.CharField(max_length=LANGUAGE_MAX_LENGTH, default=settings.LANGUAGE_CODE,
                                verbose_name=_('language'))
    timezone = models.CharField(max_length=TIMEZONE_MAX_LENGTH, default=settings.TIME_ZONE,
                                verbose_name=_('timezone'))

    class Meta:
        verbose_name = _('master user')
        verbose_name_plural = _('master users')

    def __str__(self):
        if self.name:
            return self.name
        else:
            try:
                return self._cached_str
            except AttributeError:
                ul = Member.objects.filter(master_user=self, is_owner=True).values_list('user__username', flat=True)
                self._cached_str = ', '.join(ul)
                return self._cached_str


@python_2_unicode_compatible
class Member(models.Model):
    master_user = models.ForeignKey(MasterUser, related_name='members',
                                    verbose_name=_('master user'))
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='members',
        verbose_name=_('user'),
    )

    username = models.CharField(max_length=255, blank=True, default='', editable=False, verbose_name=_('first name'))
    first_name = models.CharField(max_length=30, blank=True, default='', editable=False, verbose_name=_('first name'))
    last_name = models.CharField(max_length=30, blank=True, default='', editable=False, verbose_name=_('last name'))
    email = models.EmailField(blank=True, default='', editable=False, verbose_name=_('email'))

    join_date = models.DateTimeField(auto_now_add=True, verbose_name=_('join date'))
    is_owner = models.BooleanField(default=False, verbose_name=_('is owner'))
    is_admin = models.BooleanField(default=False, verbose_name=_('is admin'))

    groups = models.ManyToManyField('Group', blank=True, verbose_name=_('groups'))

    # permissions = models.ManyToManyField(Permission, blank=True)

    class Meta:
        verbose_name = _('member')
        verbose_name_plural = _('members')
        unique_together = [
            ['master_user', 'user']
        ]

    def __str__(self):
        # return '%s@%s' % (self.user.username, self.master_user)
        return '%s@%s' % (self.user.username, self.master_user)

    @property
    def is_superuser(self):
        return self.is_owner or self.is_admin


@python_2_unicode_compatible
class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='profile',
                                verbose_name=_('user'))
    language = models.CharField(max_length=LANGUAGE_MAX_LENGTH, default=settings.LANGUAGE_CODE,
                                verbose_name=_('language'))
    timezone = models.CharField(max_length=TIMEZONE_MAX_LENGTH, default=settings.TIME_ZONE,
                                verbose_name=_('timezone'))

    class Meta:
        verbose_name = _('profile')
        verbose_name_plural = _('profiles')

    def __str__(self):
        return self.user.username


@python_2_unicode_compatible
class Group(models.Model):
    master_user = models.ForeignKey(MasterUser, related_name='groups',
                                    verbose_name=_('master user'), )
    name = models.CharField(max_length=80,
                            verbose_name=_('name'))

    # permissions = models.ManyToManyField(Permission, verbose_name=_('permissions'), blank=True,
    #                                      related_name='poms_groups')

    class Meta:
        verbose_name = _('group')
        verbose_name_plural = _('groups')
        unique_together = [
            ['master_user', 'name']
        ]
        # permissions = [
        #     ('view_group', 'Can view group')
        # ]

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class FakeSequence(models.Model):
    master_user = models.ForeignKey(MasterUser, related_name='fake_sequences',
                                    verbose_name=_('master user'), )
    name = models.CharField(max_length=80)
    value = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = _('fake sequence')
        verbose_name_plural = _('fake sequences')
        unique_together = [
            ['master_user', 'name']
        ]
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


@receiver(post_save, dispatch_uid='update_member_when_user_update', sender=settings.AUTH_USER_MODEL)
def update_member_when_user_update(sender, instance=None, created=None, **kwargs):
    if not created:
        instance.members.all().update(
            username=instance.username,
            first_name=instance.first_name,
            last_name=instance.last_name,
            email=instance.email
        )


history.register(MasterUser)
history.register(Member)
history.register(User, follow=['profile'], exclude=['password'])
history.register(UserProfile, follow=['user'])
history.register(Group)
