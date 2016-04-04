from __future__ import unicode_literals

from django.conf import settings
from django.contrib.auth.models import User, Permission
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from poms.audit import history
from poms.fields import TimezoneField, LanguageField

AVAILABLE_APPS = ['accounts', 'counterparties', 'currencies', 'instruments', 'portfolios', 'strategies', 'transactions',
                  'reports', 'users']


@python_2_unicode_compatible
class MasterUser(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    currency = models.ForeignKey('currencies.Currency', null=True, blank=True)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, through='Member', related_name='member_of')

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
    master_user = models.ForeignKey(MasterUser)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    join_date = models.DateTimeField(auto_now_add=True)
    is_owner = models.BooleanField(default=False, verbose_name=_('is owner'))
    is_admin = models.BooleanField(default=False, verbose_name=_('is admin'))

    groups = models.ManyToManyField('Group', blank=True)
    permissions = models.ManyToManyField(Permission, blank=True)

    def __str__(self):
        return '%s@%s' % (self.user.username, self.master_user)


@python_2_unicode_compatible
class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='profile', verbose_name=_('user'))
    language = LanguageField(null=True, blank=True, verbose_name=_('language'))
    timezone = TimezoneField(null=True, blank=True, verbose_name=_('timezone'))

    class Meta:
        verbose_name = _('profile')
        verbose_name_plural = _('profiles')

    def __str__(self):
        return self.user.username


@python_2_unicode_compatible
class Group(models.Model):
    master_user = models.ForeignKey(MasterUser, verbose_name=_('master user'), related_name='groups')
    name = models.CharField(_('name'), max_length=80, unique=True)
    permissions = models.ManyToManyField(Permission, verbose_name=_('permissions'), blank=True, related_name='poms_groups')

    class Meta:
        verbose_name = _('group')
        verbose_name_plural = _('group')
        unique_together = [
            ['master_user', 'name']
        ]

    def __str__(self):
        return self.name


class ObjectPermissionBase(models.Model):
    permission = models.ForeignKey(Permission)

    class Meta:
        abstract = True


@python_2_unicode_compatible
class UserObjectPermissionBase(ObjectPermissionBase):
    member = models.ForeignKey(Member)

    class Meta:
        abstract = True

    def __str__(self):
        return '%s - %s - %s' % (self.content_object, self.member, self.permission)


@python_2_unicode_compatible
class GroupObjectPermissionBase(ObjectPermissionBase):
    group = models.ForeignKey(Group)

    class Meta:
        abstract = True

    def __str__(self):
        return '%s - %s - %s' % (self.content_object, self.group, self.permission)


history.register(MasterUser)
history.register(Member)
history.register(User, follow=['profile'], exclude=['password'])
history.register(UserProfile, follow=['user'])
history.register(Group, follow=['permissions'])
# history.register(GroupProfile, follow=['group'])
history.register(Permission)
