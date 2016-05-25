from __future__ import unicode_literals

from django.conf import settings
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.utils import translation
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from rest_framework.authtoken.serializers import AuthTokenSerializer

from poms.currencies.fields import CurrencyField
from poms.users.fields import MasterUserField, GroupField, UserField
from poms.users.models import MasterUser, UserProfile, Group, Member, TIMEZONE_CHOICES


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
    password = serializers.CharField(required=True, max_length=128, style={'input_type': 'password'})
    new_password = serializers.CharField(required=True, max_length=128, style={'input_type': 'password'})

    def create(self, validated_data):
        request = self.context['request']
        user = request.user
        password = validated_data['password']
        if user.check_password(password):
            new_password = validated_data['new_password']
            user.set_password(new_password)
            return validated_data
        raise PermissionDenied(_('Invalid password'))


class UserProfileSerializer(serializers.ModelSerializer):
    language = serializers.ChoiceField(choices=settings.LANGUAGES, default=settings.LANGUAGE_CODE)
    timezone = serializers.ChoiceField(choices=TIMEZONE_CHOICES)

    class Meta:
        model = UserProfile
        fields = ['language', 'timezone']


class UserSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='user-detail')
    groups = GroupField(many=True)  # TODO: filter groups in response JSON
    profile = UserProfileSerializer()

    class Meta:
        model = User
        fields = ['url', 'id', 'first_name', 'last_name', 'groups', 'profile']
        # read_only_fields = ['username', ]

    def create(self, validated_data):
        profile_data = validated_data.pop('profile')
        groups = validated_data.pop('groups')
        user = User.objects.create(**validated_data)
        user.groups = groups
        UserProfile.objects.create(user=user, **profile_data)
        return user

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile')
        profile = instance.profile

        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.save()

        if 'groups' in validated_data:
            request = self.context['request']
            # master_user = get_master_user(request)
            master_user = request.user.master_user

            cur_groups = set(instance.groups.filter(profile__master_user=master_user))
            new_groups = set(validated_data['groups'])

            add_groups = new_groups - cur_groups
            del_groups = cur_groups - new_groups

            if add_groups:
                instance.groups.add(*add_groups)
            if del_groups:
                instance.groups.remove(*del_groups)

                # instance.groups = validated_data.get('groups', instance.groups)

        profile.language = profile_data.get('language', profile.language)
        profile.timezone = profile_data.get('timezone', profile.timezone)
        profile.save()

        return instance


class MasterUserSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='masteruser-detail')
    currency = CurrencyField()
    language = serializers.ChoiceField(choices=settings.LANGUAGES, default=settings.LANGUAGE_CODE)
    timezone = serializers.ChoiceField(choices=TIMEZONE_CHOICES)
    is_current = serializers.SerializerMethodField()

    class Meta:
        model = MasterUser
        fields = ['url', 'id', 'name', 'currency', 'language', 'timezone', 'is_current']

    def get_is_current(self, obj):
        request = self.context['request']
        # master_user = get_master_user(request)
        master_user = request.user.master_user
        return obj.id == master_user.id


class MemberSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='member-detail')
    master_user = MasterUserField()
    # user = UserField(read_only=True)
    is_current = serializers.SerializerMethodField()

    class Meta:
        model = Member
        fields = ['url', 'id', 'master_user', 'user', 'is_owner', 'is_admin', 'join_date', 'is_current']
        read_only_fields = ['user', 'is_owner', 'join_date']

    def get_is_current(self, obj):
        request = self.context['request']
        # member = get_member(request)
        member = request.user.member
        return obj.id == member.id


class GroupSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='group-detail')
    master_user = MasterUserField()

    class Meta:
        model = Group
        fields = ['url', 'id', 'master_user', 'name']
