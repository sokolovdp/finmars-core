from django.db import IntegrityError
from django.shortcuts import render
from django.contrib import messages
from django.forms.models import inlineformset_factory, formset_factory
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect
from .models import DataImport, DataImportSchema
from .forms import DataImportForm, DataImportSchemaForm
from .utils import return_csv_file, split_csv_str
from django.views.generic import CreateView, UpdateView, FormView


class ImportMixin(FormView):
    model = DataImport
    form_class = DataImportForm
    template_name = 'import_form.html'


class ImportCreate(ImportMixin, CreateView):
    form_set = inlineformset_factory(DataImport, DataImportSchema, form=DataImportSchemaForm, extra=0)

    def form_valid_formset(self, *args):
        for formset in args:
            if formset.is_valid():
                formset.save(commit=False)
                for obj in formset.deleted_objects:
                    obj.delete()
                formset.save()
            else:
                pass
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid_formset(self, *args):
        return self.render_to_response(self.get_context_data(**dict((a, a) for a in args)))

    def get(self, request, *args, **kwargs):
        self.object = None
        form_class = self.form_class
        form = self.get_form(form_class)
        return self.render_to_response(
            self.get_context_data(form=form, schema_form=self.form_set(instance=form.instance))
        )

    def post(self, request, *args, **kwargs):
        form = self.get_form(self.form_class)
        self.object = form.save()
        schema_form = self.form_set(self.request.POST, instance=self.object)
        if form.is_valid():
            return self.form_valid_formset(schema_form)
        else:
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('import_change', kwargs={'pk': self.object.id})

    def get_initial(self):
        return {
            'master_user': self.request.user
        }


class ImportUpdate(ImportMixin, UpdateView):
    @property
    def csv_file(self):
        self.object = self.get_object()
        return return_csv_file(self.object.file.file.file)

    @property
    def fields(self):
        return split_csv_str(self.csv_file.fieldnames)

    @property
    def form_set(self):
        return inlineformset_factory(DataImport,
                                     DataImportSchema,
                                     form=DataImportSchemaForm,
                                     extra=len(self.fields),
                                     can_delete=False
                                     )

    def form_valid_formset(self, *args):
        for formset in args[2]:
            if formset.is_valid():
                formset.save()
            else:
                pass
        try:
            self.object.save()
        except IntegrityError as e:
            messages.add_message(args[0], messages.ERROR, e)
            return render(args[0],
                          template_name=self.template_name,
                          context=self.get_context_data(form=args[1], schema_form=args[2])
                          )
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid_formset(self, *args):
        return self.render_to_response(self.get_context_data(**dict((a, a) for a in args)))

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.form_class
        form = self.get_form(form_class)
        schema_formset = self.form_set(initial=[{'source': f} for f in self.fields])
        return self.render_to_response(
            self.get_context_data(form=form, schema_form=schema_formset)
        )

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form(self.form_class)
        schema_form = self.form_set(self.request.POST, instance=self.object)
        if form.is_valid():
            return self.form_valid_formset(request, form, schema_form)
        else:
            return self.form_invalid(form)