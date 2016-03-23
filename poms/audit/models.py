from __future__ import unicode_literals

from django.conf import settings
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _


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


# ADDITION = 1
# CHANGE = 2
# DELETION = 3
#
# @python_2_unicode_compatible
# class ModelLogEntry(models.Model):
#     action_time = models.DateTimeField(default=timezone.now, editable=False, verbose_name=_('action time'), )
#     user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.SET_NULL, verbose_name=_('user'),)
#     username = models.CharField(max_length=255, blank=True, null=True,  verbose_name=_('username'),)
#     content_type = models.ForeignKey(ContentType, blank=True, null=True, on_delete=models.SET_NULL, verbose_name=_('content type'))
#     object_id = models.CharField(max_length=255, blank=True, null=True)
#     content_object = GenericForeignKey('content_type', 'object_id')
#     action_flag = models.PositiveSmallIntegerField(_('action flag'))
#     change_message = models.TextField(_('change message'), blank=True)
#     object_repr = models.CharField(_('object repr'), max_length=200)
#     name = models.CharField(max_length=255, verbose_name=_('model attribute'))
#     value = models.TextField(verbose_name=_('model attribute value'))
#
#     class Meta:
#         verbose_name = _('model log entry')
#         verbose_name_plural = _('model log  entries')
#         ordering = ('-action_time',)
#
#     def __str__(self):
#         if self.is_addition():
#             return _('Added "%(object)s".') % {'object': self.object_repr}
#         elif self.is_change():
#             return _('Changed "%(object)s" - %(changes)s') % {
#                 'object': self.object_repr,
#                 'changes': self.change_message,
#             }
#         elif self.is_deletion():
#             return _('Deleted "%(object)s."') % {'object': self.object_repr}
#
#         return _('ModelLog Object')
#
#     def is_addition(self):
#         return self.action_flag == ADDITION
#
#     def is_change(self):
#         return self.action_flag == CHANGE
#
#     def is_deletion(self):
#         return self.action_flag == DELETION
#
#     def get_edited_object(self):
#         "Returns the edited object represented by this log entry"
#         return self.content_type.get_object_for_this_type(pk=self.object_id)
