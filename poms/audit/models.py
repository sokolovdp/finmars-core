from __future__ import unicode_literals

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from reversion.models import Revision


@python_2_unicode_compatible
class AuthLogEntry(models.Model):
    date = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_('create date'))
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('user'))
    user_ip = models.GenericIPAddressField(null=True, blank=True, verbose_name=_('user ip'))
    user_agent = models.CharField(max_length=255, null=True, blank=True, verbose_name=_('user agent'))
    is_success = models.BooleanField(default=False, db_index=True, verbose_name=_('is_success'))

    class Meta:
        verbose_name = _('authenticate log')
        verbose_name_plural = _('authenticate logs')

    def __str__(self):
        if self.is_success:
            msg = 'User %s logged in from %s at %s using "%s"'
        else:
            msg = 'User %s login failed from %s at %s using "%s"'
        return msg % (self.user, self.user_ip, self.date, self.user_agent)


# @python_2_unicode_compatible
# class ModelLogEntry(models.Model):
#     ADDITION = 1
#     CHANGE = 2
#     DELETION = 3
#     ACTIONS = (
#         (ADDITION, _('Add')),
#         (CHANGE, _('Change')),
#         (DELETION, _('Delete')),
#     )
#
#     action_time = models.DateTimeField(auto_now_add=True, verbose_name=_('action time'), )
#
#     master_user = models.ForeignKey('users.MasterUser')
#     user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.SET_NULL,
#                              verbose_name=_('user'), )
#     username = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('username'), )
#
#     action_flag = models.PositiveSmallIntegerField(choices=ACTIONS, verbose_name=_('action flag'))
#
#     content_type = models.ForeignKey(ContentType, blank=True, null=True, on_delete=models.SET_NULL,
#                                      verbose_name=_('content type'))
#     object_id = models.CharField(max_length=255, blank=True, null=True)
#     content_object = GenericForeignKey('content_type', 'object_id')
#
#     object_repr = models.CharField(_('object repr'), max_length=200)
#     change_message = models.TextField(_('change message'), blank=True)
#
#     class Meta:
#         verbose_name = _('model log entry')
#         verbose_name_plural = _('model log  entries')
#         ordering = ('-action_time',)
#
#     def __str__(self):
#         return self.object_repr
#
#
# class ModelLogEntryField(models.Model):
#     entry = models.ForeignKey(ModelLogEntry)
#     field = models.CharField(max_length=255)
#     value = models.TextField()


class VersionInfo(models.Model):
    # There must be a relationship with Revision called `revision`.
    revision = models.ForeignKey(Revision, related_name='info')
    master_user = models.ForeignKey('users.MasterUser')
    username = models.CharField(max_length=255, null=True, blank=True)


class ModelProxy(object):
    def __init__(self, version):
        self._version = version
        self._object = version.object_version.object
        self._m2m_data = version.object_version.m2m_data
        self._cache = {}

    def __getattr__(self, item):
        obj = self._object
        try:
            f = obj._meta.get_field(item)
        except FieldDoesNotExist:
            f = None
        # print('-' * 10)
        # print(item, ':', f)
        if f:
            # print('one_to_one: ', f.one_to_one)
            # print('many_to_many: ', f.many_to_many)
            # print('related_model: ', f.related_model)

            if item in self._cache:
                return self._cache[item]
            if f.one_to_one:
                ct = ContentType.objects.get_for_model(f.related_model)
                related_obj = self._version.revision.version_set.filter(content_type=ct).first()
                if related_obj:
                    val = related_obj.object_version.object
                    self._cache[item] = val
                    return val
                self._cache[item] = None
                return None
            elif f.many_to_many:
                m2m_d = self._m2m_data
                if m2m_d and item in m2m_d:
                    val = list(f.related_model.objects.filter(id__in=m2m_d[item]))
                    self._cache[item] = val
                    return val
                self._cache[item] = None
                return None
        val = getattr(obj, item)
        return val

    def save(self, *args, **kwargs):
        raise NotImplementedError()

    def delete(self, *args, **kwargs):
        raise NotImplementedError()
