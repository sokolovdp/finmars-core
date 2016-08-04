from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel

from poms.audit import history
from poms.common.models import NamedModel
from poms.obj_attrs.models import AbstractAttributeType, AbstractAttribute, AbstractAttributeTypeOption, \
    AbstractClassifier
from poms.obj_perms.models import AbstractGroupObjectPermission, AbstractUserObjectPermission
from poms.users.models import MasterUser, Member


@python_2_unicode_compatible
class Counterparty(NamedModel):
    master_user = models.ForeignKey(MasterUser, related_name='counterparties',
                                    verbose_name=_('master user'))

    # portfolios = models.ManyToManyField(
    #     'portfolios.Portfolio',
    #     related_name='counterparties',
    #     blank=True,
    #     verbose_name=_('portfolios')
    # )

    class Meta(NamedModel.Meta):
        verbose_name = _('counterparty')
        verbose_name_plural = _('counterparties')
        permissions = [
            ('view_counterparty', 'Can view counterparty'),
            ('manage_counterparty', 'Can manage counterparty'),
        ]

    def __str__(self):
        return self.name

    @property
    def is_default(self):
        return self.master_user.counterparty_id == self.id if self.master_user_id else False


class CounterpartyUserObjectPermission(AbstractUserObjectPermission):
    content_object = models.ForeignKey(Counterparty, related_name='user_object_permissions',
                                       verbose_name=_('content object'))

    class Meta(AbstractUserObjectPermission.Meta):
        verbose_name = _('counterparties - user permission')
        verbose_name_plural = _('counterparties - user permissions')


class CounterpartyGroupObjectPermission(AbstractGroupObjectPermission):
    content_object = models.ForeignKey(Counterparty, related_name='group_object_permissions',
                                       verbose_name=_('content object'))

    class Meta(AbstractGroupObjectPermission.Meta):
        verbose_name = _('counterparties - group permission')
        verbose_name_plural = _('counterparties - group permissions')


class CounterpartyAttributeType(AbstractAttributeType):
    # classifier_root = models.OneToOneField(
    #     CounterpartyClassifier,
    #     on_delete=models.PROTECT,
    #     null=True,
    #     blank=True,
    #     verbose_name=_('classifier)')
    # )

    class Meta(AbstractAttributeType.Meta):
        verbose_name = _('counterparty attribute type')
        verbose_name_plural = _('counterparty attribute types')
        permissions = [
            ('view_counterpartyattributetype', 'Can view counterparty attribute type'),
            ('manage_counterpartyattributetype', 'Can manage counterparty attribute type'),
        ]


class CounterpartyAttributeTypeUserObjectPermission(AbstractUserObjectPermission):
    content_object = models.ForeignKey(CounterpartyAttributeType, related_name='user_object_permissions',
                                       verbose_name=_('content object'))

    class Meta(AbstractUserObjectPermission.Meta):
        verbose_name = _('counterparty attribute types - user permission')
        verbose_name_plural = _('counterparty attribute types - user permissions')


class CounterpartyAttributeTypeGroupObjectPermission(AbstractGroupObjectPermission):
    content_object = models.ForeignKey(CounterpartyAttributeType, related_name='group_object_permissions',
                                       verbose_name=_('content object'))

    class Meta(AbstractGroupObjectPermission.Meta):
        verbose_name = _('counterparty attribute types - group permission')
        verbose_name_plural = _('counterparty attribute types - group permissions')


class CounterpartyClassifier(AbstractClassifier):
    attribute_type = models.ForeignKey(
        CounterpartyAttributeType,
        null=True,
        blank=True,
        related_name='classifiers',
        verbose_name=_('attribute type')
    )
    parent = TreeForeignKey(
        'self',
        related_name='children',
        null=True,
        blank=True,
        db_index=True,
        verbose_name=_('parent')
    )

    class Meta(AbstractClassifier.Meta):
        verbose_name = _('counterparty classifier')
        verbose_name_plural = _('counterparty classifiers')


class CounterpartyAttributeTypeOption(AbstractAttributeTypeOption):
    member = models.ForeignKey(Member, related_name='counterparty_attribute_type_options',
                               verbose_name=_('member'))
    attribute_type = models.ForeignKey(CounterpartyAttributeType, related_name='options',
                                       verbose_name=_('attribute type'))

    class Meta(AbstractAttributeTypeOption.Meta):
        verbose_name = _('counterparty attribute types - option')
        verbose_name_plural = _('counterparty attribute types - options')
        unique_together = [
            ['member', 'attribute_type']
        ]


class CounterpartyAttribute(AbstractAttribute):
    attribute_type = models.ForeignKey(CounterpartyAttributeType, related_name='attributes', on_delete=models.PROTECT,
                                       verbose_name=_('attribute type'))
    content_object = models.ForeignKey(Counterparty, related_name='attributes',
                                       verbose_name=_('content object'))
    classifier = models.ForeignKey(CounterpartyClassifier, on_delete=models.PROTECT, null=True, blank=True,
                                   verbose_name=_('classifier'))

    class Meta(AbstractAttribute.Meta):
        verbose_name = _('counterparty attribute')
        verbose_name_plural = _('counterparty attributes')


