from rest_framework import serializers

from poms.common import formula
from poms.common.fields import ExpressionField


class Language(object):
    def __init__(self, code='', name=''):
        self.code = code
        self.name = name

    def __str__(self):
        return '{}: {}'.format(self.code, self.name)


class LanguageSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=2)
    name = serializers.CharField(max_length=50)

    def create(self, validated_data):
        return Language(**validated_data)

    def update(self, instance, validated_data):
        instance.code = validated_data.get('code', instance.code)
        instance.name = validated_data.get('name', instance.name)
        return instance


class Timezone(object):
    def __init__(self, code='', name='', offset=0):
        self.code = code
        self.name = name
        self.offset = offset

    def __str__(self):
        return '{}: {}'.format(self.code, self.name)


class TimezoneSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=2)
    name = serializers.CharField(max_length=50)

    def create(self, validated_data):
        return Timezone(**validated_data)

    def update(self, instance, validated_data):
        instance.code = validated_data.get('code', instance.code)
        instance.name = validated_data.get('name', instance.name)
        return instance


class ExpressionSerializer(serializers.Serializer):
    expression = ExpressionField(required=True)
    names = serializers.DictField(required=False, allow_null=True)
    is_eval = serializers.BooleanField()
    result = serializers.ReadOnlyField()
    help = serializers.SerializerMethodField()

    def validate(self, attrs):
        expression = attrs['expression']
        names = attrs.get('names', None)
        is_eval = attrs.get('is_eval', False)
        if is_eval:
            attrs['result'] = formula.safe_eval(expression, names)
        return attrs

    def get_help(self, obj):
        return formula.HELP.split('\n')
