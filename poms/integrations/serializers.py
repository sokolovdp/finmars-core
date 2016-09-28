from __future__ import unicode_literals, print_function

import json
import uuid
from datetime import timedelta
from logging import getLogger

from django.core.exceptions import ObjectDoesNotExist
from django.core.signing import TimestampSigner, BadSignature
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from poms.common.fields import ExpressionField, DateTimeTzAwareField
from poms.common.serializers import PomsClassSerializer, ReadonlyModelSerializer, ReadonlyModelWithNameSerializer, \
    ReadonlyNamedModelSerializer
from poms.currencies.fields import CurrencyField
from poms.currencies.models import CurrencyHistory
from poms.currencies.serializers import CurrencyHistorySerializer
from poms.instruments.fields import InstrumentTypeField, InstrumentAttributeTypeField, InstrumentClassifierField
from poms.instruments.models import InstrumentAttributeType, PriceHistory
from poms.instruments.serializers import InstrumentAttributeSerializer, InstrumentSerializer, \
    AccrualCalculationScheduleSerializer, InstrumentFactorScheduleSerializer, PriceHistorySerializer
from poms.integrations.fields import InstrumentDownloadSchemeField, PriceDownloadSchemeField
from poms.integrations.models import InstrumentDownloadSchemeInput, InstrumentDownloadSchemeAttribute, \
    InstrumentDownloadScheme, ImportConfig, Task, ProviderClass, FactorScheduleDownloadMethod, \
    AccrualScheduleDownloadMethod, PriceDownloadScheme, CurrencyMapping, InstrumentTypeMapping, \
    InstrumentAttributeValueMapping, AccrualCalculationModelMapping, PeriodicityMapping, PricingAutomatedSchedule
from poms.integrations.providers.base import get_provider
from poms.integrations.storage import import_file_storage
from poms.integrations.tasks import download_pricing, download_instrument
from poms.obj_attrs.serializers import ReadOnlyAttributeTypeSerializer, ReadOnlyClassifierSerializer, \
    ModelWithAttributesSerializer, AbstractAttributeSerializer
from poms.obj_perms.serializers import ReadonlyNamedModelWithObjectPermissionSerializer
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


class ProviderClassSerializer(PomsClassSerializer):
    class Meta(PomsClassSerializer.Meta):
        model = ProviderClass


class FactorScheduleDownloadMethodSerializer(PomsClassSerializer):
    class Meta(PomsClassSerializer.Meta):
        model = FactorScheduleDownloadMethod


class AccrualScheduleDownloadMethodSerializer(PomsClassSerializer):
    class Meta(PomsClassSerializer.Meta):
        model = AccrualScheduleDownloadMethod


class ImportConfigSerializer(serializers.ModelSerializer):
    master_user = MasterUserField()
    provider_object = ReadonlyNamedModelSerializer(source='provider')
    p12cert = serializers.FileField(allow_null=True, allow_empty_file=False, write_only=True)
    password = serializers.CharField(allow_null=True, allow_blank=True, write_only=True)

    class Meta:
        model = ImportConfig
        fields = [
            'url', 'id', 'master_user', 'provider', 'provider_object', 'p12cert', 'password', 'has_p12cert',
            'has_password',
        ]


class InstrumentDownloadSchemeInputSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=False, required=False, allow_null=True)

    class Meta:
        model = InstrumentDownloadSchemeInput
        fields = ['id', 'name', 'field']


class InstrumentDownloadSchemeAttributeSerializer(AbstractAttributeSerializer):
    id = serializers.IntegerField(read_only=False, required=False, allow_null=True)
    attribute_type = InstrumentAttributeTypeField()
    attribute_type_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='attribute_type')
    value = ExpressionField(allow_blank=True)

    class Meta(AbstractAttributeSerializer.Meta):
        model = InstrumentDownloadSchemeAttribute
        attribute_type_model = InstrumentAttributeType
        fields = ['id', 'attribute_type', 'attribute_type_object', 'value']