@python_2_unicode_compatible
class Responsible(NamedModel):
    master_user = models.ForeignKey(MasterUser, related_name='responsibles',
                                    verbose_name=_('master user'))

    class Meta(NamedModel.Meta):
        verbose_name = _('responsible')
        verbose_name_plural = _('responsibles')
        permissions = [
            ('view_responsible', 'Can view responsible'),
            ('manage_responsible', 'Can manage responsible'),
        ]

    def __str__(self):
        return self.name

    @property
    def is_default(self):
        return self.master_user.responsible_id == self.id if self.master_user_id else False


class ResponsibleUserObjectPermission(AbstractUserObjectPermission):
    content_object = models.ForeignKey(Responsible, related_name='user_object_permissions',
                                       verbose_name=_('content object'))

    class Meta(AbstractUserObjectPermission.Meta):
        verbose_name = _('responsibles - user permission')
        verbose_name_plural = _('responsibles - user permissions')


class ResponsibleGroupObjectPermission(AbstractGroupObjectPermission):
    content_object = models.ForeignKey(Responsible, related_name='group_object_permissions',
                                       verbose_name=_('content object'))

    class Meta(AbstractGroupObjectPermission.Meta):
        verbose_name = _('responsibles - group permission')
        verbose_name_plural = _('responsibles - group permissions')


class ResponsibleAttributeType(AbstractAttributeType):
    # classifier_root = models.OneToOneField(
    #     ResponsibleClassifier,
    #     on_delete=models.PROTECT,
    #     null=True,
    #     blank=True,
    #     verbose_name=_('classifier (root)')
    # )

    class Meta(AbstractAttributeType.Meta):
        verbose_name = _('responsible attribute type')
        verbose_name_plural = _('responsible attribute types')
        permissions = [
            ('view_responsibleattributetype', 'Can view responsible attribute type'),
            ('manage_responsibleattributetype', 'Can manage responsible attribute type'),
        ]


class ResponsibleAttributeTypeUserObjectPermission(AbstractUserObjectPermission):
    content_object = models.ForeignKey(ResponsibleAttributeType, related_name='user_object_permissions',
                                       verbose_name=_('content object'))

    class Meta(AbstractUserObjectPermission.Meta):
        verbose_name = _('responsible attribute types - user permission')
        verbose_name_plural = _('responsible attribute types - user permissions')


class ResponsibleAttributeTypeGroupObjectPermission(AbstractGroupObjectPermission):
    content_object = models.ForeignKey(ResponsibleAttributeType, related_name='group_object_permissions',
                                       verbose_name=_('content object'))

    class Meta(AbstractGroupObjectPermission.Meta):
        verbose_name = _('responsible attribute types - group permission')
        verbose_name_plural = _('responsible attribute types - group permissions')


class ResponsibleClassifier(AbstractClassifier):
    attribute_type = models.ForeignKey(
        ResponsibleAttributeType,
        null=True,
        blank=True,
        related_name='classifiers',
        verbose_name=_('attribute type')
    )
    parent = TreeForeignKey(
        'self',
        related_name='children',
        null=True,
        blank=True,
        db_index=True,
        verbose_name=_('parent')
    )

    class Meta(AbstractClassifier.Meta):
        verbose_name = _('responsible classifier')
        verbose_name_plural = _('responsible classifiers')


class ResponsibleAttributeTypeOption(AbstractAttributeTypeOption):
    member = models.ForeignKey(Member, related_name='responsible_attribute_type_options',
                               verbose_name=_('meber'))
    attribute_type = models.ForeignKey(ResponsibleAttributeType, related_name='options',
                                       verbose_name=_('attribute type'))

    class Meta(AbstractAttributeTypeOption.Meta):
        verbose_name = _('responsible attribute types - option')
        verbose_name_plural = _('responsible attribute types - options')
        unique_together = [
            ['member', 'attribute_type']
        ]


class ResponsibleAttribute(AbstractAttribute):
    attribute_type = models.ForeignKey(ResponsibleAttributeType, related_name='attributes', on_delete=models.PROTECT,
                                       verbose_name=_('attribute type'))
    content_object = models.ForeignKey(Responsible, related_name='attributes',
                                       verbose_name=_('content object'))
    classifier = models.ForeignKey(ResponsibleClassifier, on_delete=models.PROTECT, null=True, blank=True,
                                   verbose_name=_('classifier'))

    class Meta(AbstractAttribute.Meta):
        verbose_name = _('responsible attribute')
        verbose_name_plural = _('responsible attributes')


history.register(Counterparty, follow=['attributes', 'tags', 'user_object_permissions', 'group_object_permissions'])
history.register(CounterpartyUserObjectPermission)
history.register(CounterpartyGroupObjectPermission)
history.register(CounterpartyAttributeType,
                 follow=['classifiers', 'options', 'user_object_permissions', 'group_object_permissions'])
history.register(CounterpartyAttributeTypeUserObjectPermission)
history.register(CounterpartyAttributeTypeGroupObjectPermission)
history.register(CounterpartyClassifier)
history.register(CounterpartyAttributeTypeOption)
history.register(CounterpartyAttribute)
history.register(Responsible, follow=['attributes', 'tags', 'user_object_permissions', 'group_object_permissions'])
history.register(ResponsibleUserObjectPermission)
history.register(ResponsibleGroupObjectPermission)
history.register(ResponsibleAttributeType,
                 follow=['classifiers', 'options', 'user_object_permissions', 'group_object_permissions'])
history.register(ResponsibleAttributeTypeUserObjectPermission)
history.register(ResponsibleAttributeTypeGroupObjectPermission)
history.register(ResponsibleClassifier)
history.register(ResponsibleAttributeTypeOption)
history.register(ResponsibleAttribute)
