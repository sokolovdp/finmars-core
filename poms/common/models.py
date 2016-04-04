from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.text import Truncator
from django.utils.translation import ugettext_lazy as _


@python_2_unicode_compatible
class NamedModel(models.Model):
    user_code = models.CharField(max_length=25, null=True, blank=True, verbose_name=_('user code'))
    name = models.CharField(max_length=255, verbose_name=_('name'))
    short_name = models.CharField(max_length=50, null=True, blank=True, verbose_name=_('short name'))
    notes = models.TextField(null=True, blank=True, verbose_name=_('notes'))

    class Meta:
        abstract = True

    def __str__(self):
        return self.name

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self.user_code:
            self.user_code = Truncator(self.name).chars(25)
        if not self.short_name:
            self.short_name = Truncator(self.name).chars(50)
        super(NamedModel, self).save(force_insert=force_insert, force_update=force_update, using=using,
                                     update_fields=update_fields)


class TimeStampedModel(models.Model):
    created = models.DateTimeField(auto_now_add=True, editable=False, verbose_name=_('created'))
    modified = models.DateTimeField(auto_now=True, editable=False, verbose_name=_('modified'))

    class Meta:
        abstract = True
        get_latest_by = 'modified'
        ordering = ('-modified', '-created',)


class TagModelBase(NamedModel):
    class Meta:
        abstract = True


# class UserTimeStampedModel(TimeStampedModel):
#     created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, verbose_name=_('created by'))
#     modified_by = models.DateTimeField(settings.AUTH_USER_MODEL, null=True, blank=True, verbose_name=_('modified by'))
#
#     class Meta:
#         abstract = True
