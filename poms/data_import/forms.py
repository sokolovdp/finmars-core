from django import forms
from .models import DataImport, DataImportSchema
from django.contrib.contenttypes.models import ContentType


class DataImportForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(DataImportForm, self).__init__(*args, **kwargs)
        self.fields['model'].queryset = ContentType.objects.filter(model__in=['portfolio'])
        self.fields['master_user'].widget = forms.HiddenInput()

    class Meta:
        model = DataImport
        fields = ['model', 'file', 'master_user']


class DataImportSchemaForm(forms.ModelForm):
    class Meta:
        model = DataImportSchema
        fields = '__all__'
