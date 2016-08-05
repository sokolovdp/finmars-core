from rest_framework import serializers


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
