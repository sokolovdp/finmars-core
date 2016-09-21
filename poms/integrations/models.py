from __future__ import unicode_literals, print_function

import json
import uuid
from datetime import date, datetime, timedelta
from logging import getLogger

from croniter import croniter
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext, ugettext_lazy

from poms.common.models import TimeStampedModel, AbstractClassModel
from poms.instruments.models import Instrument, InstrumentAttribute
from poms.integrations.storage import import_config_storage
from poms.obj_attrs.models import AbstractAttributeType

_l = getLogger('poms.integrations')


class ProviderClass(AbstractClassModel):
    BLOOMBERG = 1
    CLASSES = (
        (BLOOMBERG, 'BLOOMBERG', ugettext_lazy("Bloomberg")),
    )

    class Meta(AbstractClassModel.Meta):
        pass


class FactorScheduleDownloadMethod(AbstractClassModel):
    IGNORE = 1
    DEFAULT = 2
    CLASSES = (
        (IGNORE, 'IGNORE', ugettext_lazy("Ignore")),
        (DEFAULT, 'DEFAULT', ugettext_lazy("Default")),
    )

    class Meta(AbstractClassModel.Meta):
        pass


class AccrualScheduleDownloadMethod(AbstractClassModel):
    IGNORE = 1
    DEFAULT = 2
    CLASSES = (
        (IGNORE, 'IGNORE', ugettext_lazy("Ignore")),
        (DEFAULT, 'DEFAULT', ugettext_lazy("Default")),
    )

    class Meta(AbstractClassModel.Meta):
        pass


def import_cert_upload_to(instance, filename):
    # return '%s/%s' % (instance.master_user_id, filename)
    return '%s/%s-%s' % (instance.master_user_id, instance.provider_id, uuid.uuid4().hex)


class ImportConfig(models.Model):
    master_user = models.ForeignKey('users.MasterUser', related_name='import_configs')
    provider = models.ForeignKey(ProviderClass)
    p12cert = models.FileField(null=True, blank=True, upload_to=import_cert_upload_to, storage=import_config_storage)
    password = models.CharField(max_length=64, null=True, blank=True)
    cert = models.FileField(null=True, blank=True, upload_to=import_cert_upload_to, storage=import_config_storage)
    key = models.FileField(null=True, blank=True, upload_to=import_cert_upload_to, storage=import_config_storage)

    class Meta:
        verbose_name = ugettext_lazy('import config')
        verbose_name_plural = ugettext_lazy('import configs')
        unique_together = [
            ['master_user', 'provider']
        ]

    def __str__(self):
        return '%s' % self.provider.name

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
    user_text_1 = models.CharField(max_length=255, blank=True, default='')
    user_text_2 = models.CharField(max_length=255, blank=True, default='')
    user_text_3 = models.CharField(max_length=255, blank=True, default='')

    maturity_date = models.CharField(max_length=255, blank=True, default='')

    payment_size_detail = models.ForeignKey('instruments.PaymentSizeDetail', on_delete=models.PROTECT,
                                            null=True, blank=True, verbose_name=ugettext_lazy('payment size detail'))
    daily_pricing_model = models.ForeignKey('instruments.DailyPricingModel', null=True, blank=True,
                                            verbose_name=ugettext_lazy('daily pricing model'))
    price_download_scheme = models.ForeignKey('integrations.PriceDownloadScheme', on_delete=models.PROTECT, null=True,
                                              blank=True, verbose_name=ugettext_lazy('price download scheme'))
    default_price = models.FloatField(default=0.0, verbose_name=ugettext_lazy('default price'))
    default_accrued = models.FloatField(default=0.0, verbose_name=ugettext_lazy('default accrued'))

    factor_schedule_method = models.ForeignKey(FactorScheduleDownloadMethod, null=True, blank=True)
    accrual_calculation_schedule_method = models.ForeignKey(AccrualScheduleDownloadMethod, null=True, blank=True)

    class Meta:
        index_together = (
            ('master_user', 'scheme_name')
        )
        verbose_name = ugettext_lazy('instrument download scheme')
        verbose_name_plural = ugettext_lazy('instrument download schemes')
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
        verbose_name = ugettext_lazy('instrument download scheme input')
        verbose_name_plural = ugettext_lazy('instrument download scheme inputs')

    def __str__(self):
        return self.name

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self.field:
            self.field = self.name
        return super(InstrumentDownloadSchemeInput, self).save(
            force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)


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
        verbose_name = ugettext_lazy('instrument download scheme attribute')
        verbose_name_plural = ugettext_lazy('instrument download schemes attribute')

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
        verbose_name = ugettext_lazy('price download scheme')
        verbose_name_plural = ugettext_lazy('price download schemes')

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
        verbose_name = ugettext_lazy('currency mapping')
        verbose_name_plural = ugettext_lazy('currency mappings')

    def __str__(self):
        return '%s / %s -> %s' % (self.provider, self.value, self.currency)


