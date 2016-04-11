from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from mptt.models import MPTTModel

# from poms.accounts.models import AccountClassifier, Account
from poms.common.models import NamedModel
# from poms.counterparties.models import CounterpartyClassifier, Counterparty, ResponsibleClassifier, Responsible
# from poms.instruments.models import InstrumentClassifier, Instrument
# from poms.obj_perms.utils import register_model
# from poms.portfolios.models import PortfolioClassifier, Portfolio
# from poms.strategies.models import Strategy
# from poms.transactions.models import Transaction
from poms.users.models import MasterUser

#
# class AttrBase(NamedModel):
#     STRING = 10
#     NUMBER = 20
#     CLASSIFIER = 30
#
#     VALUE_TYPES = (
#         (NUMBER, _('Number')),
#         (STRING, _('String')),
#         (CLASSIFIER, _('Classifier')),
#     )
#
#     master_user = models.ForeignKey(MasterUser, verbose_name=_('master user'),
#                                     related_name="%(app_label)s_%(class)s_attrs")
#     order = models.IntegerField(default=0)
#     value_type = models.PositiveSmallIntegerField(default=STRING, choices=VALUE_TYPES)
#
#     class Meta:
#         abstract = True
#         unique_together = [
#             ['master_user', 'user_code']
#         ]
#
#     def __str__(self):
#         return '%s:%s' % (self.short_name, self.get_value_type_display())
#
#
# @python_2_unicode_compatible
# class AttrValueBase(models.Model):
#     value = models.CharField(max_length=255, null=True, blank=True)
#
#     class Meta:
#         abstract = True
#         unique_together = [
#             ['content_object', 'attr']
#         ]
#
#     def __str__(self):
#         return '%s value is %s' % (self.attr, self._get_value())
#
#     def _get_value(self):
#         if self.attr.value_type in [AttrBase.STR, AttrBase.NUM]:
#             return self.value
#         elif self.attr.value_type in [AttrBase.CLASSIFIER]:
#             return self.classifier
#         return None
#
#
# class AccountAttr(AttrBase):
#     classifier = TreeForeignKey(AccountClassifier, null=True, blank=True, related_name='attrs')
#
#     class Meta(AttrBase.Meta):
#         pass
#
#
# class AccountAttrValue(AttrValueBase):
#     content_object = models.ForeignKey(Account, related_name='attr_values')
#     attr = models.ForeignKey(AccountAttr, related_name='values')
#     classifier = TreeForeignKey(AccountClassifier, null=True, blank=True, related_name='attr_values')
#
#     class Meta(AttrValueBase.Meta):
#         pass
#
#
# class CounterpartyAttr(AttrBase):
#     classifier = TreeForeignKey(CounterpartyClassifier, null=True, blank=True, related_name='attrs')
#
#     class Meta(AttrBase.Meta):
#         pass
#
#
# class CounterpartyAttrValue(AttrValueBase):
#     content_object = models.ForeignKey(Counterparty, related_name='attr_values')
#     attr = models.ForeignKey(CounterpartyAttr, related_name='values')
#     classifier = TreeForeignKey(CounterpartyClassifier, null=True, blank=True, related_name='attr_values')
#
#     class Meta(AttrValueBase.Meta):
#         pass
#
#
# class ResponsibleAttr(AttrBase):
#     classifier = TreeForeignKey(ResponsibleClassifier, null=True, blank=True, related_name='attrs')
#
#     class Meta(AttrBase.Meta):
#         pass
#
#
# class ResponsibleAttrValue(AttrValueBase):
#     content_object = models.ForeignKey(Responsible, related_name='attr_values')
#     attr = models.ForeignKey(ResponsibleAttr, related_name='values')
#     classifier = TreeForeignKey(ResponsibleClassifier, null=True, blank=True, related_name='attr_values')
#
#     class Meta(AttrValueBase.Meta):
#         pass
#
#
# class InstrumentAttr(AttrBase):
#     classifier = TreeForeignKey(InstrumentClassifier, null=True, blank=True, related_name='attrs')
#
#     class Meta(AttrBase.Meta):
#         pass
#
#
# class InstrumentAttrValue(AttrValueBase):
#     content_object = models.ForeignKey(Instrument, related_name='attr_values')
#     attr = models.ForeignKey(InstrumentAttr, related_name='values')
#     classifier = TreeForeignKey(InstrumentClassifier, null=True, blank=True, related_name='attr_values')
#
#     class Meta(AttrValueBase.Meta):
#         pass
#
#
# class PortfolioAttr(AttrBase):
#     classifier = TreeForeignKey(PortfolioClassifier, null=True, blank=True, related_name='attrs')
#
#     class Meta(AttrBase.Meta):
#         pass
#
#
# class PortfolioAttrValue(AttrValueBase):
#     content_object = models.ForeignKey(Portfolio, related_name='attr_values')
#     attr = models.ForeignKey(PortfolioAttr, related_name='values')
#     classifier = TreeForeignKey(PortfolioClassifier, null=True, blank=True, related_name='attr_values')
#
#     class Meta(AttrValueBase.Meta):
#         pass
#
#
# class TransactionAttr(AttrBase):
#     strategy_position = TreeForeignKey(Strategy, null=True, blank=True, related_name='position_attrs')
#     strategy_cash = TreeForeignKey(Strategy, null=True, blank=True, related_name='cash_attrs')
#
#     class Meta(AttrBase.Meta):
#         pass
#
#
# class TransactionAttrValue(AttrValueBase):
#     content_object = models.ForeignKey(Transaction, related_name='attr_values')
#     attr = models.ForeignKey(TransactionAttr, related_name='values')
#     strategy_position = TreeForeignKey(Strategy, null=True, blank=True, related_name='position_attr_values')
#     strategy_cash = TreeForeignKey(Strategy, null=True, blank=True, related_name='cash_attr_values')
#
#     class Meta(AttrValueBase.Meta):
#         pass
#
#     def _get_value(self):
#         if self.attr.value_type in [AttrBase.STR, AttrBase.NUM]:
#             return self.value
#         elif self.attr.value_type in [AttrBase.CLASSIFIER]:
#             return self.strategy_position, self.strategy_cash
#         return None


