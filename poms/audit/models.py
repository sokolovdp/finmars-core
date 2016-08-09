from __future__ import unicode_literals

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _


@python_2_unicode_compatible
class AuthLogEntry(models.Model):
    date = models.DateTimeField(auto_now_add=True, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('user'))
    user_ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, null=True, blank=True)
    is_success = models.BooleanField(default=False, db_index=True)

    class Meta:
        verbose_name = _('authenticate log')
        verbose_name_plural = _('authenticate logs')

    def __str__(self):
        if self.is_success:
            msg = 'User %s logged in from %s at %s using "%s"'
        else:
            msg = 'User %s login failed from %s at %s using "%s"'
        return msg % (self.user, self.user_ip, self.date, self.user_agent)


@python_2_unicode_compatible
class ObjectHistory4Entry(models.Model):
    ADDITION = 1
    DELETION = 2
    CHANGE = 3
    M2M_ADDITION = 4
    M2M_DELETION = 5
    FLAG_CHOICES = (
        (ADDITION, 'added'),
        (DELETION, 'deleted'),
        (CHANGE, 'changed'),
        (M2M_ADDITION, 'm2m added'),
        (M2M_DELETION, 'm2m deleted'),
    )

    # actor = models.ForeignKey(ObjectHistory4Actor)
    master_user = models.ForeignKey('users.MasterUser', related_name='object_histories')
    member = models.ForeignKey('users.Member', related_name='object_histories', null=True, blank=True,
                               on_delete=models.SET_NULL)

    group_id = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True, db_index=True)

    actor_content_type = models.ForeignKey(ContentType, related_name='+', blank=True, null=True)
    actor_object_id = models.BigIntegerField(blank=True, null=True)
    actor_content_object = GenericForeignKey(ct_field='actor_content_type', fk_field='actor_object_id')
    actor_object_repr = models.TextField(blank=True)

    action_flag = models.PositiveSmallIntegerField(choices=FLAG_CHOICES)

    content_type = models.ForeignKey(ContentType, related_name='+', blank=True, null=True)
    object_id = models.BigIntegerField(blank=True, null=True)
    content_object = GenericForeignKey()
    object_repr = models.TextField(blank=True)

    field_name = models.CharField(max_length=50, null=True, blank=True)

    value = models.TextField(blank=True)
    value_content_type = models.ForeignKey(ContentType, related_name='+', blank=True, null=True)
    value_object_id = models.BigIntegerField(blank=True, null=True)
    value_content_object = GenericForeignKey(ct_field='value_content_type', fk_field='value_object_id')

    old_value = models.TextField(blank=True)
    old_value_content_type = models.ForeignKey(ContentType, related_name='+', blank=True, null=True)
    old_value_object_id = models.BigIntegerField(blank=True, null=True)
    old_value_content_object = GenericForeignKey(ct_field='old_value_content_type', fk_field='old_value_object_id')

    class Meta:
        verbose_name = _('object history (v4)')
        verbose_name_plural = _('object histories (v4)')
        ordering = ['-created']
        index_together = [
            ['master_user', 'created'],
            # ['master_user', 'group_id'],
            # ['master_user', 'actor_object_repr'],
            # ['master_user', 'actor_content_type', 'actor_object_id'],
            #
            # ['master_user', 'object_repr'],
            # ['master_user', 'content_type', 'object_id'],
            #
            # ['master_user', 'value'],
            # ['master_user', 'value_content_type', 'value_object_id'],
            #
            # ['master_user', 'old_value'],
            # ['master_user', 'old_value_content_type', 'old_value_object_id'],
        ]

    def __str__(self):
        if self.action_flag == self.CHANGE:
            return '%s, %s, %s' % (self.get_action_flag_display(), self.object_repr, self.field_name)
        else:
            return '%s, %s' % (self.get_action_flag_display(), self.object_repr)

    @property
    def is_root_object(self):
        return self.actor_content_type_id == self.content_type_id and self.actor_object_id == self.object_id

    @property
    def actor_content_type_repr(self):
        return self.actor_content_type.model_class()._meta.verbose_name

    @property
    def content_type_repr(self):
        return self.content_type.model_class()._meta.verbose_name

    @property
    def field_name_repr(self):
        if self.field_name:
            model = self.content_type.model_class()
            try:
                f = model._meta.get_field(self.field_name)
                return f.verbose_name
            except (FieldDoesNotExist, AttributeError):
                pass
        return self.field_name

    @property
    def value_content_type_repr(self):
        if self.value_content_type_id:
            return self.value_content_type.model_class()._meta.verbose_name
        return None

    @property
    def value_repr(self):
        # if self.value_content_type_id:
        #     return self.value
        # try:
        #     return json.loads(self.value)
        # except:
        #     return self.value
        return self.value

    @property
    def old_value_content_type_repr(self):
        if self.old_value_content_type_id:
            return self.old_value_content_type.model_class()._meta.verbose_name
        return None

    @property
    def old_value_repr(self):
        # if self.old_value_content_type_id:
        #     return self.old_value
        # try:
        #     return json.loads(self.old_value)
        # except:
        #     return self.old_value
        return self.old_value

    @property
    def message(self):
        data = {
            'actor_object_name': self.actor_content_type_repr,
            'actor_object_repr': self.actor_object_repr,
            'object_name': self.content_type_repr,
            'object_repr': self.object_repr,
            'field_name': self.field_name_repr,
            'value_object_name': self.value_content_type_repr,
            'value': self.value_repr,
            'old_value_object_name': self.old_value_content_type_repr,
            'old_value': self.old_value_repr,
        }
        if self.action_flag == self.ADDITION:
            if self.is_root_object:
                return _('Added "%(object_name)s" "%(object_repr)s".') % data
            else:
                return _(
                    'Added "%(object_name)s" "%(object_repr)s" inside "%(actor_object_name)s" "%(actor_object_repr)s".') % data
        elif self.action_flag == self.DELETION:
            if self.is_root_object:
                return _('Deleted "%(object_name)s" "%(object_repr)s".') % data
            else:
                return _(
                    'Deleted "%(object_name)s" "%(object_repr)s" inside "%(actor_object_name)s" "%(actor_object_repr)s".') % data
        elif self.action_flag == self.CHANGE:
            if self.is_root_object:
                return _(
                    'Changed "%(field_name)s" in "%(object_name)s" "%(object_repr)s" from "%(old_value)s" to "%(value)s".') % data
            else:
                return _(
                    'Changed "%(field_name)s" in "%(object_name)s" "%(object_repr)s" from "%(old_value)s" to "%(value)s" inside "%(actor_object_name)s" "%(actor_object_repr)s".') % data
        elif self.action_flag == self.M2M_ADDITION:
            if self.is_root_object:
                return _(
                    'Added "%(value_object_name)s" "%(value)s" into "%(field_name)s" in "%(object_name)s" "%(object_repr)s".') % data
            else:
                return _(
                    'Added "%(value_object_name)s" "%(value)s" into "%(field_name)s" in "%(object_name)s" "%(object_repr)s" inside "%(actor_object_name)s" "%(actor_object_repr)s".') % data
        elif self.action_flag == self.M2M_DELETION:
            if self.is_root_object:
                return _(
                    'Deleted "%(value_object_name)s" "%(value)s" from "%(field_name)s" in "%(object_name)s" "%(object_repr)s".') % data
            else:
                return _(
                    '"Deleted %(value_object_name)s" "%(value)s" from "%(field_name)s" in "%(object_name)s" "%(object_repr)s" inside "%(actor_object_name)s" "%(actor_object_repr)s".') % data
        return None
