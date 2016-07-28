from __future__ import unicode_literals, print_function

import uuid
from logging import getLogger

import six
from django.core.cache import caches
from django.core.exceptions import ObjectDoesNotExist
from django.core.signing import TimestampSigner, BadSignature
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from poms.instruments.fields import InstrumentTypeField, InstrumentAttributeTypeField
from poms.instruments.serializers import InstrumentSerializer
from poms.integrations.fields import InstrumentMappingField
from poms.integrations.models import InstrumentMapping, InstrumentAttributeMapping, BloombergConfig, BloombergTask
from poms.integrations.storages import FileImportStorage
from poms.integrations.tasks import schedule_file_import_delete, bloomberg_instrument
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
    cert = serializers.FileField(allow_null=True, allow_empty_file=False, write_only=True)
    key = serializers.FileField(allow_null=True, allow_empty_file=False, write_only=True)

    class Meta:
        model = BloombergConfig
        fields = ['url', 'id', 'master_user', 'p12cert', 'password', 'cert', 'key',
                  'has_p12cert', 'has_password', 'has_cert', 'has_key']


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
    def __init__(self, master_user=None, member=None, mapping=None, mode=None, code=None, industry=None, task_id=None,
                 instrument=None):
        self.master_user = master_user
        self.member = member
        self.mapping = mapping
        self.mode = mode
        self.code = code
        self.industry = industry
        self.task_id = task_id
        self._task = None
        self.instrument = instrument

    @property
    def task(self):
        if self.task_id:
            self._task = self.master_user.bloomberg_tasks.get(pk=self.task_id)
        return self._task


class InstrumentBloombergImportSerializer(serializers.Serializer):
    master_user = MasterUserField()
    member = HiddenMemberField()
    mapping = InstrumentMappingField()
    mode = serializers.ChoiceField(choices=IMPORT_MODE_CHOICES)
    code = serializers.CharField(required=False, allow_null=True, allow_blank=True, initial='XS1433454243')
    industry = serializers.CharField(required=False, allow_null=True, allow_blank=True, initial='Corp')
    task_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    task = BloombergTaskSerializer(read_only=True)
    instrument = InstrumentSerializer(read_only=True)

    def create(self, validated_data):
        instance = InstrumentBloombergImport(**validated_data)
        if not instance.task_id:
            instance.task_id = bloomberg_instrument(
                master_user=instance.master_user, member=instance.member,
                instrument={
                    'code': instance.code,
                    'industry': instance.industry,
                },
                fields=list(instance.mapping.mapping_fields))

        if instance.task.status == BloombergTask.STATUS_DONE:
            values = instance.task.result_object
            if instance.mode == IMPORT_PREVIEW:
                instance.instrument = instance.mapping.create_instrument(values, preview=True)
            else:
                pass

        return instance

        # def update(self, instance, validated_data):
        #     instance = InstrumentBloombergImport(**validated_data)
        #
        #     for attr, value in validated_data.items():
        #         setattr(instance, attr, value)
        #
        #     return instance