@python_2_unicode_compatible
class AttributeType(NamedModel):
    STRING = 10
    NUMBER = 20
    CLASSIFIER = 30
    # CHOICE = 40
    # CHOICES = 50

    VALUE_TYPES = (
        (NUMBER, _('Number')),
        (STRING, _('String')),
        (CLASSIFIER, _('Classifier')),
        # (CHOICE, _('Choice')),
        # (CHOICES, _('Choices')),
    )

    master_user = models.ForeignKey(MasterUser, related_name='attribute_types')
    content_type = models.ForeignKey(ContentType, related_name='attribute_types')
    value_type = models.PositiveSmallIntegerField(choices=VALUE_TYPES, default=STRING)
    order = models.IntegerField(default=0)

    classifier_content_type = models.ForeignKey(ContentType, null=True, blank=True,
                                                related_name='attribute_type_classifiers')
    classifier_object_id = models.BigIntegerField(null=True, blank=True)
    classifier = GenericForeignKey(ct_field='classifier_content_type', fk_field='classifier_object_id')

    class Meta:
        unique_together = [
            ['master_user', 'content_type', 'name']
        ]
        permissions = [
            ('view_attribute_type', 'Can view attribute_type'),
            ('share_attribute_type', 'Can share attribute_type'),
            ('manage_attribute_type', 'Can manage attribute_type'),
        ]

    def __str__(self):
        return self.name


# register_model(AttributeType)


@python_2_unicode_compatible
class AttributeTypeOrder(models.Model):
    member = models.ForeignKey('users.Member', related_name='attribute_orders')
    attribute_type = models.ForeignKey(AttributeType, related_name='orders')
    order = models.IntegerField(default=0)
    is_hidden = models.BooleanField(default=False)

    class Meta:
        unique_together = [
            ['member', 'attribute_type']
        ]


@python_2_unicode_compatible
class Attribute(models.Model):
    attribute_type = models.ForeignKey(AttributeType, related_name='attributes')

    content_type = models.ForeignKey(ContentType, related_name='attributes')
    object_id = models.BigIntegerField()
    content_object = GenericForeignKey()

    value = models.CharField(max_length=255, blank=True, default='')
    # choices = models.ManyToManyField(AttributeChoice, blank=True)
    # classifiers = TreeManyToManyField(Classifier, blank=True)

    classifier_content_type = models.ForeignKey(ContentType, null=True, blank=True,
                                                related_name='attribute_classifiers')
    classifier_object_id = models.BigIntegerField(null=True, blank=True)
    classifier = GenericForeignKey(ct_field='classifier_content_type', fk_field='classifier_object_id')

    def __str__(self):
        # return '%s[%s] = %s' % (self.content_object, self.attribute, self._get_value())
        return '%s' % self.get_display_value()

    def get_display_value(self):
        t = self.attribute_type.value_type
        if t == AttributeType.NUMBER or t == AttributeType.STRING:
            return self.value
        elif t == AttributeType.CLASSIFIER:
            return self.classifier
        # elif t == Attribute.CHOICE or t == Attribute.CHOICES:
        #     choices = [c.name for c in self.choices.all()]
        #     return ', '.join(choices)
        return None


# ------

class AttributeTypeBase(NamedModel):
    STRING = 10
    NUMBER = 20
    CLASSIFIER = 30
    # CHOICE = 40
    # CHOICES = 50

    VALUE_TYPES = (
        (NUMBER, _('Number')),
        (STRING, _('String')),
        (CLASSIFIER, _('Classifier')),
        # (CHOICE, _('Choice')),
        # (CHOICES, _('Choices')),
    )

    master_user = models.ForeignKey(MasterUser)
    value_type = models.PositiveSmallIntegerField(choices=VALUE_TYPES, default=STRING)
    order = models.IntegerField(default=0)

    class Meta:
        abstract = True
        unique_together = [
            ['master_user', 'name']
        ]


# class AttributeTypeOrderBase(models.Model):
#     member = models.ForeignKey('users.Member', related_name='attribute_orders')
#     attribute_type = models.ForeignKey(AttributeType, related_name='orders')
#     order = models.IntegerField(default=0)
#     is_hidden = models.BooleanField(default=False)
#
#     class Meta:
#         unique_together = [
#             ['member', 'attribute_type']
#         ]

class AttributeBase(models.Model):
    value = models.CharField(max_length=255, blank=True, default='')

    def __str__(self):
        return '%s' % self.get_display_value()

    def get_display_value(self):
        t = self.attribute_type.value_type
        if t == AttributeType.NUMBER or t == AttributeType.STRING:
            return self.value
        elif t == AttributeType.CLASSIFIER:
            return self.classifier
        return None