class InstrumentTypeMapping(AbstractMapping):
    instrument_type = models.ForeignKey('instruments.InstrumentType')

    class Meta:
        verbose_name = ugettext_lazy('instrument type mapping')
        verbose_name_plural = ugettext_lazy('instrument type mappings')

    def __str__(self):
        return '%s / %s -> %s' % (self.provider, self.value, self.instrument_type)


class InstrumentAttributeValueMapping(AbstractMapping):
    attribute_type = models.ForeignKey('instruments.InstrumentAttributeType', on_delete=models.PROTECT,
                                       verbose_name=ugettext_lazy('attribute type'))
    value_string = models.CharField(max_length=255, default='', blank=True,
                                    verbose_name=ugettext_lazy('value (String)'))
    value_float = models.FloatField(default=0.0, verbose_name=ugettext_lazy('value (Float)'))
    value_date = models.DateField(default=date.min, verbose_name=ugettext_lazy('value (Date)'))
    classifier = models.ForeignKey('instruments.InstrumentClassifier', on_delete=models.SET_NULL, null=True, blank=True,
                                   verbose_name=ugettext_lazy('classifier'))

    class Meta:
        verbose_name = ugettext_lazy('instrument attribute value mapping')
        verbose_name_plural = ugettext_lazy('instrument attribute value mappings')

    def __str__(self):
        value = self.attribute_type.get_value(self)
        return '%s / %s -> %s / %s' % (self.provider, self.value, self.attribute_type, value)


class AccrualCalculationModelMapping(AbstractMapping):
    accrual_calculation_model = models.ForeignKey('instruments.AccrualCalculationModel')

    class Meta:
        verbose_name = ugettext_lazy('accrual calculation model mapping')
        verbose_name_plural = ugettext_lazy('accrual calculation model  mappings')

    def __str__(self):
        return '%s / %s -> %s' % (self.provider, self.value, self.accrual_calculation_model)


class PeriodicityMapping(AbstractMapping):
    periodicity = models.ForeignKey('instruments.Periodicity')

    class Meta:
        verbose_name = ugettext_lazy('periodicity mapping')
        verbose_name_plural = ugettext_lazy('periodicity  mappings')

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

    master_user = models.ForeignKey('users.MasterUser', related_name='tasks')
    member = models.ForeignKey('users.Member', related_name='tasks', null=True, blank=True)

    provider = models.ForeignKey(ProviderClass, null=True, blank=True, db_index=True)
    action = models.CharField(max_length=20, db_index=True)
    status = models.CharField(max_length=1, default=STATUS_PENDING, choices=STATUS_CHOICES)

    celery_tasks_id = models.CharField(max_length=255, blank=True, default='')
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children')

    options = models.TextField(null=True, blank=True)
    result = models.TextField(null=True, blank=True)
    request_id = models.CharField(max_length=50, null=True, db_index=True)
    response_id = models.CharField(max_length=50, null=True, db_index=True)

    class Meta:
        verbose_name = ugettext_lazy('task')
        verbose_name_plural = ugettext_lazy('tasks')
        index_together = (
            ('master_user', 'created')
        )
        ordering = ('-created',)

    def __str__(self):
        return '%s / %s' % (self.id, self.status)

    @property
    def is_running(self):
        return self.status in [self.STATUS_PENDING, self.STATUS_REQUEST_SENT, self.STATUS_WAIT_RESPONSE]

    @property
    def is_finished(self):
        return self.status in [self.STATUS_DONE, self.STATUS_ERROR, self.STATUS_TIMEOUT]

    def add_celery_task_id(self, celery_task_id):
        if not celery_task_id:
            return
        if self.celery_tasks_id is None:
            self.celery_tasks_id = ''
        if celery_task_id in self.celery_tasks_id:
            return
        if self.celery_tasks_id:
            self.celery_tasks_id = '%s %s' % (self.celery_tasks_id, celery_task_id)
        else:
            self.celery_tasks_id = celery_task_id

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


