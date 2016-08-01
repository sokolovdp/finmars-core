from __future__ import unicode_literals, print_function

import uuid
from datetime import timedelta
from logging import getLogger

import six
from django.core.cache import caches
from django.core.exceptions import ObjectDoesNotExist
from django.core.signing import TimestampSigner, BadSignature
from django.db import IntegrityError
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from poms.common import formula
from poms.common.fields import ISINField
from poms.currencies.fields import CurrencyField
from poms.currencies.models import CurrencyHistory
from poms.currencies.serializers import CurrencyHistorySerializer
from poms.instruments.fields import InstrumentTypeField, InstrumentAttributeTypeField, InstrumentField
from poms.instruments.models import Instrument, PriceHistory
from poms.instruments.serializers import InstrumentAttributeSerializer, PriceHistorySerializer
from poms.integrations.fields import InstrumentMappingField
from poms.integrations.models import InstrumentMapping, InstrumentAttributeMapping, BloombergConfig, BloombergTask
from poms.integrations.providers.bloomberg import str_to_date, map_pricing_history
from poms.integrations.storage import FileImportStorage
from poms.users.fields import MasterUserField, MemberField, HiddenMemberField

_l = getLogger('poms.integrations')

IMPORT_PREVIEW = 1
IMPORT_PROCESS = 2

IMPORT_MODE_CHOICES = (
    (IMPORT_PREVIEW, 'Preview'),
    (IMPORT_PROCESS, 'Process'),
)

FILE_FORMAT_CSV = 1
FILE_FORMAT_CHOICES = (
    (FILE_FORMAT_CSV, 'CSV'),
)

bloomberg_cache = caches['bloomberg']


class InstrumentAttributeMappingSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    attribute_type = InstrumentAttributeTypeField()

    class Meta:
        model = InstrumentAttributeMapping
        fields = ['id', 'attribute_type', 'name']


class InstrumentMappingSerializer(serializers.ModelSerializer):
    master_user = MasterUserField()
    attributes = InstrumentAttributeMappingSerializer(many=True, read_only=False)

    class Meta:
        model = InstrumentMapping
        fields = ['url', 'id', 'master_user', 'mapping_name', 'user_code', 'name', 'short_name', 'public_name', 'notes',
                  'instrument_type', 'pricing_currency', 'price_multiplier', 'accrued_currency', 'accrued_multiplier',
                  'daily_pricing_model', 'payment_size_detail', 'default_price', 'default_accrued',
                  'user_text_1', 'user_text_2', 'user_text_3', 'price_download_mode',
                  'attributes']

    def create(self, validated_data):
        attributes = validated_data.pop('attributes', None) or tuple()
        instance = super(InstrumentMappingSerializer, self).create(validated_data)
        self.save_attributes(instance, attributes)
        return instance

    def update(self, instance, validated_data):
        attributes = validated_data.pop('attributes', None) or tuple()
        instance = super(InstrumentMappingSerializer, self).update(instance, validated_data)
        self.save_attributes(instance, attributes)
        return instance

    def save_attributes(self, instance, attributes):
        attrs = set()
        for attr_values in attributes:
            attr_id = attr_values.pop('id', None)
            attr = None
            if attr_id:
                try:
                    attr = instance.attributes.get(pk=attr_id)
                except ObjectDoesNotExist:
                    pass
            if attr is None:
                attr = InstrumentAttributeMapping(mapping=instance)
            for name, value in six.iteritems(attr_values):
                setattr(attr, name, value)
            attr.save()
            attrs.add(attr.id)
        instance.attributes.exclude(pk__in=attrs).delete()


class BloombergConfigSerializer(serializers.ModelSerializer):
    master_user = MasterUserField()
    p12cert = serializers.FileField(allow_null=True, allow_empty_file=False, write_only=True)
    password = serializers.CharField(allow_null=True, allow_blank=True, write_only=True)

    # cert = serializers.FileField(allow_null=True, allow_empty_file=False, write_only=True)
    # key = serializers.FileField(allow_null=True, allow_empty_file=False, write_only=True)

    class Meta:
        model = BloombergConfig
        fields = [
            'url', 'id', 'master_user', 'p12cert', 'password',
            # 'cert', 'key',
            'has_p12cert', 'has_password',
            # 'has_cert', 'has_key'
        ]


