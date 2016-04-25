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


@python_2_unicode_compatible
class PortfolioClassifier(MPTTModel, NamedModel):
    master_user = models.ForeignKey(MasterUser, related_name='portfolio_classifiers',
                                    verbose_name=_('master user'))
    parent = TreeForeignKey('self', related_name='children', null=True, blank=True, db_index=True,
                            verbose_name=_('parent'))

    class MPTTMeta:
        order_insertion_by = ['master_user', 'name']

    class Meta(NamedModel.Meta):
        verbose_name = _('portfolio classifier')
        verbose_name_plural = _('portfolio classifiers')
        permissions = [
            ('view_portfolioclassifier', 'Can view portfolio classifier')
        ]

    def __str__(self):
        return self.name


class PortfolioClassifierUserObjectPermission(UserObjectPermissionBase):
    content_object = models.ForeignKey(PortfolioClassifier, related_name='user_object_permissions',
                                       verbose_name=_('content object'))

    class Meta(UserObjectPermissionBase.Meta):
        verbose_name = _('portfolio classifiers - user permission')
        verbose_name_plural = _('portfolio classifiers - user permissions')


class PortfolioClassifierGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(PortfolioClassifier, related_name='group_object_permissions',
                                       verbose_name=_('content object'))

    class Meta(GroupObjectPermissionBase.Meta):
        verbose_name = _('portfolio classifiers - group permission')
        verbose_name_plural = _('portfolio classifiers - group permissions')


@python_2_unicode_compatible
class Portfolio(NamedModel):
    master_user = models.ForeignKey(MasterUser, related_name='portfolios',
                                    verbose_name=_('master user'))

    class Meta(NamedModel.Meta):
        verbose_name = _('portfolio')
        verbose_name_plural = _('portfolios')
        permissions = [
            ('view_portfolio', 'Can view portfolio')
        ]

    def __str__(self):
        return self.name


class PortfolioUserObjectPermission(UserObjectPermissionBase):
    content_object = models.ForeignKey(Portfolio, related_name='user_object_permissions',
                                       verbose_name=_('content object'))

    class Meta(UserObjectPermissionBase.Meta):
        verbose_name = _('portfolios - user permission')
        verbose_name_plural = _('portfolios - user permissions')


class PortfolioGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(Portfolio, related_name='group_object_permissions',
                                       verbose_name=_('content object'))

    class Meta(GroupObjectPermissionBase.Meta):
        verbose_name = _('portfolios - group permission')
        verbose_name_plural = _('portfolios - group permissions')


class PortfolioAttributeType(AttributeTypeBase):
    classifier_root = models.ForeignKey(PortfolioClassifier, on_delete=models.PROTECT, null=True, blank=True,
                                        verbose_name=_('classifier (root)'))

    class Meta(AttributeTypeBase.Meta):
        verbose_name = _('portfolio attribute type')
        verbose_name_plural = _('portfolio attribute types')


class PortfolioAttributeTypeOption(AttributeTypeOptionBase):
    member = models.ForeignKey(Member, related_name='portfolio_attribute_type_options',
                               verbose_name=_('member'))
    attribute_type = models.ForeignKey(PortfolioAttributeType, related_name='options',
                                       verbose_name=_('attribute type'))

    class Meta(AttributeTypeOptionBase.Meta):
        verbose_name = _('portfolio attribute types - option')
        verbose_name_plural = _('portfolio attribute types - options')


class PortfolioAttributeTypeUserObjectPermission(UserObjectPermissionBase):
    content_object = models.ForeignKey(PortfolioAttributeType, related_name='user_object_permissions',
                                       verbose_name=_('content object'))

    class Meta(UserObjectPermissionBase.Meta):
        verbose_name = _('portfolio attribute types - user permission')
        verbose_name_plural = _('portfolio attribute types - user permissions')


class PortfolioAttributeTypeGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(PortfolioAttributeType, related_name='group_object_permissions',
                                       verbose_name=_('content object'))

    class Meta(GroupObjectPermissionBase.Meta):
        verbose_name = _('portfolio attribute types - group permission')
        verbose_name_plural = _('portfolio attribute types - group permissions')


class PortfolioAttribute(AttributeBase):
    attribute_type = models.ForeignKey(PortfolioAttributeType, related_name='attributes', on_delete=models.PROTECT,
                                       verbose_name=_('attribute type'))
    content_object = models.ForeignKey(Portfolio, related_name='attributes',
                                       verbose_name=_('content object'))
    classifier = models.ForeignKey(PortfolioClassifier, on_delete=models.PROTECT, null=True, blank=True,
                                   verbose_name=_('classifier'))

    class Meta(AttributeBase.Meta):
        verbose_name = _('portfolio attribute')
        verbose_name_plural = _('portfolio attributes')


history.register(PortfolioClassifier)
history.register(Portfolio)
history.register(PortfolioAttributeType)
history.register(PortfolioAttributeTypeOption)
history.register(PortfolioAttribute)