class InstrumentDownloadSchemeSerializer(ModelWithAttributesSerializer):
    master_user = MasterUserField()
    provider_object = ReadonlyNamedModelSerializer(source='provider')

    inputs = InstrumentDownloadSchemeInputSerializer(many=True, read_only=False)

    user_code = ExpressionField(allow_blank=True)
    name = ExpressionField()
    short_name = ExpressionField(allow_blank=True)
    public_name = ExpressionField(allow_blank=True)
    notes = ExpressionField(allow_blank=True)
    instrument_type = ExpressionField(allow_blank=True)
    pricing_currency = ExpressionField(allow_blank=True)
    price_multiplier = ExpressionField(allow_blank=True)
    accrued_currency = ExpressionField(allow_blank=True)
    accrued_multiplier = ExpressionField(allow_blank=True)
    # daily_pricing_model = ExpressionField(allow_blank=True)
    # payment_size_detail = ExpressionField(allow_blank=True)
    # default_price = ExpressionField(allow_blank=True)
    # default_accrued = ExpressionField(allow_blank=True)
    user_text_1 = ExpressionField(allow_blank=True)
    user_text_2 = ExpressionField(allow_blank=True)
    user_text_3 = ExpressionField(allow_blank=True)
    # price_download_mode = ExpressionField(allow_blank=True)
    maturity_date = ExpressionField(allow_blank=True)

    payment_size_detail_object = ReadonlyModelWithNameSerializer(source='payment_size_detail')
    daily_pricing_model_object = ReadonlyModelWithNameSerializer(source='daily_pricing_model')
    price_download_scheme = PriceDownloadSchemeField()
    price_download_scheme_object = ReadonlyModelSerializer(source='price_download_scheme', fields=['scheme_name'])
    factor_schedule_method_object = ReadonlyModelWithNameSerializer(source='factor_schedule_method')
    accrual_calculation_schedule_method_object = ReadonlyModelWithNameSerializer(
        source='accrual_calculation_schedule_method')

    attributes = InstrumentDownloadSchemeAttributeSerializer(many=True, read_only=False)

    class Meta:
        model = InstrumentDownloadScheme
        fields = [
            'url', 'id', 'master_user', 'scheme_name', 'provider', 'provider_object', 'inputs',
            'reference_for_pricing', 'user_code', 'name', 'short_name', 'public_name', 'notes',
            'instrument_type', 'pricing_currency', 'price_multiplier', 'accrued_currency', 'accrued_multiplier',
            'user_text_1', 'user_text_2', 'user_text_3', 'maturity_date',
            'payment_size_detail', 'payment_size_detail_object',
            'daily_pricing_model', 'daily_pricing_model_object',
            'price_download_scheme', 'price_download_scheme_object',
            'default_price', 'default_accrued',
            'factor_schedule_method', 'factor_schedule_method_object',
            'accrual_calculation_schedule_method', 'accrual_calculation_schedule_method_object',
            'attributes',
        ]

    def create(self, validated_data):
        inputs = validated_data.pop('inputs', None) or []
        # attributes = validated_data.pop('attributes', None) or []
        instance = super(InstrumentDownloadSchemeSerializer, self).create(validated_data)
        self.save_inputs(instance, inputs)
        # self.save_attributes(instance, attributes)
        return instance

    def update(self, instance, validated_data):
        inputs = validated_data.pop('inputs', None) or []
        # attributes = validated_data.pop('attributes', None) or []
        instance = super(InstrumentDownloadSchemeSerializer, self).update(instance, validated_data)
        self.save_inputs(instance, inputs)
        # self.save_attributes(instance, attributes)
        return instance

    def save_inputs(self, instance, inputs):
        pk_set = set()
        for input_values in inputs:
            input_id = input_values.pop('id', None)
            input0 = None
            if input_id:
                try:
                    input0 = instance.inputs.get(pk=input_id)
                except ObjectDoesNotExist:
                    pass
            if input0 is None:
                input0 = InstrumentDownloadSchemeInput(scheme=instance)
            for name, value in input_values.items():
                setattr(input0, name, value)
            input0.save()
            pk_set.add(input0.id)
        instance.inputs.exclude(pk__in=pk_set).delete()

        # def save_attributes(self, instance, attributes):
        #     pk_set = set()
        #     for attr_values in attributes:
        #         attribute_type = attr_values['attribute_type']
        #         try:
        #             attr = instance.attributes.get(attribute_type=attribute_type)
        #         except ObjectDoesNotExist:
        #             attr = None
        #         if attr is None:
        #             attr = InstrumentDownloadSchemeAttribute(scheme=instance)
        #         for name, value in attr_values.items():
        #             setattr(attr, name, value)
        #         attr.save()
        #         pk_set.add(attr.id)
        #     instance.attributes.exclude(pk__in=pk_set).delete()


