from __future__ import unicode_literals

from django.conf import settings
from django.contrib.auth.models import User, Permission
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from poms.audit import history
from poms.common.fields import TimezoneField, LanguageField
from poms.common.models import NamedModel

AVAILABLE_APPS = ['accounts', 'counterparties', 'currencies', 'instruments', 'portfolios', 'strategies', 'transactions',
                  'reports', 'users']


@python_2_unicode_compatible
class MasterUser(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True,
                            verbose_name=_('name'))
    currency = models.ForeignKey('currencies.Currency', null=True, blank=True, on_delete=models.PROTECT,
                                 verbose_name=_('currency'))

    # members = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, through='Member', related_name='member_of')

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
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='members',
                             verbose_name=_('user'))

    first_name = models.CharField(max_length=30, blank=True, default='', editable=False,
                                  verbose_name=_('first name'))
    last_name = models.CharField(max_length=30, blank=True, default='', editable=False,
                                 verbose_name=_('last name'))
    email = models.EmailField(blank=True, default='', editable=False,
                              verbose_name=_('email'))

    join_date = models.DateTimeField(auto_now_add=True,
                                     verbose_name=_('join date'))
    is_owner = models.BooleanField(default=False,
                                   verbose_name=_('is owner'))
    is_admin = models.BooleanField(default=False,
                                   verbose_name=_('is admin'))

    groups = models.ManyToManyField('Group', blank=True,
                                    verbose_name=_('groups'))

    # permissions = models.ManyToManyField(Permission, blank=True)

    def __str__(self):
        return '%s@%s' % (self.user.username, self.master_user)


@python_2_unicode_compatible
class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='profile',
                                verbose_name=_('user'))
    language = LanguageField(null=True, blank=True,
                             verbose_name=_('language'))
    timezone = TimezoneField(null=True, blank=True,
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
    name = models.CharField(max_length=80, unique=True,
                            verbose_name=_('name'))

    # permissions = models.ManyToManyField(Permission, verbose_name=_('permissions'), blank=True,
    #                                      related_name='poms_groups')

    class Meta:
        verbose_name = _('group')
        verbose_name_plural = _('group')
        unique_together = [
            ['master_user', 'name']
        ]

    def __str__(self):
        return self.name


@receiver(post_save, dispatch_uid='members_fill_from_user', sender=settings.AUTH_USER_MODEL)
def members_fill_from_user(sender, instance=None, created=None, **kwargs):
    if not created:
        instance.members.all().update(
            first_name=instance.first_name,
            last_name=instance.last_name,
            email=instance.email
        )


@receiver(post_save, dispatch_uid='members_fill_from_user', sender=Member)
def member_fill_from_user(sender, instance=None, created=None, **kwargs):
    if created:
        instance.first_name = instance.user.first_name
        instance.last_name = instance.user.last_name
        instance.email = instance.user.email
        instance.save(update_fields=['first_name', 'last_name', 'email'])


history.register(MasterUser)
history.register(Member)
history.register(User, follow=['profile'], exclude=['password'])
history.register(UserProfile, follow=['user'])
history.register(Group)
# history.register(Permission)
