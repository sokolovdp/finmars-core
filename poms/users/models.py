from __future__ import unicode_literals

from django.conf import settings
from django.contrib.auth.models import Group, User, Permission
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

    groups = models.ManyToManyField('Group2', blank=True)
    permissions = models.ManyToManyField(Permission, blank=True)

    def __str__(self):
        return '%s@%s' % (self.user.username,self.master_user)


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
class GroupProfile(models.Model):
    group = models.OneToOneField('auth.Group', related_name='profile', verbose_name=_('group'))
    master_user = models.ForeignKey(MasterUser, verbose_name=_('master user'), related_name='groups')
    name = models.CharField(max_length=80, blank=True, default='', verbose_name=_('real name'),
                            help_text=_('user group name'))

    class Meta:
        verbose_name = _('group profile')
        verbose_name_plural = _('group profiles')
        unique_together = [
            ['master_user', 'name']
        ]

    def __str__(self):
        return self.name

    @staticmethod
    def make_group_name(master_user_id, name):
        return '!:%s:%s' % (master_user_id, name)

    @property
    def group_name(self):
        return self.make_group_name(self.master_user_id, self.name)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        super(GroupProfile, self).save(force_insert=force_insert, force_update=force_update, using=using,
                                       update_fields=update_fields)

        self.group.name = self.group_name
        self.group.save(using=using)

    def get_permissions(self):
        return self.group.permissions

    def set_permissions(self, value):
        self.group.permissions = value

    permissions = property(get_permissions, set_permissions)


@python_2_unicode_compatible
class Group2(models.Model):
    master_user = models.ForeignKey(MasterUser, verbose_name=_('master user'), related_name='groups2')
    name = models.CharField(_('name'), max_length=80, unique=True)
    permissions = models.ManyToManyField(Permission, verbose_name=_('permissions'), blank=True)

    class Meta:
        verbose_name = _('group2')
        verbose_name_plural = _('group2')
        unique_together = [
            ['master_user', 'name']
        ]

    def __str__(self):
        return '%s@%s' % (self.name, self.master_user)


class BaseObjectPermission(models.Model):
    permission = models.ForeignKey(Permission)

    class Meta:
        abstract = True


class BaseUserObjectPermission(BaseObjectPermission):
    member = models.ForeignKey(Member)

    class Meta:
        abstract = True


class BaseGroupObjectPermission(BaseObjectPermission):
    group = models.ForeignKey(Group2)

    class Meta:
        abstract = True


history.register(MasterUser)
history.register(Member)
history.register(Permission)
history.register(User, follow=['profile'], exclude=['password'])
history.register(UserProfile)
history.register(Group, follow=['profile', 'permissions'])
history.register(GroupProfile, follow=['group'])
