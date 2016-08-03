from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel

from poms.audit import history
from poms.common.models import NamedModel
from poms.obj_attrs.models import AbstractAttributeType, AbstractAttribute, AbstractAttributeTypeOption
from poms.obj_perms.models import AbstractGroupObjectPermission, AbstractUserObjectPermission
from poms.users.models import MasterUser, Member


@python_2_unicode_compatible
class Portfolio(NamedModel):
    master_user = models.ForeignKey(MasterUser, related_name='portfolios')
    accounts = models.ManyToManyField('accounts.Account', related_name='portfolios', blank=True)
    responsibles = models.ManyToManyField('counterparties.Responsible', related_name='portfolios', blank=True)
    counterparties = models.ManyToManyField('counterparties.Counterparty', related_name='portfolios', blank=True)
    transaction_types = models.ManyToManyField('transactions.TransactionType', related_name='portfolios', blank=True)

    class Meta(NamedModel.Meta):
        verbose_name = _('portfolio')
        verbose_name_plural = _('portfolios')
        permissions = (
            ('view_portfolio', 'Can view portfolio'),
            ('manage_portfolio', 'Can manage portfolio'),
        )

    def __str__(self):
        return self.name

    @property
    def is_default(self):
        return self.master_user.portfolio_id == self.id if self.master_user_id else False


class PortfolioUserObjectPermission(AbstractUserObjectPermission):
    content_object = models.ForeignKey(Portfolio, related_name='user_object_permissions')

    class Meta(AbstractUserObjectPermission.Meta):
        verbose_name = _('portfolios - user permission')
        verbose_name_plural = _('portfolios - user permissions')


class PortfolioGroupObjectPermission(AbstractGroupObjectPermission):
    content_object = models.ForeignKey(Portfolio, related_name='group_object_permissions')

    class Meta(AbstractGroupObjectPermission.Meta):
        verbose_name = _('portfolios - group permission')
        verbose_name_plural = _('portfolios - group permissions')


class PortfolioAttributeType(AbstractAttributeType):
    class Meta(AbstractAttributeType.Meta):
        verbose_name = _('portfolio attribute type')
        verbose_name_plural = _('portfolio attribute types')
        permissions = [
            ('view_portfolioattributetype', 'Can view portfolio attribute type'),
            ('manage_portfolioattributetype', 'Can manage portfolio attribute type'),
        ]


class PortfolioAttributeTypeUserObjectPermission(AbstractUserObjectPermission):
    content_object = models.ForeignKey(PortfolioAttributeType, related_name='user_object_permissions')

    class Meta(AbstractUserObjectPermission.Meta):
        verbose_name = _('portfolio attribute types - user permission')
        verbose_name_plural = _('portfolio attribute types - user permissions')


class PortfolioAttributeTypeGroupObjectPermission(AbstractGroupObjectPermission):
    content_object = models.ForeignKey(PortfolioAttributeType, related_name='group_object_permissions')

    class Meta(AbstractGroupObjectPermission.Meta):
        verbose_name = _('portfolio attribute types - group permission')
        verbose_name_plural = _('portfolio attribute types - group permissions')


class PortfolioClassifier(MPTTModel, NamedModel):
    attribute_type = models.ForeignKey(PortfolioAttributeType, null=True, blank=True, related_name='classifiers')
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True)

    class MPTTMeta:
        order_insertion_by = ['attribute_type', 'name']

    class Meta(NamedModel.Meta):
        verbose_name = _('portfolio classifier')
        verbose_name_plural = _('portfolio classifiers')
        unique_together = [
            ['attribute_type', 'user_code']
        ]


class PortfolioAttributeTypeOption(AbstractAttributeTypeOption):
    member = models.ForeignKey(Member, related_name='portfolio_attribute_type_options')
    attribute_type = models.ForeignKey(PortfolioAttributeType, related_name='options')

    class Meta(AbstractAttributeTypeOption.Meta):
        verbose_name = _('portfolio attribute types - option')
        verbose_name_plural = _('portfolio attribute types - options')


class PortfolioAttribute(AbstractAttribute):
    attribute_type = models.ForeignKey(PortfolioAttributeType, related_name='attributes', on_delete=models.PROTECT)
    content_object = models.ForeignKey(Portfolio, related_name='attributes')
    classifier = models.ForeignKey(PortfolioClassifier, on_delete=models.PROTECT, null=True, blank=True)

    class Meta(AbstractAttribute.Meta):
        verbose_name = _('portfolio attribute')
        verbose_name_plural = _('portfolio attributes')


history.register(Portfolio, follow=['attributes', 'tags', 'user_object_permissions', 'group_object_permissions'])
history.register(PortfolioUserObjectPermission)
history.register(PortfolioGroupObjectPermission)
history.register(PortfolioAttributeType,
                 follow=['classifiers', 'options', 'user_object_permissions', 'group_object_permissions'])
history.register(PortfolioAttributeTypeUserObjectPermission)
history.register(PortfolioAttributeTypeGroupObjectPermission)
history.register(PortfolioClassifier)
history.register(PortfolioAttributeTypeOption)
history.register(PortfolioAttribute)