class PriceDownloadSchemeSerializer(serializers.ModelSerializer):
    master_user = MasterUserField()
    provider_object = ReadonlyNamedModelSerializer(source='provider')

    class Meta:
        model = PriceDownloadScheme
        fields = [
            'url', 'id', 'master_user', 'scheme_name', 'provider', 'provider_object',
            'bid0', 'bid1', 'bid2', 'bid_multiplier', 'ask0', 'ask1', 'ask2', 'ask_multiplier', 'last',
            'last_multiplier', 'mid', 'mid_multiplier',
            'bid_history', 'bid_history_multiplier', 'ask_history', 'ask_history_multiplier', 'mid_history',
            'mid_history_multiplier', 'last_history', 'last_history_multiplier',
            'currency_fxrate', 'currency_fxrate_multiplier',
        ]


class CurrencyMappingSerializer(serializers.ModelSerializer):
    master_user = MasterUserField()
    provider_object = ReadonlyNamedModelSerializer(source='provider')
    currency = CurrencyField()
    currency_object = ReadonlyNamedModelSerializer(source='currency')

    class Meta:
        model = CurrencyMapping
        fields = [
            'url', 'id', 'master_user', 'provider', 'provider_object', 'value', 'currency', 'currency_object',
        ]


class InstrumentTypeMappingSerializer(serializers.ModelSerializer):
    master_user = MasterUserField()
    provider_object = ReadonlyNamedModelSerializer(source='provider')
    instrument_type = InstrumentTypeField()
    instrument_type_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='instrument_type')

    class Meta:
        model = InstrumentTypeMapping
        fields = [
            'url', 'id', 'master_user', 'provider', 'provider_object', 'value', 'instrument_type',
            'instrument_type_object',
        ]


class InstrumentAttributeValueMappingSerializer(serializers.ModelSerializer):
    master_user = MasterUserField()
    provider_object = ReadonlyNamedModelSerializer(source='provider')
    attribute_type = InstrumentAttributeTypeField()
    attribute_type_object = ReadOnlyAttributeTypeSerializer(source='attribute_type', read_only=True)
    classifier = InstrumentClassifierField(allow_empty=True, allow_null=True)
    classifier_object = ReadOnlyClassifierSerializer(source='classifier', read_only=True)

    class Meta:
        model = InstrumentAttributeValueMapping
        fields = [
            'url', 'id', 'master_user', 'provider', 'provider_object', 'value',
            'attribute_type', 'attribute_type_object', 'value_string', 'value_float', 'value_date',
            'classifier', 'classifier_object',
        ]

    def validate(self, attrs):
        attribute_type = attrs.get('attribute_type')
        classifier = attrs.get('classifier', None)
        if classifier:
            if classifier.attribute_type_id != attribute_type.id:
                raise ValidationError({'classifier': 'Invalid classifier'})
        return attrs


class AccrualCalculationModelMappingSerializer(serializers.ModelSerializer):
    master_user = MasterUserField()
    provider_object = ReadonlyNamedModelSerializer(source='provider')
    accrual_calculation_model_object = ReadonlyNamedModelSerializer(source='accrual_calculation_model')

    class Meta:
        model = AccrualCalculationModelMapping
        fields = [
            'url', 'id', 'master_user', 'provider', 'provider_object', 'value', 'accrual_calculation_model',
            'accrual_calculation_model_object',
        ]


class PeriodicityMappingSerializer(serializers.ModelSerializer):
    master_user = MasterUserField()
    provider_object = ReadonlyNamedModelSerializer(source='provider')
    periodicity_object = ReadonlyNamedModelSerializer(source='periodicity')

    class Meta:
        model = PeriodicityMapping
        fields = [
            'url', 'id', 'master_user', 'provider', 'provider_object', 'value', 'periodicity', 'periodicity_object',
        ]


