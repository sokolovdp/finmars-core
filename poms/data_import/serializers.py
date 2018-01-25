from rest_framework import serializers
from .models import DataImport, DataImportSchema, DataImportSchemaFields


class DataImportSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataImport
        fields = '__all__'


class DataImportSchemaSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataImportSchema
        fields = '__all__'


class DataImportSchemaFieldsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataImportSchemaFields
        fields = '__all__'
