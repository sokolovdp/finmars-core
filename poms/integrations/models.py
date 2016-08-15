from __future__ import unicode_literals, print_function

import json
import uuid
from datetime import date, datetime
from logging import getLogger

import six
from dateutil import parser
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from poms.common import formula
from poms.common.models import TimeStampedModel, AbstractClassModel
from poms.instruments.models import Instrument, InstrumentAttribute
from poms.integrations.storage import import_config_storage
from poms.obj_attrs.models import AbstractAttributeType

_l = getLogger('poms.integrations')


class ProviderClass(AbstractClassModel):
    BLOOMBERG = 1
    CLASSES = (
        (BLOOMBERG, _("Bloomberg")),
    )

    class Meta(AbstractClassModel.Meta):
        pass


class FactorScheduleMethod(AbstractClassModel):
    IGNORE = 1
    DEFAULT_BLOOMBERG = 100
    CLASSES = (
        (IGNORE, _("Ignore")),
        (DEFAULT_BLOOMBERG, _("Default bloomberg method")),
    )

    MAP = {
        ProviderClass.BLOOMBERG: [IGNORE, DEFAULT_BLOOMBERG, ]
    }

    class Meta(AbstractClassModel.Meta):
        pass


class AccrualCalculationScheduleMethod(AbstractClassModel):
    IGNORE = 1
    DEFAULT_BLOOMBERG = 100
    CLASSES = (
        (IGNORE, _("Ignore")),
        (DEFAULT_BLOOMBERG, _("Default bloomberg method")),
    )

    MAP = {
        ProviderClass.BLOOMBERG: [IGNORE, DEFAULT_BLOOMBERG, ]
    }

    class Meta(AbstractClassModel.Meta):
        pass