class TaskSerializer(serializers.ModelSerializer):
    master_user = MasterUserField()
    member = MemberField()
    provider_object = ReadonlyNamedModelSerializer(source='provider')
    is_yesterday = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            'url', 'id', 'master_user', 'member', 'provider', 'provider_object',
            'created', 'modified', 'status',
            'action',
            'is_yesterday',
            'parent', 'children',
            # 'options_object',
            # 'result_object',
        ]

    def get_is_yesterday(self, obj):
        if obj.action == Task.ACTION_PRICING:
            options = obj.options_object or {}
            return options.get('is_yesterday', None)
        return None


class PricingAutomatedScheduleSerializer(serializers.ModelSerializer):
    master_user = MasterUserField()
    last_run_at = DateTimeTzAwareField()
    next_run_at = DateTimeTzAwareField()

    class Meta:
        model = PricingAutomatedSchedule
        fields = [
            'url', 'id', 'master_user',
            'is_enabled', 'cron_expr', 'balance_day', 'load_days', 'fill_days', 'override_existed',
            'last_run_at', 'next_run_at', 'last_run_task',
        ]
        read_only_fields = ['last_run_at', 'next_run_at', 'last_run_task']


class ImportFileInstrumentSerializer(serializers.Serializer):
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
            import_file_storage.save(tmp_file_name, file)

            from poms.integrations.tasks import schedule_file_import_delete
            schedule_file_import_delete(tmp_file_name)

        with import_file_storage.open(tmp_file_name, 'rt') as f:
            # ret = []
            # import csv
            # for row in csv.reader(f):
            #     ret.append(row)
            #     data['preview'] = ret
            pass

        return validated_data

    def get_file_path(self, owner, token):
        return '%s/%s/%s' % (owner.pk, token[0:4], token)


class InstrumentMiniSerializer(InstrumentSerializer):
    accrual_calculation_schedules = serializers.SerializerMethodField()
    factor_schedules = serializers.SerializerMethodField()
    attributes = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        super(InstrumentMiniSerializer, self).__init__(*args, **kwargs)
        self.fields.pop('manual_pricing_formulas')
        # self.fields.pop('accrual_calculation_schedules')
        # self.fields.pop('factor_schedules')
        self.fields.pop('event_schedules')
        self.fields.pop('tags')
        self.fields.pop('tags_object')
        # self.fields.pop('attributes')
        self.fields.pop('granted_permissions')
        self.fields.pop('user_object_permissions', None)
        self.fields.pop('group_object_permissions', None)

    def get_accrual_calculation_schedules(self, obj):
        if hasattr(obj, '_accrual_calculation_schedules'):
            l = obj._accrual_calculation_schedules
        else:
            l = obj.accrual_calculation_schedules.all()
        return AccrualCalculationScheduleSerializer(instance=l, many=True, read_only=True).data

    def get_factor_schedules(self, obj):
        if hasattr(obj, '_factor_schedules'):
            l = obj._factor_schedules
        else:
            l = obj.factor_schedules.all()
        return InstrumentFactorScheduleSerializer(instance=l, many=True, read_only=True).data

    def get_attributes(self, obj):
        if hasattr(obj, '_attributes'):
            l = obj._attributes
        else:
            l = obj.attributes.all()
        return InstrumentAttributeSerializer(instance=l, many=True, read_only=True).data


class ImportInstrumentEntry(object):
    def __init__(self, master_user=None, member=None, instrument_code=None, instrument_download_scheme=None,
                 task=None, task_result_overrides=None, instrument=None, errors=None):
        self.master_user = master_user
        self.member = member
        self.instrument_code = instrument_code
        self.instrument_download_scheme = instrument_download_scheme
        self.task = task
        self._task_object = None
        self.task_result_overrides = task_result_overrides
        self.instrument = instrument
        self.errors = errors

    @property
    def task_object(self):
        if not self._task_object and self.task:
            self._task_object = self.master_user.tasks.get(pk=self.task)
        return self._task_object

    @task_object.setter
    def task_object(self, value):
        self._task_object = value
        self.task = getattr(value, 'pk', None)


