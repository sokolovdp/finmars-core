from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.text import Truncator
from django.utils.translation import ugettext_lazy as _


@python_2_unicode_compatible
class NamedModel(models.Model):
    user_code = models.CharField(
        max_length=25,
        null=True,
        blank=True,
        verbose_name=_('user code')
    )
    name = models.CharField(
        max_length=255,
        verbose_name=_('name')
    )
    public_name = models.CharField(
        max_length=255,
        verbose_name=_('public name'),
        null=True,
        blank=True,
        help_text=_('used if user does not have permissions to view object')
    )
    short_name = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name=_('short name')
    )
    notes = models.TextField(
        null=True,
        blank=True,
        verbose_name=_('notes')
    )

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
            self.short_name = Truncator(self.name).chars(50, truncate='')
        super(NamedModel, self).save(*args, **kwargs)


class TimeStampedModel(models.Model):
    created = models.DateTimeField(
        auto_now_add=True,
        editable=False,
        db_index=True,
        verbose_name=_('created')
    )
    modified = models.DateTimeField(
        auto_now=True,
        editable=False,
        db_index=True,
        verbose_name=_('modified')
    )

    class Meta:
        abstract = True
        get_latest_by = 'modified'
        ordering = ('-modified', '-created',)


class TagModelBase(NamedModel):
    class Meta(NamedModel.Meta):
        abstract = True


@python_2_unicode_compatible
class ClassModelBase(models.Model):
    id = models.PositiveSmallIntegerField(
        primary_key=True,
        verbose_name=_('ID')
    )
    system_code = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        unique=True,
        verbose_name=_('system code')
    )
    name = models.CharField(
        max_length=255,
        verbose_name=_('name')
    )
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name=_('description')
    )

    class Meta:
        abstract = True

    def __str__(self):
        return self.name
