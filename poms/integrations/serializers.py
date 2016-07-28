from __future__ import unicode_literals, print_function

import json
import uuid
from logging import getLogger

import six
from django.core.cache import caches
from django.core.exceptions import ObjectDoesNotExist
from django.core.signing import TimestampSigner, BadSignature
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from poms.instruments.fields import InstrumentTypeField, InstrumentAttributeTypeField
from poms.integrations.models import InstrumentMapping, InstrumentAttributeMapping, BloombergConfig, BloombergTask
from poms.integrations.storages import FileImportStorage
from poms.integrations.tasks import schedule_file_import_delete
from poms.users.fields import MasterUserField, MemberField

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

    kwargs = serializers.SerializerMethodField()
    result = serializers.SerializerMethodField()

    class Meta:
        model = BloombergTask
        fields = ['url', 'id', 'master_user', 'member', 'action', 'created', 'modified', 'status', 'kwargs', 'result']

    def get_kwargs(self, obj):
        if obj.kwargs:
            return json.loads(obj.kwargs)
        return None

    def get_result(self, obj):
        if obj.result:
            return json.loads(obj.result)
        return None


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


class InstrumentBloombergImportSerializer(serializers.Serializer):
    master_user = MasterUserField()
    mode = serializers.ChoiceField(choices=IMPORT_MODE_CHOICES)
    token = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    name = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    def get_import_cache_key(self, token):
        return 'import:%s' % token

    def create(self, validated_data):
        _l.info('BloombergInstrumentImportSerializer.create: %s', validated_data)

        if validated_data.get('token', None):
            try:
                token = TimestampSigner().unsign(validated_data['token'])
            except BadSignature:
                raise ValidationError({'token': 'Invalid value.'})

            cache_key = self.get_import_cache_key(token)
            bloomberg_token = bloomberg_cache.get(cache_key)
            _l.info('bloomberg_token.get: %s', bloomberg_token)
        else:
            name = validated_data['name']
            if not name:
                raise ValidationError({'name': 'This field is required.'})
            token = '%s' % (uuid.uuid4().hex,)
            validated_data['token'] = TimestampSigner().sign(token)

            cache_key = self.get_import_cache_key(token)
            bloomberg_token = '%s-%s' % (uuid.uuid4().hex, uuid.uuid1().hex)
            bloomberg_cache.set(cache_key, bloomberg_token, timeout=600)
            _l.info('bloomberg_token.set: %s', bloomberg_token)

        return validated_data
