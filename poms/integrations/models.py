from __future__ import unicode_literals, print_function

import json
import uuid
from logging import getLogger

from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from poms.common.models import TimeStampedModel, AbstractClassModel
from poms.instruments.models import Instrument, InstrumentAttribute
from poms.integrations.storage import import_config_storage
from poms.obj_attrs.models import AbstractAttributeType

_l = getLogger('poms.integrations')


class ProviderClass(AbstractClassModel):
    BLOOMBERG = 1
    CLASSES = (
        (BLOOMBERG, 'BLOOMBERG', _("Bloomberg")),
    )

    class Meta(AbstractClassModel.Meta):
        pass


class FactorScheduleDownloadMethod(AbstractClassModel):
    IGNORE = 1
    DEFAULT = 2
    CLASSES = (
        (IGNORE, 'IGNORE', _("Ignore")),
        (DEFAULT, 'DEFAULT', _("Default")),
    )

    class Meta(AbstractClassModel.Meta):
        pass


class AccrualScheduleDownloadMethod(AbstractClassModel):
    IGNORE = 1
    DEFAULT = 2
    CLASSES = (
        (IGNORE, 'IGNORE', _("Ignore")),
        (DEFAULT, 'DEFAULT', _("Default")),
    )

    class Meta(AbstractClassModel.Meta):
        pass


def import_cert_upload_to(instance, filename):
    # return '%s/%s' % (instance.master_user_id, filename)
    return '/'.join([instance.master_user_id, instance.provider_id, uuid.uuid4().hex])


class ImportConfig(models.Model):
    master_user = models.ForeignKey('users.MasterUser', related_name='import_configs')
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


# TODO: rename to InstrumentDownloadScheme
@python_2_unicode_compatible
class InstrumentDownloadScheme(models.Model):
    BASIC_FIELDS = ['reference_for_pricing', 'user_code', 'name', 'short_name', 'public_name', 'notes',
                    'instrument_type', 'pricing_currency', 'price_multiplier', 'accrued_currency', 'accrued_multiplier',
                    'user_text_1', 'user_text_2', 'user_text_3',
                    # 'daily_pricing_model',
                    # 'payment_size_detail',
                    # 'default_price',
                    # 'default_accrued',
                    # 'price_download_mode',
                    ]

    master_user = models.ForeignKey('users.MasterUser')
    scheme_name = models.CharField(max_length=255)
    provider = models.ForeignKey(ProviderClass)

    reference_for_pricing = models.CharField(max_length=255, blank=True, default='')
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

    factor_schedule_method = models.ForeignKey(FactorScheduleDownloadMethod, null=True, blank=True)
    accrual_calculation_schedule_method = models.ForeignKey(AccrualScheduleDownloadMethod, null=True, blank=True)

    class Meta:
        index_together = (
            ('master_user', 'scheme_name')
        )
        verbose_name = _('instrument download scheme')
        verbose_name_plural = _('instrument download schemes')
        # permissions = [
        #     ('view_instrumentdownloadscheme', 'Can view instrument download scheme'),
        #     ('manage_instrumentdownloadscheme', 'Can manage instrument download scheme'),
        # ]

    def __str__(self):
        return self.scheme_name

    @property
    def fields(self):
        return [f.field for f in self.inputs.all() if f.field]


class InstrumentDownloadSchemeInput(models.Model):
    scheme = models.ForeignKey(InstrumentDownloadScheme, related_name='inputs')
    name = models.CharField(max_length=32, blank=True, default='')
    field = models.CharField(max_length=32, blank=True, default='')

    class Meta:
        unique_together = (
            ('scheme', 'name')
        )
        ordering = ('name',)
        verbose_name = _('instrument download scheme input')
        verbose_name_plural = _('instrument download scheme inputs')

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class InstrumentDownloadSchemeAttribute(models.Model):
    scheme = models.ForeignKey(InstrumentDownloadScheme, related_name='attributes')
    attribute_type = models.ForeignKey('instruments.InstrumentAttributeType', null=True, blank=True)
    value = models.CharField(max_length=255, blank=True, default='')

    class Meta:
        unique_together = (
            ('scheme', 'attribute_type')
        )
        ordering = ('attribute_type__name',)
        verbose_name = _('instrument download scheme attribute')
        verbose_name_plural = _('instrument download schemes attribute')

    def __str__(self):
        # return '%s -> %s' % (self.name, self.attribute_type)
        return '%s' % (self.attribute_type,)