@python_2_unicode_compatible
class InstrumentMapping(models.Model):
    BASIC_FIELDS = ['isin', 'user_code', 'name', 'short_name', 'public_name', 'notes', 'instrument_type',
                    'pricing_currency', 'price_multiplier', 'accrued_currency', 'accrued_multiplier',
                    'user_text_1', 'user_text_2', 'user_text_3',
                    # 'daily_pricing_model',
                    # 'payment_size_detail',
                    # 'default_price',
                    # 'default_accrued',
                    # 'price_download_mode',
                    ]

    master_user = models.ForeignKey('users.MasterUser')
    mapping_name = models.CharField(max_length=255)
    provider = models.ForeignKey(ProviderClass)

    isin = models.CharField(max_length=255, blank=True, default='')
    user_code = models.CharField(max_length=255, blank=True, default='')
    name = models.CharField(max_length=255)
    short_name = models.CharField(max_length=255, blank=True, default='')
    public_name = models.CharField(max_length=255, blank=True, default='')
    notes = models.CharField(max_length=255, blank=True, default='')
    instrument_type = models.CharField(max_length=255, blank=True, default='')
    pricing_currency = models.CharField(max_length=255, blank=True, default='')
    price_multiplier = models.CharField(max_length=255, blank=True, default='1.0')
    accrued_currency = models.CharField(max_length=255, blank=True, default='')
    accrued_multiplier = models.CharField(max_length=255, blank=True, default='1.0')
    # daily_pricing_model = models.CharField(max_length=255, blank=True, default='')
    # payment_size_detail = models.CharField(max_length=255, blank=True, default='')
    # default_price = models.CharField(max_length=255, blank=True, default='0.0')
    # default_accrued = models.CharField(max_length=255, blank=True, default='0.0')
    user_text_1 = models.CharField(max_length=255, blank=True, default='')
    user_text_2 = models.CharField(max_length=255, blank=True, default='')
    user_text_3 = models.CharField(max_length=255, blank=True, default='')

    # price_download_mode = models.CharField(max_length=255, blank=True, default='')

    factor_schedule_method = models.ForeignKey(FactorScheduleMethod, null=True, blank=True)
    accrual_calculation_schedule_method = models.ForeignKey(AccrualCalculationScheduleMethod, null=True, blank=True)

    class Meta:
        index_together = (
            ('master_user', 'mapping_name')
        )
        verbose_name = _('instrument mapping')
        verbose_name_plural = _('instrument mappings')
        permissions = [
            ('view_instrumentmapping', 'Can view instrument mapping'),
            ('manage_instrumentmapping', 'Can manage instrument mapping'),
        ]

    def __str__(self):
        return self.mapping_name

    def create_instrument(self, values, save=True):
        instr = Instrument(master_user=self.master_user)

        instr.instrument_type = self.master_user.instrument_type
        instr.pricing_currency = self.master_user.currency
        instr.accrued_currency = self.master_user.currency

        def get_date(v):
            if v is not None:
                if isinstance(v, date):
                    return v
                elif isinstance(v, datetime):
                    return v.date()
                else:
                    v = parser.parse(v)
                    if v:
                        return v.date()
            return None

        for attr in self.BASIC_FIELDS:
            expr = getattr(self, attr)
            if expr:
                try:
                    v = formula.safe_eval(expr, names=values)
                except formula.InvalidExpression:
                    _l.debug('Invalid expression "%s"', attr, exc_info=True)
                    v = None
                if attr in ['pricing_currency', 'accrued_currency']:
                    if v is not None:
                        v = self.master_user.currencies.get(user_code=v)
                        setattr(instr, attr, v)
                elif attr in ['instrument_type']:
                    if v is not None:
                        v = self.master_user.instrument_types.get(user_code=v)
                        setattr(instr, attr, v)
                elif attr in ['price_multiplier', 'accrued_multiplier', 'default_price', 'default_accrued']:
                    if v is not None:
                        v = float(v)
                        setattr(instr, attr, v)
                else:
                    if v is not None:
                        v = six.text_type(v)
                        setattr(instr, attr, v)

        if save:
            instr.save()

        iattrs = []
        for attr in self.attributes.select_related('attribute_type').all():
            tattr = attr.attribute_type

            iattr = InstrumentAttribute(content_object=instr, attribute_type=tattr)
            iattrs.append(iattr)

            if attr.value:
                try:
                    v = formula.safe_eval(attr.value, names=values)
                except formula.InvalidExpression as e:
                    _l.debug('Invalid expression "%s"', attr.value, exc_info=True)
                    v = None
                if tattr.value_type == AbstractAttributeType.STRING:
                    if v is not None:
                        iattr.value_string = six.text_type(v)
                elif tattr.value_type == AbstractAttributeType.NUMBER:
                    if v is not None:
                        iattr.value_float = float(v)
                elif tattr.value_type == AbstractAttributeType.DATE:
                    if v is not None:
                        iattr.value_date = get_date(v)
                elif tattr.value_type == AbstractAttributeType.CLASSIFIER:
                    if v is not None:
                        v = six.text_type(v)
                        v = tattr.classifiers.filter(name=v).first()
                        iattr.classifier = v

            if save:
                iattr.save()

        instr.attributes_preview = iattrs
        # if not preview:
        #     instr.attributes = iattrs

        return instr


class InstrumentMappingInput(models.Model):
    mapping = models.ForeignKey(InstrumentMapping, related_name='inputs')
    name = models.CharField(max_length=32, blank=True, default='')
    field = models.CharField(max_length=32, blank=True, default='')

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class InstrumentMappingAttribute(models.Model):
    mapping = models.ForeignKey(InstrumentMapping, related_name='attributes')
    attribute_type = models.ForeignKey('instruments.InstrumentAttributeType', null=True, blank=True)
    value = models.CharField(max_length=255, blank=True, default='')

    class Meta:
        unique_together = (
            ('mapping', 'attribute_type')
        )
        ordering = ('attribute_type__name',)

    def __str__(self):
        # return '%s -> %s' % (self.name, self.attribute_type)
        return '%s' % (self.attribute_type,)


