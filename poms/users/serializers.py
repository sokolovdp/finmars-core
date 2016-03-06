from __future__ import unicode_literals

from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.models import User
from django.utils import translation
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from rest_framework.authtoken.serializers import AuthTokenSerializer

from poms.users.models import MasterUser, Employee, PrivateGroup


class LoginSerializer(AuthTokenSerializer):
    pass


class RegisterSerializer(AuthTokenSerializer):
    username = serializers.CharField(required=True, max_length=30)
    password = serializers.CharField(required=True, max_length=128, style={'input_type': 'password'})

    def create(self, validated_data):
        username = validated_data.get('username')
        password = validated_data.get('password')

        user_model = get_user_model()

        if user_model.objects.filter(username=username).exists():
            msg = _('User already exist.')
            raise serializers.ValidationError(msg)

        user = user_model.objects.create_user(username=username, password=password)
        master_user = MasterUser.objects.create(user=user, language=translation.get_language())

        user = authenticate(username=username, password=password)

        validated_data['user'] = user
        return validated_data


class PasswordChangeSerializer(serializers.Serializer):
    original_password = serializers.CharField(required=True, max_length=128, style={'input_type': 'password'})
    new_password = serializers.CharField(required=True, max_length=128, style={'input_type': 'password'})

    def create(self, validated_data):
        # password = validated_data.get('password')
        # user.set_password()
        return validated_data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'is_active']

    def create(self, validated_data):
        return super(UserSerializer, self).create(validated_data)


class MasterUserSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(max_length=30, allow_null=False, allow_blank=True)
    last_name = serializers.CharField(max_length=30, allow_null=False, allow_blank=True)

    class Meta:
        model = MasterUser
        fields = ['first_name', 'last_name', 'currency', 'language', 'timezone']

    def update(self, instance, validated_data):
        if 'first_name' in validated_data or 'last_name' in validated_data:
            first_name = validated_data.pop('first_name', None)
            last_name = validated_data.pop('last_name', None)
        else:
            first_name = None
            last_name = None
        instance = super(MasterUserSerializer, self).update(instance, validated_data)
        if first_name is not None or last_name is not None:
            if first_name:
                instance.user.first_name = first_name
            if last_name:
                instance.user.last_name = last_name
            instance.user.save(update_fields=['first_name', 'last_name'])
        return instance


class EmployeeSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(max_length=30, allow_null=False, allow_blank=True)
    last_name = serializers.CharField(max_length=30, allow_null=False, allow_blank=True)

    class Meta:
        model = Employee
        fields = ['first_name', 'last_name', 'language', 'timezone']

    def create(self, validated_data):
        return super(EmployeeSerializer, self).create(validated_data)


class PrivateGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrivateGroup
        fields = ['name']

    def create(self, validated_data):
        return super(PrivateGroupSerializer, self).create(validated_data)