class ImportInstrumentSerializer(serializers.Serializer):
    master_user = MasterUserField()
    member = HiddenMemberField()
    instrument_download_scheme = InstrumentDownloadSchemeField()
    instrument_code = serializers.CharField(required=True, initial='USP16394AG62 Corp')

    task = serializers.IntegerField(required=False, allow_null=True)
    task_object = TaskSerializer(read_only=True)
    task_result = serializers.SerializerMethodField()
    task_result_overrides = serializers.JSONField(default={}, allow_null=True)

    instrument = InstrumentMiniSerializer(read_only=True)
    errors = serializers.ReadOnlyField()

    def validate(self, attrs):
        master_user = attrs['master_user']
        instrument_download_scheme = attrs['instrument_download_scheme']
        instrument_code = attrs['instrument_code']
        provider = get_provider(master_user=master_user, provider=instrument_download_scheme.provider_id)
        if not provider.is_valid_reference(instrument_code):
            raise ValidationError(
                {'instrument_code': 'Invalid value for provider %s' % instrument_download_scheme.provider.name})

        task_result_overrides = attrs.get('task_result_overrides', None) or {}
        if isinstance(task_result_overrides, str):
            try:
                task_result_overrides = json.loads(task_result_overrides)
            except ValueError:
                raise ValidationError({'task_result_overrides': 'Invalid JSON string'})
        if not isinstance(task_result_overrides, dict):
            raise ValidationError({'task_result_overrides': 'Invalid value'})
        task_result_overrides = {k: v for k, v in task_result_overrides.items()
                                 if k in instrument_download_scheme.fields}
        attrs['task_result_overrides'] = task_result_overrides
        return attrs

    def create(self, validated_data):
        task_result_overrides = validated_data.get('task_result_overrides', None)
        instance = ImportInstrumentEntry(**validated_data)
        if instance.task:
            task, instrument, errors = download_instrument(
                # instrument_code=instance.instrument_code,
                # instrument_download_scheme=instance.instrument_download_scheme,
                # master_user=instance.master_user,
                # member=instance.member,
                task=instance.task_object,
                value_overrides=task_result_overrides
            )
            instance.task_object = task
            instance.instrument = instrument
            instance.errors = errors
        else:
            task, instrument, errors = download_instrument(
                instrument_code=instance.instrument_code,
                instrument_download_scheme=instance.instrument_download_scheme,
                master_user=instance.master_user,
                member=instance.member
            )
            instance.task_object = task
            instance.instrument = instrument
            instance.errors = errors
        return instance

    def get_task_result(self, obj):
        if obj.task_object.status == Task.STATUS_DONE:
            fields = obj.task_object.options_object['fields']
            result_object = obj.task_object.result_object
            return {k: v for k, v in result_object.items() if k in fields}
        return {}


