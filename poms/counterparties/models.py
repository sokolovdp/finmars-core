from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel

from poms.audit import history
from poms.common.models import NamedModel
from poms.obj_attrs.models import AttributeTypeBase, AttributeBase
from poms.users.models import MasterUser


class CounterpartyClassifier(NamedModel, MPTTModel):
    master_user = models.ForeignKey(MasterUser, related_name='counterparty_classifiers', verbose_name=_('master user'))
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True)

    class MPTTMeta:
        order_insertion_by = ['master_user', 'name']

    class Meta:
        verbose_name = _('counterparty classifier')
        verbose_name_plural = _('counterparty classifiers')
        permissions = [
            ('view_counterpartyclassifier', 'Can view counterparty classifier')
        ]


@python_2_unicode_compatible
class Counterparty(NamedModel):
    master_user = models.ForeignKey(MasterUser, related_name='counterparties', verbose_name=_('master user'))

    class Meta:
        verbose_name = _('counterparty')
        verbose_name_plural = _('counterparties')
        unique_together = [
            ['master_user', 'user_code']
        ]
        permissions = [
            ('view_counterparty', 'Can view counterparty')
        ]

    def __str__(self):
        return self.name


class CounterpartyAttributeType(AttributeTypeBase):
    classifier_root = models.ForeignKey('counterparties.CounterpartyClassifier', null=True, blank=True)


class CounterpartyAttribute(AttributeBase):
    attribute_type = models.ForeignKey(CounterpartyAttributeType, related_name='attributes')
    content_object = models.ForeignKey('counterparties.Counterparty')
    classifier = models.ForeignKey('counterparties.CounterpartyClassifier', null=True, blank=True)


class ResponsibleClassifier(NamedModel, MPTTModel):
    master_user = models.ForeignKey(MasterUser, related_name='responsible_classifiers', verbose_name=_('master user'))
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True)

    class MPTTMeta:
        order_insertion_by = ['master_user', 'name']

    class Meta:
        verbose_name = _('responsible classifier')
        verbose_name_plural = _('responsible classifiers')
        permissions = [
            ('view_responsibleclassifier', 'Can view responsible classifier')
        ]


@python_2_unicode_compatible
class Responsible(NamedModel):
    master_user = models.ForeignKey(MasterUser, related_name='responsibles', verbose_name=_('master user'))

    class Meta:
        verbose_name = _('responsible')
        verbose_name_plural = _('responsibles')
        unique_together = [
            ['master_user', 'user_code']
        ]
        permissions = [
            ('view_responsible', 'Can view responsible')
        ]

    def __str__(self):
        return self.name


class ResponsibleAttributeType(AttributeTypeBase):
    classifier_root = models.ForeignKey('counterparties.ResponsibleClassifier', null=True, blank=True)


class ResponsibleAttribute(AttributeBase):
    attribute_type = models.ForeignKey(ResponsibleAttributeType, related_name='attributes')
    content_object = models.ForeignKey('counterparties.Responsible')
    classifier = models.ForeignKey('counterparties.ResponsibleClassifier', null=True, blank=True)


history.register(CounterpartyClassifier)
history.register(Counterparty)
history.register(ResponsibleClassifier)
history.register(Responsible)
