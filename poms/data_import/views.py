from django.db import IntegrityError
# from django.shortcuts import render
# from django.contrib import messages
# from django.forms.models import inlineformset_factory
# from django.urls import reverse_lazy
# from django.http import HttpResponseRedirect
# from .models import DataImport, DataImportSchema
# from .forms import DataImportForm, DataImportSchemaForm, ListTextWidget
# from .utils import return_csv_file, split_csv_str
# from django.views.generic import CreateView, UpdateView, FormView

#
#
# class ImportMixin(FormView):
#     model = DataImport
#     form_class = DataImportForm
#     template_name = 'import_form.html'
#
#
# class ImportCreate(ImportMixin, CreateView):
#     form_set = inlineformset_factory(DataImport, DataImportSchema, form=DataImportSchemaForm, extra=0)
#
#     def form_valid_formset(self, *args):
#         for formset in args:
#             if formset.is_valid():
#                 formset.save(commit=False)
#                 for obj in formset.deleted_objects:
#                     obj.delete()
#                 formset.save()
#             else:
#                 pass
#         return HttpResponseRedirect(self.get_success_url())
#
#     def form_invalid_formset(self, *args):
#         return self.render_to_response(self.get_context_data(**dict((a, a) for a in args)))
#
#     def get(self, request, *args, **kwargs):
#         self.object = None
#         form_class = self.form_class
#         form = self.get_form(form_class)
#         return self.render_to_response(
#             self.get_context_data(form=form, schema_form=self.form_set(instance=form.instance))
#         )
#
#     def post(self, request, *args, **kwargs):
#         form = self.get_form(self.form_class)
#         if form.is_valid():
#             self.object = form.save()
#             schema_form = self.form_set(self.request.POST, instance=self.object)
#             return self.form_valid_formset(schema_form)
#         else:
#             return self.form_invalid(form)
#
#     def get_success_url(self):
#         return reverse_lazy('import_change', kwargs={'pk': self.object.id})
#
#     def get_initial(self):
#         master_user = Member.objects.get(user=self.request.user).master_user.id
#
#         return {
#             'master_user': master_user
#         }
#
#
# class ImportUpdate(ImportMixin, UpdateView):
#     # def __init__(self, **kwargs):
#     #     super(ImportUpdate, self).__init__(**kwargs)
#     #     self.object = self.get_object()
#
#
#     @property
#     def csv_file(self):
#         self.object = self.get_object()
#         return return_csv_file(self.object.file.file.file)
#
#     @property
#     def fields(self):
#         return split_csv_str(self.csv_file.fieldnames)
#
#     @property
#     def form_set(self):
#         choices = list(map(lambda f: f.column, self.get_object()._meta.fields))
#
#         return inlineformset_factory(DataImport,
#                                      DataImportSchema,
#                                      form=DataImportSchemaForm,
#                                      extra=len(self.fields),
#                                      can_delete=False,
#                                      widgets={'target': ListTextWidget(data_list=choices, name='target')}
#                                      )
#
#     def form_valid_formset(self, *args):
#         for formset in args[2]:
#             if formset.is_valid():
#                 formset.save()
#             else:
#                 pass
#         try:
#             self.object.save()
#         except IntegrityError as e:
#             messages.add_message(args[0], messages.ERROR, e)
#             return render(args[0],
#                           template_name=self.template_name,
#                           context=self.get_context_data(form=args[1], schema_form=args[2])
#                           )
#         return HttpResponseRedirect(self.get_success_url())
#
#     def form_invalid_formset(self, *args):
#         return self.render_to_response(self.get_context_data(**dict((a, a) for a in args)))
#
#     def get(self, request, *args, **kwargs):
#         self.object = self.get_object()
#         form_class = self.form_class
#         form = self.get_form(form_class)
#         schema_formset = self.form_set(initial=[{'source': f} for f in self.fields])
#         return self.render_to_response(
#             self.get_context_data(form=form, schema_form=schema_formset)
#         )
#
#     def post(self, request, *args, **kwargs):
#         self.object = self.get_object()
#         form = self.get_form(self.form_class)
#         schema_form = self.form_set(self.request.POST, instance=self.object)
#         if form.is_valid():
#             return self.form_valid_formset(request, form, schema_form)
#         else:
#             return self.form_invalid(form)
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
                        o = schema.model.model_class()(**data)
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