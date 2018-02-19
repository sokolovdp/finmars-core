import io
import csv
from dateutil.parser import parse
from django.db import IntegrityError
from django.db.models.base import ModelBase
from django.contrib.contenttypes.models import ContentType
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import detail_route
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.status import HTTP_201_CREATED, HTTP_500_INTERNAL_SERVER_ERROR
from poms.common.formula import safe_eval, InvalidExpression
from poms.obj_attrs.models import GenericAttributeType, GenericAttribute
from poms.users.models import Member
from poms.integrations.models import CounterpartyMapping, AccountMapping, ResponsibleMapping
from .serializers import DataImportSerializer, DataImportSchemaSerializer, DataImportSchemaFieldsSerializer, \
    DataImportSchemaModelsSerializer, DataImportSchemaMatchingSerializer, DataImportContentTypeSerializer
from .models import DataImport, DataImportSchema, DataImportSchemaFields, DataImportSchemaMatching
from .options import PUBLIC_FIELDS
from .utils import split_csv_str


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
        matchings_fields = DataImportSchemaMatching.objects.filter(schema=schema)
        data = {}
        raw_data = {}
        for row in f:
            values = split_csv_str(row.values())
            if values:
                for field in fields:
                    try:
                        raw_data[field.source] = values[field.num]
                    except IndexError:
                        pass
                for matching_field in matchings_fields:
                    try:
                        if raw_data.get(matching_field.expression):
                            data[matching_field.model_field] = raw_data.get(matching_field.expression)
                        else:
                            dict_row = {}
                            for field in fields:
                                if isinstance(values[field.num], str):
                                    dict_row[field.source] = '"' + values[field.num] + '"'
                                else:
                                    dict_row[field.source] = values[field.num]
                            expr = matching_field.expression.format(**dict_row)
                            data[matching_field.model_field] = safe_eval(expr)
                    except (IndexError, InvalidExpression):
                        pass
                if data:
                    try:
                        master_user_id = Member.objects.get(user=self.request.user).master_user.id
                        accepted_data = {}
                        additional_data = {}
                        relation_data = {}
                        accepted_data['master_user_id'] = master_user_id
                        for key in PUBLIC_FIELDS[schema.model.model]:
                            accepted_data[key] = data.get(key)
                        for k, v in accepted_data.copy().items():
                            if isinstance(k, ModelBase):
                                del accepted_data[k]
                                try:
                                    relation_data[k._meta.model_name] = CounterpartyMapping.objects.filter(value=data[k._meta.model_name])[0].content_object
                                except KeyError:
                                    continue
                            else:
                                accepted_data[k] = v
                        additional_keys = []
                        for item in data.keys():
                            if item not in accepted_data.keys() and len(item.split(':')) == 1:
                                additional_keys.append(item)
                        for k in additional_keys:
                            accepted_data[k] = data[k]

                        o, _ = schema.model.model_class().objects.get_or_create(**accepted_data)
                        for r in relation_data.keys():
                            o.counterparty_set(relation_data[r])
                        for additional_key in additional_keys:
                            attr_type = GenericAttributeType.objects.filter(user_code=additional_key).first()
                            attribute = GenericAttribute(content_object=o, attribute_type=attr_type)
                            if attr_type:
                                if attr_type.value_type == 40:
                                    attribute.value_date = parse(additional_data[additional_key])
                                elif attr_type.value_type == 10:
                                    attribute.value_string = additional_data[additional_key]
                                elif attr_type.value_type == 20:
                                    attribute.value_float = additional_data[additional_key]
                                else:
                                    pass
                                attribute.save()
                    except IntegrityError as e:
                        if int(request.data.get('error_handling')[0]):
                            continue
                        else:
                            return Response(e, status=HTTP_500_INTERNAL_SERVER_ERROR)
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
                        o, _ = DataImportSchemaMatching.objects.update_or_create(schema=serializer.instance.schema,
                                                                          model_field=m['model_field'],
                                                                          expression=m['expression'])
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
        return Response(status=HTTP_201_CREATED)


class DataImportSchemaModelsViewSet(viewsets.ModelViewSet):
    queryset = ContentType.objects.filter(model__in=[
        'accounttype',
        'counterparty',
        'currency',
        'instrument',
        'portfolio',
        'pricingpolicy',
        'responsible',
        'strategy1',
        'strategy2',
        'strategy3',

    ])
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
        base_fields = list(map(lambda f: {'model_field': f if isinstance(f, str) else f._meta.model_name, 'expression': '', 'related': False if isinstance(f, str) else True}, PUBLIC_FIELDS[schema.model.name]))
        master_user = Member.objects.get(user=self.request.user).master_user
        all_attr_fields = GenericAttributeType.objects.filter(master_user=master_user, content_type=schema.model)
        additional_fields = []
        for attr_fields in all_attr_fields:
            additional_fields.append({'model_field': attr_fields.name, 'expression': '', 'related': False})
        all_fields = base_fields + additional_fields
        for f in serializer.data:
            if f['expression']:
                for i, item in enumerate(all_fields):
                    if f['model_field'].split(':')[0] == item['model_field']:
                        f['related'] = item['related']
                        all_fields[i] = f
        return Response(all_fields)


class ContentTypeViewSet(viewsets.ModelViewSet):
    queryset = ContentType.objects.filter(app_label__in=[
        'accounts', 'counterparties', 'currencies', 'instruments', 'portfolios', 'strategies'
    ])
    serializer_class = DataImportContentTypeSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('id',)

    @detail_route(methods=['get'])
    def fields(self, request, pk=None):
        obj = self.get_object()
        model = obj.model_class()
        return Response({'results': [f.name for f in model._meta.fields]})
