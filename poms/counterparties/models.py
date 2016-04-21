from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel

from poms.audit import history
from poms.common.models import NamedModel
from poms.obj_attrs.models import AttributeTypeBase, AttributeBase, AttributeTypeOptionBase
from poms.obj_perms.models import UserObjectPermissionBase, GroupObjectPermissionBase
from poms.users.models import MasterUser, Member


class CounterpartyClassifier(MPTTModel, NamedModel):
    master_user = models.ForeignKey(MasterUser, related_name='counterparty_classifiers',
                                    verbose_name=_('master user'))
    parent = TreeForeignKey('self', related_name='children', null=True, blank=True, db_index=True,
                            verbose_name=_('parent'))

    class MPTTMeta:
        order_insertion_by = ['master_user', 'name']

    class Meta:
        verbose_name = _('counterparty classifier')
        verbose_name_plural = _('counterparty classifiers')
        permissions = [
            ('view_counterpartyclassifier', 'Can view counterparty classifier')
        ]


class CounterpartyClassifierUserObjectPermission(UserObjectPermissionBase):
    content_object = models.ForeignKey(CounterpartyClassifier, related_name='user_object_permissions',
                                       verbose_name=_('content object'))

    class Meta:
        verbose_name = _('counterparty classifiers - user permission')
        verbose_name_plural = _('counterparty classifiers - user permissions')


class CounterpartyClassifierGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(CounterpartyClassifier, related_name='group_object_permissions',
                                       verbose_name=_('content object'))

    class Meta:
        verbose_name = _('counterparty classifiers - group permission')
        verbose_name_plural = _('counterparty classifiers - group permissions')


@python_2_unicode_compatible
class Counterparty(NamedModel):
    master_user = models.ForeignKey(MasterUser, related_name='counterparties',
                                    verbose_name=_('master user'))

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


class CounterpartyUserObjectPermission(UserObjectPermissionBase):
    content_object = models.ForeignKey(Counterparty, related_name='user_object_permissions',
                                       verbose_name=_('content object'))

    class Meta:
        verbose_name = _('counterparties - user permission')
        verbose_name_plural = _('counterparties - user permissions')


class CounterpartyGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(Counterparty, related_name='group_object_permissions',
                                       verbose_name=_('content object'))

    class Meta:
        verbose_name = _('counterparties - group permission')
        verbose_name_plural = _('counterparties - group permissions')


class CounterpartyAttributeType(AttributeTypeBase):
    classifier_root = models.ForeignKey(CounterpartyClassifier, on_delete=models.PROTECT, null=True, blank=True,
                                        verbose_name=_('classifier (root)'))

    class Meta:
        verbose_name = _('counterparty attribute type')
        verbose_name_plural = _('counterparty attribute types')


class CounterpartyAttributeTypeUserObjectPermission(UserObjectPermissionBase):
    content_object = models.ForeignKey(CounterpartyAttributeType, related_name='user_object_permissions',
                                       verbose_name=_('content object'))

    class Meta:
        verbose_name = _('counterparty attribute types - user permission')
        verbose_name_plural = _('counterparty attribute types - user permissions')


class CounterpartyAttributeTypeGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(CounterpartyAttributeType, related_name='group_object_permissions',
                                       verbose_name=_('content object'))

    class Meta:
        verbose_name = _('counterparty attribute types - group permission')
        verbose_name_plural = _('counterparty attribute types - group permissions')


class CounterpartyAttributeTypeOption(AttributeTypeOptionBase):
    member = models.ForeignKey(Member, related_name='counterparty_attribute_type_options',
                                       verbose_name=_('member'))
    attribute_type = models.ForeignKey(CounterpartyAttributeType, related_name='attribute_type_options',
                                       verbose_name=_('attribute type'))

    class Meta:
        verbose_name = _('counterparty attribute types - option')
        verbose_name_plural = _('counterparty attribute types - options')
        unique_together = [
            ['member', 'attribute_type']
        ]


class CounterpartyAttribute(AttributeBase):
    attribute_type = models.ForeignKey(CounterpartyAttributeType, related_name='attributes', on_delete=models.PROTECT,
                                       verbose_name=_('attribute type'))
    content_object = models.ForeignKey(Counterparty, related_name='attributes',
                                       verbose_name=_('content object'))
    classifier = models.ForeignKey(CounterpartyClassifier, on_delete=models.PROTECT, null=True, blank=True,
                                   verbose_name=_('classifier'))

    class Meta(AttributeBase.Meta):
        verbose_name = _('counterparty attribute')
        verbose_name_plural = _('counterparty attributes')