# def to_crontab(value):
#     from celery.schedules import crontab
#
#     if value:
#         elmts = value.split()
#         if len(elmts) != 5:
#             raise ValueError('Invalid crontab expression')
#
#         minute = elmts[0]
#         hour = elmts[1]
#         day_of_week = elmts[2]
#         day_of_month = elmts[3]
#         month_of_year = elmts[4]
#         try:
#             return crontab(
#                 minute=minute,
#                 hour=hour,
#                 day_of_week=day_of_week,
#                 day_of_month=day_of_month,
#                 month_of_year=month_of_year
#             )
#         except (TypeError, ValueError):
#             raise ValueError('Invalid crontab expression')


def validate_crontab(value):
    try:
        # to_crontab(value)
        croniter(value, timezone.now())
    except (ValueError, KeyError):
        raise ValidationError(ugettext_lazy('A valid cron string is required.'))


class PricingAutomatedSchedule(models.Model):
    master_user = models.OneToOneField('users.MasterUser', related_name='pricing_automated_schedule',
                                       verbose_name=ugettext_lazy('master user'))

    is_enabled = models.BooleanField(default=True)
    cron_expr = models.CharField(max_length=255, blank=True, default='', validators=[validate_crontab],
                                 help_text=ugettext_lazy(
                                     'Format is "* * * * *" (minute / hour / day_month / month / day_week)'))
    balance_day = models.PositiveSmallIntegerField(default=0)
    load_days = models.PositiveSmallIntegerField(default=1)
    fill_days = models.PositiveSmallIntegerField(default=0)
    override_existed = models.BooleanField(default=True)

    # latest_running = models.DateTimeField(null=True, blank=True, editable=False)
    # latest_task = models.ForeignKey(Task, null=True, blank=True, on_delete=models.SET_NULL, editable=False)

    last_run_at = models.DateTimeField(default=timezone.now, editable=False, db_index=True)
    next_run_at = models.DateTimeField(default=timezone.now, editable=False, db_index=True)
    last_run_task = models.ForeignKey(Task, null=True, blank=True, on_delete=models.SET_NULL, editable=False,
                                      db_index=True)

    class Meta:
        verbose_name = ugettext_lazy('pricing automated schedule')
        verbose_name_plural = ugettext_lazy('pricing automated schedules')
        index_together = (
            ('is_enabled', 'next_run_at'),
        )

    def __str__(self):
        return ugettext('pricing automated schedule')

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.is_enabled:
            self.schedule(save=False)
        super(PricingAutomatedSchedule, self).save(force_insert=force_insert, force_update=force_update, using=using,
                                                   update_fields=update_fields)

    # def to_crontab(self):
    #     if self.is_enabled and self.cron_expr:
    #         return to_crontab(self.cron_expr)
    #     return None

    def can_schedule(self):
        return self.latest_task is None or self.latest_task.is_finished

    def schedule(self, save=False):
        start_time = timezone.localtime(timezone.now())
        cron = croniter(self.cron_expr, start_time)

        next_run_at = cron.get_next(datetime)

        min_timedelta = settings.PRICING_AUTO_DOWNLOAD_MIN_TIMEDELTA
        if min_timedelta is not None:
            if not isinstance(min_timedelta, timedelta):
                min_timedelta = timedelta(minutes=min_timedelta)
            for i in range(100):
                if (next_run_at - start_time) >= min_timedelta:
                    break
                next_run_at = cron.get_next(datetime)

        self.next_run_at = next_run_at

        if save:
            self.save(update_fields=['last_run_at', 'next_run_at', ])