class BloombergTaskSerializer(serializers.ModelSerializer):
    master_user = MasterUserField()
    member = MemberField()

    # kwargs = serializers.SerializerMethodField()
    # result = serializers.SerializerMethodField()

    class Meta:
        model = BloombergTask
        fields = ['url', 'id', 'master_user', 'member', 'action', 'created', 'modified', 'status',
                  # 'kwargs', 'result'
                  ]

        # def get_kwargs(self, obj):
        #     if obj.kwargs:
        #         return json.loads(obj.kwargs)
        #     return None
        #
        # def get_result(self, obj):
        #     if obj.result:
        #         return json.loads(obj.result)
        #     return None


class InstrumentFileImportSerializer(serializers.Serializer):
    master_user = MasterUserField()
    mode = serializers.ChoiceField(choices=IMPORT_MODE_CHOICES)

    file = serializers.FileField(required=False, allow_null=True)
    token = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    format = serializers.ChoiceField(choices=FILE_FORMAT_CHOICES)
    skip_first_line = serializers.BooleanField()
    delimiter = serializers.CharField(max_length=1, initial=',')
    quotechar = serializers.CharField(max_length=1, initial='|')
    encoding = serializers.CharField(max_length=10, initial='utf-8')

    instrument_type = InstrumentTypeField(required=False, allow_null=True)

    def create(self, validated_data):
        _l.info('InstrumentFileImportSerializer.create: %s', validated_data)
        storage = FileImportStorage()

        master_user = validated_data['master_user']

        if validated_data.get('token', None):
            try:
                token = TimestampSigner().unsign(validated_data['token'])
            except BadSignature:
                raise ValidationError({'token': 'Invalid value.'})
            tmp_file_name = self.get_file_path(master_user, token)
        else:
            file = validated_data['file']
            if not file:
                raise ValidationError({'file': 'This field is required.'})
            token = '%s' % (uuid.uuid4().hex,)
            validated_data['token'] = TimestampSigner().sign(token)
            tmp_file_name = self.get_file_path(master_user, token)
            storage.save(tmp_file_name, file)

            from poms.integrations.tasks import schedule_file_import_delete
            schedule_file_import_delete(tmp_file_name)

        with storage.open(tmp_file_name, 'rt') as f:
            # ret = []
            # import csv
            # for row in csv.reader(f):
            #     ret.append(row)
            #     data['preview'] = ret
            pass

        return validated_data

    def get_file_path(self, owner, token):
        return '%s/%s/%s' % (owner.pk, token[0:4], token)


class InstrumentBloombergImport(object):
    def __init__(self, master_user=None, member=None, mapping=None, mode=None, isin=None, task=None,
                 instrument=None):
        self.master_user = master_user
        self.member = member
        self.mapping = mapping
        self.mode = mode
        self.isin = isin
        self.task = task
        self._task_object = None
        self.instrument = instrument

    @property
    def task_object(self):
        if self.task:
            self._task_object = self.master_user.bloomberg_tasks.get(pk=self.task)
        return self._task_object

    @property
    def to_request(self):
        return {
            'code': self.isin[0],
            'industry': self.isin[1],
        }