class PricingFieldMapping(models.Model):
    master_user = models.ForeignKey('users.MasterUser')
    provider = models.ForeignKey(ProviderClass)
    pricing_model = models.ForeignKey('instruments.DailyPricingModel')

    bid_multiplier = models.FloatField(default=1.0)
    bid0 = models.CharField(max_length=50, blank=True)
    bid1 = models.CharField(max_length=50, blank=True)
    bid2 = models.CharField(max_length=50, blank=True)
    bid_history = models.CharField(max_length=50, blank=True)

    ask_multiplier = models.FloatField(default=1.0)
    ask0 = models.CharField(max_length=50, blank=True)
    ask1 = models.CharField(max_length=50, blank=True)
    ask2 = models.CharField(max_length=50, blank=True)
    ask_history = models.CharField(max_length=50, blank=True)

    last = models.CharField(max_length=50, blank=True)
    mid = models.CharField(max_length=50, blank=True)

    class Meta:
        unique_together = [
            ['master_user', 'provider']
        ]

    def __str__(self):
        return '%s - %s' % (self.pricing_model, self.provider)

    def _get_fields(self, *args):
        ret = set()
        for attr_name in args:
            field_name = getattr(self, attr_name)
            if field_name:
                ret.add(field_name)
        return sorted(ret)

    def _get_value(self, values, *args):
        for attr_name in args:
            field_name = getattr(self, attr_name)
            if field_name and field_name in values:
                return values[field_name]
        return 0.0

    @property
    def fields(self):
        return self._get_fields('bid0', 'bid1', 'bid2',
                                'ask0', 'ask1', 'ask2',
                                'last', 'mid')

    @property
    def history_fields(self):
        return self._get_fields('bid_history', 'ask_history')

    def get_bid(self, values):
        value = self._get_value(values, 'bid0', 'bid1', 'bid2')
        return value * self.bid_multiplier

    def get_bid_history(self, values):
        value = self._get_value(values, 'bid_history')
        return value * self.bid_multiplier

    def get_ask(self, values):
        value = self._get_value(values, 'ask0', 'ask1', 'ask2')
        return value * self.ask_multiplier

    def get_ask_history(self, values):
        value = self._get_value(values, 'ask_history')
        return value * self.ask_multiplier


class CurrencyMapping(models.Model):
    provider = models.ForeignKey(ProviderClass)
    value = models.CharField(max_length=255)
    currency = models.ForeignKey('currencies.Currency')

    class Meta:
        pass

    def __str__(self):
        return '%s / %s -> %s' % (self.provider, self.value, self.currency)


class InstrumentTypeMapping(models.Model):
    provider = models.ForeignKey(ProviderClass)
    value = models.CharField(max_length=255)
    instrument_type = models.ForeignKey('instruments.InstrumentType')

    class Meta:
        pass

    def __str__(self):
        return '%s / %s -> %s' % (self.provider, self.value, self.instrument_type)


class InstrumentAttributeValueMapping(models.Model):
    provider = models.ForeignKey(ProviderClass)
    value = models.CharField(max_length=255)

    attribute_type = models.ForeignKey('instruments.InstrumentAttributeType', on_delete=models.PROTECT,
                                       verbose_name=_('attribute type'))
    value_string = models.CharField(max_length=255, null=True, blank=True, verbose_name=_('value (String)'))
    value_float = models.FloatField(null=True, blank=True, verbose_name=_('value (Float)'))
    value_date = models.DateField(null=True, blank=True, verbose_name=_('value (Date)'))
    classifier = models.ForeignKey('instruments.InstrumentClassifier', on_delete=models.PROTECT, null=True, blank=True,
                                   verbose_name=_('classifier'))

    class Meta:
        pass

    def __str__(self):
        value = self.attribute_type.get_value(self)
        return '%s / %s -> %s / %s' % (self.provider, self.value, self.attribute_type, value)


def import_cert_upload_to(instance, filename):
    # return '%s/%s' % (instance.master_user_id, filename)
    return '/'.join([instance.master_user_id, instance.provider_id, uuid.uuid4().hex])