class PriceDownloadScheme(models.Model):
    master_user = models.ForeignKey('users.MasterUser')
    scheme_name = models.CharField(max_length=255)
    provider = models.ForeignKey(ProviderClass)

    bid0 = models.CharField(max_length=50, blank=True)
    bid1 = models.CharField(max_length=50, blank=True)
    bid2 = models.CharField(max_length=50, blank=True)
    bid_multiplier = models.FloatField(default=1.0)
    ask0 = models.CharField(max_length=50, blank=True)
    ask1 = models.CharField(max_length=50, blank=True)
    ask2 = models.CharField(max_length=50, blank=True)
    ask_multiplier = models.FloatField(default=1.0)
    last = models.CharField(max_length=50, blank=True)
    last_multiplier = models.FloatField(default=1.0)
    mid = models.CharField(max_length=50, blank=True)
    mid_multiplier = models.FloatField(default=1.0)

    bid_history = models.CharField(max_length=50, blank=True)
    bid_history_multiplier = models.FloatField(default=1.0)
    ask_history = models.CharField(max_length=50, blank=True)
    ask_history_multiplier = models.FloatField(default=1.0)
    mid_history = models.CharField(max_length=50, blank=True)
    mid_history_multiplier = models.FloatField(default=1.0)
    last_history = models.CharField(max_length=50, blank=True)
    last_history_multiplier = models.FloatField(default=1.0)

    currency_fxrate = models.CharField(max_length=50, blank=True)
    currency_fxrate_multiplier = models.FloatField(default=1.0)

    class Meta:
        unique_together = [
            ['master_user', 'scheme_name']
        ]
        verbose_name = _('price download scheme')
        verbose_name_plural = _('price download schemes')

    def __str__(self):
        return self.scheme_name

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
                value = values[field_name]
                return float(value) if value is not None else 0.0
        return 0.0

    @property
    def instrument_yesterday_fields(self):
        return self._get_fields('bid0', 'bid1', 'bid2', 'ask0', 'ask1', 'ask2', 'last', 'mid')

    @property
    def instrument_history_fields(self):
        return self._get_fields('bid_history', 'ask_history', 'mid_history', 'last_history')

    @property
    def currency_history_fields(self):
        return self._get_fields('currency_fxrate')

    def instrument_yesterday_values(self, values):
        return {
            'bid': self._get_value(values, 'bid0', 'bid1', 'bid2') * self.bid_multiplier,
            'ask': self._get_value(values, 'ask0', 'ask1', 'ask2') * self.ask_multiplier,
            'mid': self._get_value(values, 'mid') * self.last_multiplier,
            'last': self._get_value(values, 'last') * self.mid_multiplier,
        }

    def instrument_history_values(self, values):
        return {
            'bid': self._get_value(values, 'bid_history') * self.bid_history_multiplier,
            'ask': self._get_value(values, 'ask_history') * self.ask_history_multiplier,
            'mid': self._get_value(values, 'last_history') * self.last_history_multiplier,
            'last': self._get_value(values, 'mid_history') * self.mid_history_multiplier,
        }

    def currency_history_values(self, values):
        value = self._get_value(values, 'currency_fxrate')
        return {
            'bid': value * self.currency_fxrate_multiplier,
            'ask': value * self.currency_fxrate_multiplier,
            'mid': value * self.currency_fxrate_multiplier,
            'last': value * self.currency_fxrate_multiplier,
        }


class AbstractMapping(models.Model):
    master_user = models.ForeignKey('users.MasterUser')
    provider = models.ForeignKey(ProviderClass)
    value = models.CharField(max_length=255)

    class Meta:
        abstract = True


class CurrencyMapping(AbstractMapping):
    currency = models.ForeignKey('currencies.Currency')

    class Meta:
        verbose_name = _('currency mapping')
        verbose_name_plural = _('currency mappings')

    def __str__(self):
        return '%s / %s -> %s' % (self.provider, self.value, self.currency)


class InstrumentTypeMapping(AbstractMapping):
    instrument_type = models.ForeignKey('instruments.InstrumentType')

    class Meta:
        verbose_name = _('instrument type mapping')
        verbose_name_plural = _('instrument type mappings')

    def __str__(self):
        return '%s / %s -> %s' % (self.provider, self.value, self.instrument_type)