class ImportInstrumentSerializer(serializers.ModelSerializer):
    # instrument_type = serializers.PrimaryKeyRelatedField(read_only=True)
    # pricing_currency = serializers.PrimaryKeyRelatedField(read_only=True)
    # accrued_currency = serializers.PrimaryKeyRelatedField(read_only=True)

    # manual_pricing_formulas = ManualPricingFormulaSerializer(many=True, read_only=True)
    # accrual_calculation_schedules = AccrualCalculationScheduleSerializer(many=True, read_only=True)
    # factor_schedules = InstrumentFactorScheduleSerializer(many=True, read_only=True)
    # event_schedules = EventScheduleSerializer(many=True, read_only=True)

    # attributes = InstrumentAttributeSerializer(many=True, read_only=True)
    attributes = serializers.SerializerMethodField()

    # tags = TagField(many=True, read_only=True)

    class Meta:
        model = Instrument
        fields = ['id', 'instrument_type', 'user_code', 'name', 'short_name', 'public_name',
                  'notes', 'is_active',
                  'pricing_currency', 'price_multiplier', 'accrued_currency', 'accrued_multiplier',
                  'daily_pricing_model', 'payment_size_detail', 'price_download_mode',
                  'default_price', 'default_accrued',
                  'user_text_1', 'user_text_2', 'user_text_3',
                  # 'manual_pricing_formulas', 'accrual_calculation_schedules', 'factor_schedules', 'event_schedules',
                  'attributes',
                  # 'tags',
                  ]

    def get_attributes(self, obj):
        if hasattr(obj, 'attributes_preview'):
            return InstrumentAttributeSerializer(instance=obj.attributes_preview, many=True, read_only=True).data
        else:
            return InstrumentAttributeSerializer(instance=obj.attributes.all(), many=True, read_only=True).data


class InstrumentBloombergImportSerializer(serializers.Serializer):
    master_user = MasterUserField()
    member = HiddenMemberField()
    mapping = InstrumentMappingField()
    mode = serializers.ChoiceField(choices=IMPORT_MODE_CHOICES)

    isin = ISINField(required=True, initial='XS1433454243 Corp')
    # code = serializers.CharField(required=False, allow_null=True, allow_blank=True, initial='XS1433454243')
    # industry = serializers.CharField(required=False, allow_null=True, allow_blank=True, initial='Corp')

    task = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    task_object = BloombergTaskSerializer(read_only=True)
    instrument = ImportInstrumentSerializer(read_only=True)

    def create(self, validated_data):
        instance = InstrumentBloombergImport(**validated_data)
        if instance.task:
            if instance.task_object.status == BloombergTask.STATUS_DONE:
                values = instance.task_object.result_object
                if instance.mode == IMPORT_PREVIEW:
                    instance.instrument = instance.mapping.create_instrument(values, save=False)
                else:
                    instance.instrument = instance.mapping.create_instrument(values, save=True)
        else:
            from poms.integrations.tasks import bloomberg_instrument
            instance.task = bloomberg_instrument(
                master_user=instance.master_user, member=instance.member,
                instrument=instance.to_request,
                fields=list(instance.mapping.mapping_fields))

        return instance


def create_instrument_price_history(task, instruments=None, pricing_policies=None, save=False,
                                    map_func=map_pricing_history, delete_exists=False, fail_silently=False,
                                    date_range=None):
    result = task.result_object

    if instruments is None:
        instruments = list(task.master_user.instruments.all())
    instr_map = {six.text_type(i.id): i for i in instruments}

    if pricing_policies is None:
        pricing_policies = list(task.master_user.pricing_policies.all())

    exists = set()
    if fail_silently and date_range:
        for p in PriceHistory.objects.filter(instrument__in=instruments, date__range=date_range):
            exists.add(
                (p.instrument_id, p.pricing_policy_id, p.date)
            )
    if delete_exists and date_range:
        PriceHistory.objects.filter(instrument__in=instruments, date__range=date_range).delete()

    histories = []
    for instr_code, values in result.items():
        instr = instr_map.get(instr_code, None)
        if instr is None:
            continue
        for pd in values:
            pd = map_func(pd)
            for pp in pricing_policies:
                p = PriceHistory()
                p.instrument = instr
                p.date = str_to_date(pd['date'])
                p.pricing_policy = pp
                p.principal_price = formula.safe_eval(pp.expr, names=pd)
                p.accrued_price = 0.0
                p.factor = 1.0

                if fail_silently and (p.instrument_id, p.pricing_policy_id, p.date) in exists:
                    continue

                if save:
                    try:
                        p.save()
                    except IntegrityError:
                        if not fail_silently:
                            raise

                _l.debug(
                    'PriceHistory: id=%s, instrument=%s, date=%s, pricing_policy=%s, principal_price=%s, accrued_price=%s, factor=%s',
                    p.id, p.instrument.id, p.date, p.pricing_policy.id, p.principal_price, p.accrued_price, p.factor)

                histories.append(p)

    # if save:
    #     PriceHistory.objects.bulk_create(histories)

    return histories