class ImportPricingEntry(object):
    def __init__(self, master_user=None, member=None,
                 instruments=None, currencies=None,
                 date_from=None, date_to=None, is_yesterday=None,
                 balance_date=None, fill_days=None, override_existed=False,
                 task=None, instrument_histories=None, currency_histories=None):
        self.master_user = master_user
        self.member = member
        self.instruments = instruments
        self.currencies = currencies

        self.date_from = date_from
        self.date_to = date_to
        self.is_yesterday = is_yesterday
        self.balance_date = balance_date
        self.fill_days = fill_days
        self.override_existed = override_existed

        self.task = task
        self._task_object = None
        self.instrument_histories = instrument_histories
        self.currency_histories = currency_histories

    @property
    def task_object(self):
        if not self._task_object and self.task:
            self._task_object = self.master_user.tasks.get(pk=self.task)
        return self._task_object

    @task_object.setter
    def task_object(self, value):
        self._task_object = value
        self.task = getattr(value, 'pk', None)

    @property
    def errors(self):
        t = self.task_object
        if t:
            return t.options_object.get('errors', None)
        return None

    @property
    def instrument_price_missed(self):
        if not self.is_yesterday:
            return []
        result = getattr(self.task_object, 'result_object', {})
        instrument_price_missed = result.get('instrument_price_missed', None)
        if instrument_price_missed:
            instruments_pk = [instr_id for instr_id, _ in instrument_price_missed]
            existed_instrument_prices = {
                (p.instrument_id, p.pricing_policy_id): p
                for p in PriceHistory.objects.filter(instrument__in=instruments_pk, date=self.date_to)
                }

            instrument_price_missed_objects = []
            for instrument_id, pricing_policy_id in instrument_price_missed:
                op = existed_instrument_prices.get((instrument_id, pricing_policy_id), None)
                if op is None:
                    op = PriceHistory(instrument_id=instrument_id, pricing_policy_id=pricing_policy_id,
                                      date=self.date_to)
                instrument_price_missed_objects.append(op)
            return instrument_price_missed_objects
        return []

    @property
    def currency_price_missed(self):
        if not self.is_yesterday:
            return []
        result = getattr(self.task_object, 'result_object', {})
        currency_price_missed = result.get('currency_price_missed', None)
        if currency_price_missed:
            currencies_pk = [instr_id for instr_id, _ in currency_price_missed]
            existed_currency_prices = {
                (p.currency_id, p.pricing_policy_id): p
                for p in CurrencyHistory.objects.filter(currency__in=currencies_pk, date=self.date_to)
                }
            currency_price_missed_objects = []
            for currency_id, pricing_policy_id in currency_price_missed:
                op = existed_currency_prices.get((currency_id, pricing_policy_id), None)
                if op is None:
                    op = CurrencyHistory(currency_id=currency_id, pricing_policy_id=pricing_policy_id,
                                         date=self.date_to)
                currency_price_missed_objects.append(op)
            return currency_price_missed_objects
        return []


class ImportPricingSerializer(serializers.Serializer):
    master_user = MasterUserField()
    member = HiddenMemberField()

    date_from = serializers.DateField(allow_null=True, required=False)
    date_to = serializers.DateField(allow_null=True, required=False)
    is_yesterday = serializers.BooleanField(read_only=True)
    balance_date = serializers.DateField(allow_null=True, required=False)
    fill_days = serializers.IntegerField(initial=0, default=0, min_value=0)
    override_existed = serializers.BooleanField()

    task = serializers.IntegerField(required=False, allow_null=True)
    task_object = TaskSerializer(read_only=True)

    errors = serializers.ReadOnlyField()
    instrument_price_missed = PriceHistorySerializer(read_only=True, many=True)
    currency_price_missed = CurrencyHistorySerializer(read_only=True, many=True)

    def validate(self, attrs):
        attrs = super(ImportPricingSerializer, self).validate(attrs)

        yesterday = timezone.now().date() - timedelta(days=1)

        date_from = attrs.get('date_from', yesterday) or yesterday
        date_to = attrs.get('date_to', yesterday) or yesterday
        if date_from > date_to:
            raise ValidationError({
                'date_from': 'Invalid date range',
                'date_to': 'Invalid date range',
            })

        balance_date = attrs.get('balance_date', date_to) or date_to
        is_yesterday = (date_from == yesterday) and (date_to == yesterday)

        attrs['date_from'] = date_from
        attrs['date_to'] = date_to
        attrs['balance_date'] = balance_date
        attrs['is_yesterday'] = is_yesterday
        attrs['fill_days'] = attrs.get('fill_days', 0) if is_yesterday else 0

        return attrs

    def create(self, validated_data):
        instance = ImportPricingEntry(**validated_data)

        if instance.task:
            task, is_ready = download_pricing(
                master_user=instance.master_user,
                fill_days=instance.fill_days,
                override_existed=instance.override_existed,
                task=instance.task_object
            )
            instance.task_object = task
        else:
            task, is_ready = download_pricing(
                master_user=instance.master_user,
                member=instance.member,
                date_from=instance.date_from,
                date_to=instance.date_to,
                is_yesterday=instance.is_yesterday,
                balance_date=instance.balance_date,
                fill_days=instance.fill_days,
                override_existed=instance.override_existed
            )
            instance.task_object = task
        return instance
