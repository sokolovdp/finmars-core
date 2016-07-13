import os
import uuid

from django.conf import settings
from django.core import signing
from django.core.files.storage import FileSystemStorage
from django.utils.functional import SimpleLazyObject
from rest_framework import status, serializers
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from poms.common.utils import date_now
from poms.common.views import AbstractViewSet
from poms.instruments.fields import InstrumentTypeField
from poms.integrations.tasks import delete_temp_file

import_storage = SimpleLazyObject(lambda: FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, "import")))


class ImportSerializer(serializers.Serializer):
    is_preview = serializers.BooleanField()

    data = serializers.FileField(required=False, allow_null=True)
    data_key = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    format = serializers.ChoiceField(choices=(('csv', 'CSV'),), initial='csv')
    skip_first_line = serializers.BooleanField()
    delimiter = serializers.CharField(max_length=1, initial=',')
    quotechar = serializers.CharField(max_length=1, initial='|')
    encoding = serializers.CharField(max_length=10, initial='utf-8')
    mapping = serializers.DictField(required=False)
    preview = serializers.JSONField(read_only=True)

    instrument_type = InstrumentTypeField(required=False, allow_null=True)

    def create(self, validated_data):
        print('create: validated_data=%s' % (validated_data,))
        return validated_data


class AbstractImportViewSet(AbstractViewSet):
    serializer_class = ImportSerializer

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        kwargs['context'] = self.get_serializer_context()
        return serializer_class(*args, **kwargs)

    def get_serializer_class(self):
        return self.serializer_class

    def get_serializer_context(self):
        return {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self
        }

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.data
        print(data)
        if data.get('data_key', '') == '':
            file = request.data['data']
            if not file:
                raise ValidationError({'data': 'data is required'})
            tmp_file_name = '%s' % (uuid.uuid4().hex)
            delete_temp_file(tmp_file_name)
            data['data_key'] = signing.TimestampSigner().sign(tmp_file_name)
            import_storage.save(tmp_file_name, file)
        else:
            tmp_file_name = data.get('data_key')
            tmp_file_name = signing.TimestampSigner().unsign(tmp_file_name)

            import csv

            with import_storage.open(tmp_file_name, 'rt') as f:
                ret = []
                for row in csv.reader(f):
                    ret.append(row)
                data['preview'] = ret

        return Response(data, status=status.HTTP_200_OK)


class BloombergSerializer(serializers.Serializer):
    begin_date = serializers.DateField(default=date_now)
    end_date = serializers.DateField(default=date_now)


class BloombergInstrumentViewSet(AbstractViewSet):
    serializer_class = BloombergSerializer

    def list(self, request, *args, **kwargs):
        return Response()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)