class ResponsibleClassifier(MPTTModel, NamedModel):
    master_user = models.ForeignKey(MasterUser, related_name='responsible_classifiers',
                                    verbose_name=_('master user'))
    parent = TreeForeignKey('self', related_name='children', null=True, blank=True, db_index=True,
                            verbose_name=_('parent'))

    class MPTTMeta:
        order_insertion_by = ['master_user', 'name']

    class Meta:
        verbose_name = _('responsible classifier')
        verbose_name_plural = _('responsible classifiers')
        permissions = [
            ('view_responsibleclassifier', 'Can view responsible classifier')
        ]


class ResponsibleClassifierUserObjectPermission(UserObjectPermissionBase):
    content_object = models.ForeignKey(ResponsibleClassifier, related_name='user_object_permissions',
                                       verbose_name=_('content object'))

    class Meta:
        verbose_name = _('responsible classifiers - user permission')
        verbose_name_plural = _('responsible classifiers - user permissions')


class ResponsibleClassifierGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(ResponsibleClassifier, related_name='group_object_permissions',
                                       verbose_name=_('content object'))

    class Meta:
        verbose_name = _('responsible classifiers - group permission')
        verbose_name_plural = _('responsible classifiers - group permissions')


@python_2_unicode_compatible
class Responsible(NamedModel):
    master_user = models.ForeignKey(MasterUser, related_name='responsibles',
                                    verbose_name=_('master user'))

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


class ResponsibleUserObjectPermission(UserObjectPermissionBase):
    content_object = models.ForeignKey(Responsible, related_name='user_object_permissions',
                                       verbose_name=_('content object'))

    class Meta:
        verbose_name = _('responsibles - user permission')
        verbose_name_plural = _('responsibles - user permissions')


class ResponsibleGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(Responsible, related_name='group_object_permissions',
                                       verbose_name=_('content object'))

    class Meta:
        verbose_name = _('responsibles - group permission')
        verbose_name_plural = _('responsibles - group permissions')


class ResponsibleAttributeType(AttributeTypeBase):
    classifier_root = models.ForeignKey(ResponsibleClassifier, on_delete=models.PROTECT, null=True, blank=True,
                                        verbose_name=_('classifier (root)'))

    class Meta:
        verbose_name = _('responsible attribute type')
        verbose_name_plural = _('responsible attribute types')


class ResponsibleAttributeTypeUserObjectPermission(UserObjectPermissionBase):
    content_object = models.ForeignKey(ResponsibleAttributeType, related_name='user_object_permissions',
                                       verbose_name=_('content object'))

    class Meta:
        verbose_name = _('responsible attribute types - user permission')
        verbose_name_plural = _('responsible attribute types - user permissions')


class ResponsibleAttributeTypeGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(ResponsibleAttributeType, related_name='group_object_permissions',
                                       verbose_name=_('content object'))

    class Meta:
        verbose_name = _('responsible attribute types - group permission')
        verbose_name_plural = _('responsible attribute types - group permissions')


class ResponsibleAttributeTypeOption(AttributeTypeOptionBase):
    member = models.ForeignKey(Member, related_name='responsible_attribute_type_options',
                               verbose_name=_('meber'))
    attribute_type = models.ForeignKey(ResponsibleAttributeType, related_name='attribute_type_options',
                                       verbose_name=_('attribute type'))

    class Meta:
        verbose_name = _('responsible attribute types - option')
        verbose_name_plural = _('responsible attribute types - options')
        unique_together = [
            ['member', 'attribute_type']
        ]


class ResponsibleAttribute(AttributeBase):
    attribute_type = models.ForeignKey(ResponsibleAttributeType, related_name='attributes', on_delete=models.PROTECT,
                                       verbose_name=_('attribute type'))
    content_object = models.ForeignKey(Responsible, related_name='attributes',
                                       verbose_name=_('content object'))
    classifier = models.ForeignKey(ResponsibleClassifier, on_delete=models.PROTECT, null=True, blank=True,
                                   verbose_name=_('classifier'))

    class Meta(AttributeBase.Meta):
        verbose_name = _('responsible attribute')
        verbose_name_plural = _('responsible attributes')


history.register(CounterpartyClassifier)
history.register(Counterparty)
history.register(CounterpartyAttributeType)
history.register(CounterpartyAttributeTypeOption)
history.register(CounterpartyAttribute)
history.register(ResponsibleClassifier)
history.register(Responsible)
history.register(ResponsibleAttributeType)
history.register(ResponsibleAttributeTypeOption)
history.register(ResponsibleAttribute)
