import uuid
from logging import getLogger

from django.core.cache import caches
from django.core.signing import TimestampSigner, BadSignature
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from poms.instruments.fields import InstrumentTypeField
from poms.integrations.storages import FileImportStorage
from poms.integrations.tasks import schedule_file_import_delete
from poms.users.fields import MasterUserField

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