def create_currency_price_history(task, currencies=None, pricing_policies=None, save=False,
                                  map_func=map_pricing_history, delete_exists=False, fail_silently=False,
                                  date_range=None):
    result = task.result_object

    if currencies is None:
        currencies = list(task.master_user.currencies.all())

    ccy_map = {six.text_type(i.id): i for i in currencies}

    if pricing_policies is None:
        pricing_policies = list(task.master_user.pricing_policies.all())

    exists = set()
    if fail_silently and date_range:
        for p in CurrencyHistory.objects.filter(currency__in=currencies, date__range=date_range):
            exists.add(
                (p.currency_id, p.pricing_policy_id, p.date)
            )
    if delete_exists and date_range:
        CurrencyHistory.objects.filter(currency__in=currencies, date__range=date_range).delete()

    histories = []
    for ccy_code, values in result.items():
        ccy = ccy_map.get(ccy_code, None)
        if ccy is None:
            continue
        for pd in values:
            pd = map_func(pd)
            for pp in pricing_policies:
                p = CurrencyHistory()
                p.currency = ccy
                p.date = str_to_date(pd['date'])
                p.pricing_policy = pp
                p.fx_rate = formula.safe_eval(pp.expr, names=pd)

                if fail_silently and (p.currency_id, p.pricing_policy_id, p.date) in exists:
                    continue

                if save:
                    try:
                        p.save()
                    except IntegrityError:
                        if not fail_silently:
                            raise

                histories.append(p)

                _l.debug(
                    'CurrencyHistory: id=%s, currency=%s, date=%s, pricing_policy=%s, fx_rate=%s',
                    p.id, p.currency.id, p.date, p.pricing_policy.id, p.fx_rate)

    # if save:
    #     PriceHistory.objects.bulk_create(histories)

    return histories


class PriceHistoryBloombergImport(object):
    def __init__(self, master_user=None, member=None, mode=None, instruments=None,
                 date_from=None, date_to=None, task=None, histories=None):
        self.master_user = master_user
        self.member = member
        self.mode = mode
        self.instruments = instruments
        self.date_from = date_from
        self.date_to = date_to
        self.task = task
        self._task_object = None
        self.histories = histories

    @property
    def task_object(self):
        if self.task:
            self._task_object = self.master_user.bloomberg_tasks.get(pk=self.task)
        return self._task_object


class PriceHistoryBloombergImportSerializer(serializers.Serializer):
    master_user = MasterUserField()
    mode = serializers.ChoiceField(choices=IMPORT_MODE_CHOICES)
    instruments = InstrumentField(many=True, allow_empty=False)
    date_from = serializers.DateField(allow_null=True, required=False)
    date_to = serializers.DateField(allow_null=True, required=False)
    task = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    task_object = BloombergTaskSerializer(read_only=True)
    histories = PriceHistorySerializer(many=True, read_only=True)

    def create(self, validated_data):
        instance = PriceHistoryBloombergImport(**validated_data)
        if instance.task:
            if instance.task_object.status == BloombergTask.STATUS_DONE:
                # values = instance.task_object.result_object
                # instr_map = {str(i.id): i for i in instance.instruments}
                # pricing_policies = list(instance.master_user.pricing_policies.all())
                # for instr_code, values in values.items():
                #     instr = instr_map[instr_code]
                #     for pd in values:
                #         pd = map_pricing_history(pd)
                #         for pp in pricing_policies:
                #             p = PriceHistory()
                #             p.instrument = instr
                #             p.date = str_to_date(pd['date'])
                #             p.pricing_policy = pp
                #             p.principal_price = formula.safe_eval(pp.expr, names=pd)
                #             p.accrued_price = 0.0
                #             p.factor = 1.0
                #             if instance.mode == IMPORT_PROCESS:
                #                 p.save()
                #             instance.histories.append(p)
                instance.histories = create_instrument_price_history(
                    task=instance.task_object,
                    instruments=instance.instruments,
                    save=instance.mode == IMPORT_PROCESS,
                    date_range=(instance.date_from, instance.date_to),
                    fail_silently=True
                )
        else:
            instruments = []
            for instr in instance.instruments:
                instruments.append({
                    'code': instr.id,
                    'industry': 'Corp',
                })

            if instruments:
                if instance.date_from is None:
                    instance.date_from = timezone.now().date() - timedelta(days=1)
                if instance.date_to is None:
                    instance.date_to = timezone.now().date() - timedelta(days=1)

                from poms.integrations.tasks import bloomberg_pricing_history
                instance.task = bloomberg_pricing_history(
                    master_user=instance.master_user,
                    member=instance.member,
                    instruments=instruments,
                    date_from=instance.date_from,
                    date_to=instance.date_to
                )

        return instance


