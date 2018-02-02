from django.db import IntegrityError
from django.contrib.contenttypes.models import ContentType
from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.status import HTTP_201_CREATED
from .serializers import DataImportSerializer, DataImportSchemaSerializer, DataImportSchemaFieldsSerializer, \
    DataImportSchemaModelsSerializer, DataImportSchemaMatchingSerializer
from .models import DataImport, DataImportSchema, DataImportSchemaFields, DataImportSchemaMatching
from .options import PUBLIC_FIELDS
from poms.obj_attrs.models import GenericAttributeType, GenericAttribute
from poms.users.models import MasterUser, Member
from rest_framework.status import HTTP_201_CREATED
from .utils import return_csv_file, split_csv_str
import io
import csv


class DataImportViewSet(viewsets.ModelViewSet):
    parser_classes = (MultiPartParser,)
    queryset = DataImport.objects.all()
    serializer_class = DataImportSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        f = csv.DictReader(io.TextIOWrapper(request.data['files'].file))
        schema = DataImportSchema.objects.get(pk=request.data['schema'])
        fields = schema.dataimportschemafields_set.all()
        data = {}
        for row in f:
            values = split_csv_str(row.values())
            if values:
                for field in fields:
                    matchings_field = field.dataimportschemamatching_set.all()
                    data = {matching_field.model_field: values[field.num] for matching_field in matchings_field}
                if data:
                    data['master_user_id'] = Member.objects.get(user=self.request.user).master_user.id
                    try:
                        accepted_data = {key: data.get(key) for key in PUBLIC_FIELDS[schema.model.model]}
                        o = schema.model.model_class()(**accepted_data)
                        o.save()
                    except IntegrityError:
                        continue
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=HTTP_201_CREATED, headers=headers)


class DataImportSchemaViewSet(viewsets.ModelViewSet):
    queryset = DataImportSchema.objects.all()
    serializer_class = DataImportSchemaSerializer


class DataImportSchemaFieldsViewSet(viewsets.ModelViewSet):
    queryset = DataImportSchemaFields.objects.all()
    serializer_class = DataImportSchemaFieldsSerializer

    def create(self, request, *args, **kwargs):
        for i in request.data['field_list']:
            serializer = self.get_serializer(data=i)
            if i.get('id', None):
                serializer.instance = self.queryset.get(id=i['id'])
                for m in request.data['matching_list']:
                    if m.get('expression'):
                        DataImportSchemaMatching(field=serializer.instance,
                                                 model_field=m['model_field'],
                                                 expression=m['expression']).save()
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
        return Response(status=HTTP_201_CREATED)


class DataImportSchemaModelsViewSet(viewsets.ModelViewSet):
    queryset = ContentType.objects.filter(model='portfolio')
    serializer_class = DataImportSchemaModelsSerializer

    @detail_route(methods=['get'])
    def fields(self, request, pk=None):
        obj = self.get_object()
        base_fields = list(map(lambda f: {'model_field': f, 'expression': ''}, PUBLIC_FIELDS[obj.model]))
        master_user = Member.objects.get(user=self.request.user).master_user
        all_attr_fields = GenericAttributeType.objects.filter(master_user=master_user, content_type=obj)
        additional_fields = []
        for attr_fields in all_attr_fields:
            additional_fields.append({'model_field': attr_fields.name, 'expression': ''})
        return Response({'results': base_fields + additional_fields})


class DataImportSchemaMatchingViewSet(viewsets.ModelViewSet):
    queryset = DataImportSchemaMatching.objects.all()
    serializer_class = DataImportSchemaMatchingSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        schema = DataImportSchema.objects.get(pk=self.request.query_params.get('schema_id'))
        base_fields = list(map(lambda f: {'model_field': f, 'expression': ''}, PUBLIC_FIELDS[schema.model.name]))
        master_user = Member.objects.get(user=self.request.user).master_user
        all_attr_fields = GenericAttributeType.objects.filter(master_user=master_user, content_type=schema.model)
        additional_fields = []
        for attr_fields in all_attr_fields:
            additional_fields.append({'model_field': attr_fields.name, 'expression': ''})
        all_fields = base_fields + additional_fields
        for f in serializer.data:
            if f['expression']:
                for i, item in enumerate(all_fields):
                    if f['model_field'] == item['model_field']:
                        all_fields[i] = f
        return Response(all_fields)


    @list_route(methods=['get'])
    def fields(self, request, pk=None):
        obj = self.get_object()
        base_fields = list(map(lambda f: {'model_field': f, 'expression': ''}, PUBLIC_FIELDS[obj.model]))
        master_user = Member.objects.get(user=self.request.user).master_user
        all_attr_fields = GenericAttributeType.objects.filter(master_user=master_user, content_type=obj)
        additional_fields = []
        for attr_fields in all_attr_fields:
            additional_fields.append({'field': attr_fields.name, 'expression': ''})
        return Response({'results': base_fields + additional_fields})