class InstrumentAttributeValueMapping(AbstractMapping):
    attribute_type = models.ForeignKey('instruments.InstrumentAttributeType', on_delete=models.PROTECT,
                                       verbose_name=_('attribute type'))
    value_string = models.CharField(max_length=255, null=True, blank=True, verbose_name=_('value (String)'))
    value_float = models.FloatField(null=True, blank=True, verbose_name=_('value (Float)'))
    value_date = models.DateField(null=True, blank=True, verbose_name=_('value (Date)'))
    classifier = models.ForeignKey('instruments.InstrumentClassifier', on_delete=models.PROTECT, null=True, blank=True,
                                   verbose_name=_('classifier'))

    class Meta:
        verbose_name = _('instrument attribute value mapping')
        verbose_name_plural = _('instrument attribute value mappings')

    def __str__(self):
        value = self.attribute_type.get_value(self)
        return '%s / %s -> %s / %s' % (self.provider, self.value, self.attribute_type, value)


class AccrualCalculationModelMapping(AbstractMapping):
    accrual_calculation_model = models.ForeignKey('instruments.AccrualCalculationModel')

    class Meta:
        verbose_name = _('accrual calculation model mapping')
        verbose_name_plural = _('accrual calculation model  mappings')

    def __str__(self):
        return '%s / %s -> %s' % (self.provider, self.value, self.accrual_calculation_model)


class PeriodicityMapping(AbstractMapping):
    periodicity = models.ForeignKey('instruments.Periodicity')

    class Meta:
        verbose_name = _('periodicity mapping')
        verbose_name_plural = _('periodicity  mappings')

    def __str__(self):
        return '%s / %s -> %s' % (self.provider, self.value, self.periodicity)


@python_2_unicode_compatible
class Task(TimeStampedModel):
    ACTION_INSTRUMENT = 'instrument'
    ACTION_PRICING = 'pricing'

    STATUS_PENDING = 'P'
    STATUS_REQUEST_SENT = 'S'
    STATUS_WAIT_RESPONSE = 'W'
    STATUS_DONE = 'D'
    STATUS_ERROR = 'E'
    STATUS_TIMEOUT = 'T'
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

    status = models.CharField(max_length=1, default=STATUS_PENDING, choices=STATUS_CHOICES)
    provider = models.ForeignKey(ProviderClass, null=True, blank=True)
    action = models.CharField(max_length=20, db_index=True)

    parent = models.ForeignKey('self', null=True, blank=True, related_name='children')

    # # instrument
    # instrument_code = models.CharField(max_length=100, null=True, blank=True)
    # instrument_download_scheme = models.ForeignKey(InstrumentDownloadScheme, null=True, blank=True,
    #                                                on_delete=models.SET_NULL)
    #
    # # pricing
    # date_from = models.DateField(null=True, blank=True)
    # date_to = models.DateField(null=True, blank=True)
    # balance_date = models.DateField(null=True, blank=True)
    # is_yesterday = models.NullBooleanField()
    # fill_days = models.IntegerField(null=True, blank=True)
    # override_existed = models.NullBooleanField()
    # price_download_scheme

    options = models.TextField(null=True, blank=True)
    result = models.TextField(null=True, blank=True)
    request_id = models.CharField(max_length=50, null=True, db_index=True)
    response_id = models.CharField(max_length=50, null=True, db_index=True)

    class Meta:
        verbose_name = _('task')
        verbose_name_plural = _('tasks')
        index_together = (
            ('master_user', 'created')
        )
        ordering = ('-created',)

    def __str__(self):
        return '%s' % self.id

    @property
    def options_object(self):
        if self.options is None:
            return None
        return json.loads(self.options)

    @options_object.setter
    def options_object(self, value):
        if value is None:
            self.options = None
        else:
            self.options = json.dumps(value, cls=DjangoJSONEncoder, sort_keys=True, indent=1)

    @property
    def result_object(self):
        if self.result is None:
            return None
        return json.loads(self.result)

    @result_object.setter
    def result_object(self, value):
        if value is None:
            self.result = None
        else:
            self.result = json.dumps(value, cls=DjangoJSONEncoder, sort_keys=True, indent=1)