class ImportConfig(models.Model):
    master_user = models.OneToOneField('users.MasterUser', related_name='bloomberg_config')
    provider = models.ForeignKey(ProviderClass)
    p12cert = models.FileField(null=True, blank=True, upload_to=import_cert_upload_to, storage=import_config_storage)
    password = models.CharField(max_length=64, null=True, blank=True)
    cert = models.FileField(null=True, blank=True, upload_to=import_cert_upload_to, storage=import_config_storage)
    key = models.FileField(null=True, blank=True, upload_to=import_cert_upload_to, storage=import_config_storage)

    class Meta:
        verbose_name = _('import config')
        verbose_name_plural = _('import configs')
        unique_together = [
            ['master_user', 'provider']
        ]

    def __str__(self):
        return '%s' % self.master_user

    # def delete(self, using=None, keep_parents=False):
    #     if self.p12cert:
    #         self.p12cert.delete(save=False)
    #     if self.cert:
    #         self.cert.delete(save=False)
    #     if self.key:
    #         self.key.delete(save=False)
    #     super(BloombergConfig, self).delete(using=using, keep_parents=keep_parents)

    @property
    def pair(self):
        if self.cert and self.key:
            return self.cert, self.key
        elif self.p12cert:
            from poms.integrations.providers.bloomberg import get_certs
            return get_certs(self.p12cert.read(), self.password, is_base64=False)
        return None, None

    @property
    def has_p12cert(self):
        return bool(self.p12cert)

    @property
    def has_password(self):
        return bool(self.password)

    @property
    def has_cert(self):
        return bool(self.cert)

    @property
    def has_key(self):
        return bool(self.key)

    @property
    def is_ready(self):
        return (self.has_p12cert and self.has_password) or (self.has_cert and self.has_key)


@python_2_unicode_compatible
class Task(TimeStampedModel):
    ACTION_INSTRUMENT = 1
    ACTION_PRICING_LATEST = 2
    ACTION_PRICE_HISTORY = 3
    ACTION_CHOICES = (
        (ACTION_INSTRUMENT, 'instrument'),
        (ACTION_PRICING_LATEST, 'pricing_latest'),
        (ACTION_PRICE_HISTORY, 'pricing_history'),
    )

    STATUS_PENDING = 0
    STATUS_REQUEST_SENT = 1
    STATUS_WAIT_RESPONSE = 2
    STATUS_DONE = 3
    STATUS_ERROR = -1
    STATUS_TIMEOUT = -2
    STATUS_CHOICES = (
        (STATUS_PENDING, 'PENDING'),
        (STATUS_REQUEST_SENT, 'REQUEST_SENT'),
        (STATUS_WAIT_RESPONSE, 'WAIT_RESPONSE'),
        (STATUS_DONE, 'DONE'),
        (STATUS_ERROR, 'ERROR'),
        (STATUS_TIMEOUT, 'TIMEOUT'),
    )

    master_user = models.ForeignKey('users.MasterUser', related_name='bloomberg_tasks')
    member = models.ForeignKey('users.Member', related_name='bloomberg_tasks', null=True, blank=True)

    status = models.SmallIntegerField(default=STATUS_PENDING, choices=STATUS_CHOICES)

    provider = models.ForeignKey(ProviderClass)
    action = models.SmallIntegerField(choices=ACTION_CHOICES, db_index=True)

    # request
    kwargs = models.TextField(null=True, blank=True)
    isin = models.CharField(max_length=100, null=True, blank=True)
    instruments = models.ManyToManyField('instruments.Instrument', blank=True)
    currencies = models.ManyToManyField('currencies.Currency', blank=True)
    date_from = models.DateField(null=True, blank=True)
    date_to = models.DateField(null=True, blank=True)

    response_id = models.CharField(max_length=64, null=True, blank=True, db_index=True)
    result = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = _('task')
        verbose_name_plural = _('tasks')
        ordering = ('-created',)

    def __str__(self):
        return '%s' % self.id

    @property
    def kwargs_object(self):
        if self.kwargs is None:
            return None
        return json.loads(self.kwargs)

    @property
    def result_object(self):
        if self.result is None:
            return None
        return json.loads(self.result)
