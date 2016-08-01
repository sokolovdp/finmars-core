from __future__ import unicode_literals, print_function

import uuid
from datetime import timedelta
from logging import getLogger

import six
from django.core.cache import caches
from django.core.exceptions import ObjectDoesNotExist
from django.core.signing import TimestampSigner, BadSignature
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from poms.common.fields import ISINField
from poms.currencies.fields import CurrencyField
from poms.currencies.serializers import CurrencyHistorySerializer
from poms.instruments.fields import InstrumentTypeField, InstrumentAttributeTypeField, InstrumentField
from poms.instruments.models import Instrument
from poms.instruments.serializers import InstrumentAttributeSerializer, PriceHistorySerializer
from poms.integrations.fields import InstrumentMappingField
from poms.integrations.models import InstrumentMapping, InstrumentAttributeMapping, BloombergConfig, BloombergTask
from poms.integrations.providers.bloomberg import create_instrument_price_history, create_currency_price_history
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

    def validate(self, attrs):
        attrs = super(PriceHistoryBloombergImportSerializer, self).validate(attrs)
        date_from = attrs.get('date_from', None)
        date_to = attrs.get('date_to', None)
        if date_from or date_to:
            now = timezone.now().date()
            date_from = date_from or now
            date_to = date_to or now
            if date_from > date_to:
                raise ValidationError({
                    'date_from': 'Invalid date range',
                    'date_to': 'Invalid date range',
                })
        return attrs

    def create(self, validated_data):
        instance = PriceHistoryBloombergImport(**validated_data)
        if instance.task:
            if instance.task_object.status == BloombergTask.STATUS_DONE:
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
                yesterday = timezone.now().date() - timedelta(days=1)
                action = BloombergTask.ACTION_PRICE_HISTORY
                if (instance.date_from is None and instance.date_to is None) or \
                        (instance.date_from == yesterday and instance.date_to == yesterday):
                    action = BloombergTask.ACTION_PRICING_LATEST
                if instance.date_from is None:
                    instance.date_from = yesterday
                if instance.date_to is None:
                    instance.date_to = yesterday

                if action == BloombergTask.ACTION_PRICING_LATEST:
                    from poms.integrations.tasks import bloomberg_pricing_latest
                    instance.task = bloomberg_pricing_latest(
                        master_user=instance.master_user,
                        member=instance.member,
                        instruments=instruments,
                        date_from=instance.date_from,
                        date_to=instance.date_to
                    )
                else:
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

    def validate(self, attrs):
        attrs = super(CurrencyHistoryBloombergImportSerializer, self).validate(attrs)
        date_from = attrs.get('date_from', None)
        date_to = attrs.get('date_to', None)
        if date_from or date_to:
            now = timezone.now().date()
            date_from = date_from or now
            date_to = date_to or now
            if date_from > date_to:
                raise ValidationError({
                    'date_from': 'Invalid date range',
                    'date_to': 'Invalid date range',
                })
        return attrs

    def create(self, validated_data):
        instance = CurrencyHistoryBloombergImport(**validated_data)
        if instance.task:
            if instance.task_object.status == BloombergTask.STATUS_DONE:
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
                    'industry': 'CCY',
                })
            if currencies:
                yesterday = timezone.now().date() - timedelta(days=1)
                action = BloombergTask.ACTION_PRICE_HISTORY
                if (instance.date_from is None and instance.date_to is None) or \
                        (instance.date_from == yesterday and instance.date_to == yesterday):
                    action = BloombergTask.ACTION_PRICING_LATEST
                if instance.date_from is None:
                    instance.date_from = yesterday
                if instance.date_to is None:
                    instance.date_to = yesterday

                from poms.integrations.tasks import bloomberg_pricing_history
                if action == BloombergTask.ACTION_PRICING_LATEST:
                    from poms.integrations.tasks import bloomberg_pricing_latest
                    instance.task = bloomberg_pricing_latest(
                        master_user=instance.master_user,
                        member=instance.member,
                        instruments=currencies,
                        date_from=instance.date_from,
                        date_to=instance.date_to
                    )
                else:
                    from poms.integrations.tasks import bloomberg_pricing_history
                    instance.task = bloomberg_pricing_history(
                        master_user=instance.master_user,
                        member=instance.member,
                        instruments=currencies,
                        date_from=instance.date_from,
                        date_to=instance.date_to
                    )

        return instance
