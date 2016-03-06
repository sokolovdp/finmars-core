from __future__ import unicode_literals

from django.conf import settings
from django.contrib.auth.models import Group
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from poms.fields import TimezoneField, LanguageField


@python_2_unicode_compatible
class MasterUser(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='master_user', verbose_name=_('user'))
    currency = models.ForeignKey('currencies.Currency', null=True, blank=True)
    language = LanguageField(null=True, blank=True, verbose_name=_('language'))
    timezone = TimezoneField(null=True, blank=True, verbose_name=_('timezone'))

    class Meta:
        verbose_name = _('master user')
        verbose_name_plural = _('master users')

    def __str__(self):
        return '%s' % (self.user.username,)


@python_2_unicode_compatible
class Employee(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='employee', verbose_name=_('user'))
    master_user = models.ForeignKey(MasterUser, verbose_name=_('master user'), related_name='employees')
    language = LanguageField(null=True, blank=True, verbose_name=_('language'))
    timezone = TimezoneField(null=True, blank=True, verbose_name=_('timezone'))

    class Meta:
        verbose_name = _('employee')
        verbose_name_plural = _('employees')

    def __str__(self):
        return '%s (%s)' % (self.user.username, self.master_user.user.username)


@python_2_unicode_compatible
class PrivateGroup(models.Model):
    master_user = models.ForeignKey(MasterUser, verbose_name=_('master user'), related_name='groups')
    group = models.OneToOneField('auth.Group', related_name='owner', verbose_name=_('group'), on_delete=models.PROTECT)
    name = models.CharField(max_length=80, blank=True, default='', verbose_name=_('private name'),
                            help_text=_('user group name'))

    class Meta:
        verbose_name = _('private group')
        verbose_name_plural = _('private groups')
        unique_together = ['master_user', 'name']

    def __str__(self):
        return '%s (%s)' % (self.name, self.master_user.user.username)


# ----------------------------------------------------------------------------------------------------------------------


@python_2_unicode_compatible
class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='profile', verbose_name=_('user'))
    language = LanguageField(null=True, blank=True, verbose_name=_('language'))
    timezone = TimezoneField(null=True, blank=True, verbose_name=_('timezone'))

    class Meta:
        verbose_name = _('user profile')
        verbose_name_plural = _('user profile')

    def __str__(self):
        return '%s' % (self.user.username,)


@python_2_unicode_compatible
class MasterUser2(UserProfile):
    currency = models.ForeignKey('currencies.Currency', null=True, blank=True)

    class Meta:
        verbose_name = _('master user2')
        verbose_name_plural = _('master users2')

    def __str__(self):
        return '%s' % (self.user.username,)


@python_2_unicode_compatible
class Employee2(UserProfile):
    master_user = models.ForeignKey(MasterUser2, verbose_name=_('master user'), related_name='employees')

    class Meta:
        verbose_name = _('employee2')
        verbose_name_plural = _('employees2')

    def __str__(self):
        return '%s (%s)' % (self.user.username, self.master_user.user.username)


@python_2_unicode_compatible
class GroupProfile(models.Model):
    group = models.OneToOneField('auth.Group', related_name='profile', verbose_name=_('group'))
    master_user = models.ForeignKey(MasterUser2, verbose_name=_('master user'), related_name='groups')
    user_name = models.CharField(max_length=80, blank=True, default='', verbose_name=_('private name'),
                                 help_text=_('User specified name'))

    class Meta:
        verbose_name = _('group profile')
        verbose_name_plural = _('group profiles')
        unique_together = ['master_user', 'user_name']

    def __str__(self):
        return '%s (%s)' % (self.user_name, self.master_user.user.username)

    def save(self, *args, **kwargs):
        self.group.name = '%s (%s)' % (self.user_name, self.master_user.user.username)
        self.group.save(update_fields=['name'])
        super(GroupProfile).save(*args, **kwargs)
