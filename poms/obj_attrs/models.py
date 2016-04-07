from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from mptt.fields import TreeForeignKey

from poms.accounts.models import AccountClassifier, Account
from poms.common.models import NamedModel
from poms.counterparties.models import CounterpartyClassifier, Counterparty, ResponsibleClassifier, Responsible
from poms.instruments.models import InstrumentClassifier, Instrument
from poms.portfolios.models import PortfolioClassifier, Portfolio
from poms.strategies.models import Strategy
from poms.transactions.models import Transaction
from poms.users.models import MasterUser


class AttrBase(NamedModel):
    STR = 10
    NUM = 20
    CLASSIFIER = 30

    VALUE_TYPES = (
        (NUM, _('Number')),
        (STR, _('String')),
        (CLASSIFIER, _('Classifier')),
    )

    scheme = models.ForeignKey('Scheme', verbose_name=_('attribute scheme'))
    order = models.IntegerField(default=0)
    value_type = models.PositiveSmallIntegerField(default=STR, choices=VALUE_TYPES)

    class Meta:
        abstract = True
        unique_together = [
            ['scheme', 'user_code']
        ]

    def __str__(self):
        return '%s[%s:%s]' % (self.scheme, self.short_name, self.get_value_type_display())


@python_2_unicode_compatible
class AttrValueBase(models.Model):
    value = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        abstract = True
        unique_together = [
            ['content_object', 'attr']
        ]

    def __str__(self):
        return '%s value is %s' % (self.attr, self._get_value())

    def _get_value(self):
        if self.attr.value_type in [AttrBase.STR, AttrBase.NUM]:
            return self.value
        elif self.attr.value_type in [AttrBase.CLASSIFIER]:
            return self.classifier
        return None


class Scheme(NamedModel):
    master_user = models.ForeignKey(MasterUser, verbose_name=_('master user'), related_name='schemes')

    class Meta:
        verbose_name = _('attribute scheme')
        verbose_name_plural = _('attribute schemes')
        unique_together = [
            ['master_user', 'user_code']
        ]


class AccountAttr(AttrBase):
    classifier = TreeForeignKey(AccountClassifier, null=True, blank=True, related_name='attrs')

    class Meta(AttrBase.Meta):
        pass


class AccountAttrValue(AttrValueBase):
    content_object = models.ForeignKey(Account, related_name='attr_values')
    attr = models.ForeignKey(AccountAttr, related_name='values')
    classifier = TreeForeignKey(AccountClassifier, null=True, blank=True, related_name='attr_values')

    class Meta(AttrValueBase.Meta):
        pass


class CounterpartyAttr(AttrBase):
    classifier = TreeForeignKey(CounterpartyClassifier, null=True, blank=True, related_name='attrs')

    class Meta(AttrBase.Meta):
        pass


class CounterpartyAttrValue(AttrValueBase):
    content_object = models.ForeignKey(Counterparty, related_name='attr_values')
    attr = models.ForeignKey(CounterpartyAttr, related_name='values')
    classifier = TreeForeignKey(CounterpartyClassifier, null=True, blank=True, related_name='attr_values')

    class Meta(AttrValueBase.Meta):
        pass


class ResponsibleAttr(AttrBase):
    classifier = TreeForeignKey(ResponsibleClassifier, null=True, blank=True, related_name='attrs')

    class Meta(AttrBase.Meta):
        pass


class ResponsibleAttrValue(AttrValueBase):
    content_object = models.ForeignKey(Responsible, related_name='attr_values')
    attr = models.ForeignKey(ResponsibleAttr, related_name='values')
    classifier = TreeForeignKey(ResponsibleClassifier, null=True, blank=True, related_name='attr_values')

    class Meta(AttrValueBase.Meta):
        pass


class InstrumentAttr(AttrBase):
    classifier = TreeForeignKey(InstrumentClassifier, null=True, blank=True, related_name='attrs')

    class Meta(AttrBase.Meta):
        pass


class InstrumentAttrValue(AttrValueBase):
    content_object = models.ForeignKey(Instrument, related_name='attr_values')
    attr = models.ForeignKey(InstrumentAttr, related_name='values')
    classifier = TreeForeignKey(InstrumentClassifier, null=True, blank=True, related_name='attr_values')

    class Meta(AttrValueBase.Meta):
        pass


class PortfolioAttr(AttrBase):
    classifier = TreeForeignKey(PortfolioClassifier, null=True, blank=True, related_name='attrs')

    class Meta(AttrBase.Meta):
        pass


class PortfolioAttrValue(AttrValueBase):
    content_object = models.ForeignKey(Portfolio, related_name='attr_values')
    attr = models.ForeignKey(PortfolioAttr, related_name='values')
    classifier = TreeForeignKey(PortfolioClassifier, null=True, blank=True, related_name='attr_values')

    class Meta(AttrValueBase.Meta):
        pass


class TransactionAttr(AttrBase):
    strategy_position = TreeForeignKey(Strategy, null=True, blank=True, related_name='position_attrs')
    strategy_cash = TreeForeignKey(Strategy, null=True, blank=True, related_name='cash_attrs')

    class Meta(AttrBase.Meta):
        pass


class TransactionAttrValue(AttrValueBase):
    content_object = models.ForeignKey(Transaction, related_name='attr_values')
    attr = models.ForeignKey(TransactionAttr, related_name='values')
    strategy_position = TreeForeignKey(Strategy, null=True, blank=True, related_name='position_attr_values')
    strategy_cash = TreeForeignKey(Strategy, null=True, blank=True, related_name='cash_attr_values')

    class Meta(AttrValueBase.Meta):
        pass

    def _get_value(self):
        if self.attr.value_type in [AttrBase.STR, AttrBase.NUM]:
            return self.value
        elif self.attr.value_type in [AttrBase.CLASSIFIER]:
            return self.strategy_position, self.strategy_cash
        return None
