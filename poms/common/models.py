from __future__ import unicode_literals

from django.db import models
from django.utils import translation
from django.utils.encoding import python_2_unicode_compatible
from django.utils.text import Truncator
from django.utils.translation import ugettext_lazy


@python_2_unicode_compatible
class NamedModel(models.Model):
    user_code = models.CharField(max_length=25, null=True, blank=True, verbose_name=ugettext_lazy('user code'))
    name = models.CharField(max_length=255, verbose_name=ugettext_lazy('name'))
    short_name = models.CharField(max_length=50, null=True, blank=True, verbose_name=ugettext_lazy('short name'))
    public_name = models.CharField(max_length=255, verbose_name=ugettext_lazy('public name'), null=True, blank=True,
                                   help_text=ugettext_lazy('used if user does not have permissions to view object'))
    notes = models.TextField(null=True, blank=True, verbose_name=ugettext_lazy('notes'))

    class Meta:
        abstract = True
        unique_together = [
            ['master_user', 'user_code']
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.user_code:
            self.user_code = Truncator(self.name).chars(25, truncate='')
        if not self.short_name:
            self.short_name = Truncator(self.name).chars(50)
        super(NamedModel, self).save(*args, **kwargs)


class TimeStampedModel(models.Model):
    created = models.DateTimeField(auto_now_add=True, editable=False, db_index=True,
                                   verbose_name=ugettext_lazy('created'))
    modified = models.DateTimeField(auto_now=True, editable=False, db_index=True,
                                    verbose_name=ugettext_lazy('modified'))

    class Meta:
        abstract = True
        get_latest_by = 'modified'
        ordering = ('-modified', '-created',)


@python_2_unicode_compatible
class AbstractClassModel(models.Model):
    id = models.PositiveSmallIntegerField(primary_key=True, verbose_name=ugettext_lazy('ID'))
    system_code = models.CharField(max_length=255, unique=True, verbose_name=ugettext_lazy('system code'))
    name_en = models.CharField(max_length=255, blank=True, default='', verbose_name=ugettext_lazy('name (en)'))
    name_ru = models.CharField(max_length=255, blank=True, default='', verbose_name=ugettext_lazy('name (ru)'))
    name_es = models.CharField(max_length=255, blank=True, default='', verbose_name=ugettext_lazy('name (es)'))
    name_de = models.CharField(max_length=255, blank=True, default='', verbose_name=ugettext_lazy('name (de)'))
    description_en = models.TextField(blank=True, default='', verbose_name=ugettext_lazy('description (en)'))
    description_ru = models.TextField(blank=True, default='', verbose_name=ugettext_lazy('description (ru)'))
    description_es = models.TextField(blank=True, default='', verbose_name=ugettext_lazy('description (es)'))
    description_de = models.TextField(blank=True, default='', verbose_name=ugettext_lazy('description (de)'))

    class Meta:
        abstract = True

    def __str__(self):
        return self.name

    @property
    def name(self):
        lang = translation.get_language()
        if lang is None:
            return self.name_en
        n = getattr(self, 'name_%s' % lang, None)
        return n or self.name_en

    @property
    def description(self):
        lang = translation.get_language()
        if lang is None:
            return self.description_en
        n = getattr(self, 'description_%s' % lang, None)
        return n or self.description_en


class FakeDeletableModel(models.Model):
    is_deleted = models.BooleanField(default=False, db_index=True)

    class Meta:
        abstract = True
        index_together = [
            ['master_user', 'is_deleted']
        ]

    def fake_delete(self):
        self.is_deleted = True
        self.save(update_fields=['is_deleted'])