class CurrencyHistoryBloombergImport(object):
    def __init__(self, master_user=None, member=None, mode=None, currencies=None,
                 date_from=None, date_to=None, task=None, histories=None):
        self.master_user = master_user
        self.member = member
        self.mode = mode
        self.currencies = currencies
        self.date_from = date_from
        self.date_to = date_to
        self.task = task
        self._task_object = None
        self.histories = histories

    @property
    def task_object(self):
        if self.task:
            self._task_object = self.master_user.bloomberg_tasks.get(pk=self.task)
        return self._task_object


class CurrencyHistoryBloombergImportSerializer(serializers.Serializer):
    master_user = MasterUserField()
    mode = serializers.ChoiceField(choices=IMPORT_MODE_CHOICES)
    currencies = CurrencyField(many=True, allow_empty=False)
    date_from = serializers.DateField(allow_null=True, required=False)
    date_to = serializers.DateField(allow_null=True, required=False)
    task = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    task_object = BloombergTaskSerializer(read_only=True)
    histories = CurrencyHistorySerializer(many=True, read_only=True)

    def create(self, validated_data):
        instance = CurrencyHistoryBloombergImport(**validated_data)
        if instance.task:
            if instance.task_object.status == BloombergTask.STATUS_DONE:
                # values = instance.task_object.result_object
                # instance.histories = []
                # ccy_map = {str(i.id): i for i in instance.currencies}
                # pricing_policies = list(instance.master_user.pricing_policies.all())
                # for ccy_code, values in values.items():
                #     ccy = ccy_map[ccy_code]
                #     for pd in values:
                #         pd = map_pricing_history(pd)
                #         for pp in pricing_policies:
                #             p = CurrencyHistory()
                #             p.currency = ccy
                #             p.date = str_to_date(pd['date'])
                #             p.pricing_policy = pp
                #             p.fx_rate = formula.safe_eval(pp.expr, names=pd)
                #             if instance.mode == IMPORT_PROCESS:
                #                 p.save()
                #             instance.histories.append(p)
                instance.histories = create_currency_price_history(
                    task=instance.task_object,
                    currencies=instance.currencies,
                    save=instance.mode == IMPORT_PROCESS,
                    date_range=(instance.date_from, instance.date_to),
                    fail_silently=True
                )
        else:
            currencies = []
            for ccy in instance.currencies:
                currencies.append({
                    'code': ccy.id,
                    'industry': 'Corp',
                })
            if currencies:
                if instance.date_from is None:
                    instance.date_from = timezone.now().date() - timedelta(days=1)
                if instance.date_to is None:
                    instance.date_to = timezone.now().date() - timedelta(days=1)

                from poms.integrations.tasks import bloomberg_pricing_history
                instance.task = bloomberg_pricing_history(
                    master_user=instance.master_user,
                    member=instance.member,
                    instruments=currencies,
                    date_from=instance.date_from,
                    date_to=instance.date_to
                )

        return instance
