from __future__ import unicode_literals

from django.conf import settings
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.utils import translation
from django.utils.translation import ugettext_lazy
from rest_framework import serializers
from rest_framework.authtoken.serializers import AuthTokenSerializer

from poms.accounts.fields import AccountTypeField, AccountField
from poms.chats.fields import ThreadGroupField
from poms.common.fields import DateTimeTzAwareField
from poms.common.serializers import ReadonlyModelWithNameSerializer, ReadonlyModelSerializer, \
    ReadonlyNamedModelSerializer
from poms.counterparties.fields import CounterpartyField, ResponsibleField, CounterpartyGroupField, \
    ResponsibleGroupField
from poms.currencies.fields import CurrencyField
from poms.instruments.fields import InstrumentTypeField
from poms.obj_perms.serializers import ReadonlyNamedModelWithObjectPermissionSerializer
from poms.portfolios.fields import PortfolioField
from poms.strategies.fields import Strategy1Field, Strategy2Field, Strategy3Field, Strategy1SubgroupField, \
    Strategy1GroupField, Strategy2GroupField, Strategy2SubgroupField, Strategy3GroupField, Strategy3SubgroupField
from poms.users.fields import MasterUserField, MemberField, GroupField
from poms.users.models import MasterUser, UserProfile, Group, Member, TIMEZONE_CHOICES


class PingSerializer(serializers.Serializer):
    message = serializers.CharField(read_only=True)
    version = serializers.CharField(read_only=True)
    is_authenticated = serializers.BooleanField(read_only=True)
    is_anonymous = serializers.BooleanField(read_only=True)
    now = serializers.DateTimeField(read_only=True)


class LoginSerializer(AuthTokenSerializer):
    pass


class UserRegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=30, required=True)
    password = serializers.CharField(max_length=128, required=True, style={'input_type': 'password'})
    first_name = serializers.CharField(max_length=30, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=30, required=False, allow_blank=True)
    name = serializers.CharField(max_length=30, required=False, allow_blank=True)

    def create(self, validated_data):
        username = validated_data.get('username')
        password = validated_data.get('password')
        first_name = validated_data.get('first_name', '')
        last_name = validated_data.get('last_name', '')
        name = validated_data.get('last_name', '')
        name = name or ('%s %s' % (last_name, first_name))

        user_model = get_user_model()

        if user_model.objects.filter(username=username).exists():
            msg = ugettext_lazy('User already exist.')
            raise serializers.ValidationError(msg)

        user = user_model.objects.create_user(username=username, password=password,
                                              first_name=first_name, last_name=last_name)
        MasterUser.objects.create_master_user(user=user, name=name, language=translation.get_language())

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
        raise PermissionDenied(ugettext_lazy('Invalid password'))


class UserProfileSerializer(serializers.ModelSerializer):
    language = serializers.ChoiceField(choices=settings.LANGUAGES, default=settings.LANGUAGE_CODE)
    timezone = serializers.ChoiceField(choices=TIMEZONE_CHOICES)

    class Meta:
        model = UserProfile
        fields = ['language', 'timezone']


class UserSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='user-detail')
    profile = UserProfileSerializer()

    class Meta:
        model = User
        fields = ['url', 'id', 'username', 'first_name', 'last_name', 'email', 'profile']
        read_only_fields = ['username']

    def create(self, validated_data):
        # profile_data = validated_data.pop('profile', {})
        # user = User.objects.create(**validated_data)
        # user.profile.language = profile_data.get('language', settings.LANGUAGE_CODE)
        # user.profile.timezone = profile_data.get('timezone', settings.TIME_ZONE)
        # user.profile.save()
        # # UserProfile.objects.create(user=user, **profile_data)
        return None

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', None)

        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.email = validated_data.get('email', instance.email)
        instance.save()

        if profile_data:
            profile = instance.profile
            profile.language = profile_data.get('language', profile.language)
            profile.timezone = profile_data.get('timezone', profile.timezone)
            profile.save()

        return instance


class UserSetPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(allow_null=False, allow_blank=False, required=True, write_only=True,
                                     style={'input_type': 'password'})
    new_password = serializers.CharField(allow_null=False, allow_blank=False, required=True, write_only=True,
                                         style={'input_type': 'password'})

    def validate(self, attrs):
        user = self.context['request'].user
        if not user.check_password(attrs['password']):
            raise serializers.ValidationError({'password': 'bad password'})
        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        user.set_password(validated_data['new_password'])
        return validated_data

    def update(self, instance, validated_data):
        return self.create(validated_data)


class UserUnsubscribeSerializer(serializers.Serializer):
    email = serializers.EmailField(allow_null=False, allow_blank=False, required=True, write_only=True)

    def validate(self, attrs):
        user = self.context['request'].user
        if attrs['email'] != user.email:
            raise serializers.ValidationError({'email': 'Invalid email'})
        return attrs

    def create(self, validated_data):
        email = validated_data['email']
        return validated_data

    def update(self, instance, validated_data):
        return self.create(validated_data)


class MasterUserSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='masteruser-detail')
    language = serializers.ChoiceField(choices=settings.LANGUAGES, default=settings.LANGUAGE_CODE)
    timezone = serializers.ChoiceField(choices=TIMEZONE_CHOICES)
    is_current = serializers.SerializerMethodField()
    currency = CurrencyField()
    currency_object = ReadonlyNamedModelSerializer(source='currency')
    account_type = AccountTypeField()
    account_type_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='account_type')
    account = AccountField()
    account_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='account')
    counterparty_group = CounterpartyGroupField()
    counterparty_group_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='counterparty_group')
    counterparty = CounterpartyField()
    counterparty_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='counterparty')
    responsible_group = ResponsibleGroupField()
    responsible_group_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='responsible_group')
    responsible = ResponsibleField()
    responsible_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='responsible')
    instrument_type = InstrumentTypeField()
    instrument_type_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='instrument_type')
    portfolio = PortfolioField()
    portfolio_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='portfolio')
    strategy1_group = Strategy1GroupField()
    strategy1_group_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='strategy1_group')
    strategy1_subgroup = Strategy1SubgroupField()
    strategy1_subgroup_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='strategy1_subgroup')
    strategy1 = Strategy1Field()
    strategy1_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='strategy1')
    strategy2_group = Strategy2GroupField()
    strategy2_group_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='strategy2_group')
    strategy2_subgroup = Strategy2SubgroupField()
    strategy2_subgroup_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='strategy2_subgroup')
    strategy2 = Strategy2Field()
    strategy2_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='strategy2')
    strategy3_group = Strategy3GroupField()
    strategy3_group_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='strategy3_group')
    strategy3_subgroup = Strategy3SubgroupField()
    strategy3_subgroup_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='strategy3_subgroup')
    strategy3 = Strategy3Field()
    strategy3_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='strategy3')
    thread_group = ThreadGroupField()
    thread_group_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='thread_group')

    class Meta:
        model = MasterUser
        fields = [
            'url', 'id', 'name', 'is_current', 'language', 'timezone',
            'notification_business_days',
            'currency', 'currency_object',
            'account_type', 'account_type_object',
            'account', 'account_object',
            'counterparty_group', 'counterparty_group_object',
            'counterparty', 'counterparty_object',
            'responsible_group', 'responsible_group_object',
            'responsible', 'responsible_object',
            'instrument_type', 'instrument_type_object',
            'portfolio', 'portfolio_object',
            'strategy1_group', 'strategy1_group_object',
            'strategy1_subgroup', 'strategy1_subgroup_object',
            'strategy1', 'strategy1_object',
            'strategy2_group', 'strategy2_group_object',
            'strategy2_subgroup', 'strategy2_subgroup_object',
            'strategy2', 'strategy2_object',
            'strategy3_group', 'strategy3_group_object',
            'strategy3_subgroup', 'strategy3_subgroup_object',
            'strategy3', 'strategy3_object',
            'thread_group', 'thread_group_object',
        ]

    def to_representation(self, instance):
        ret = super(MasterUserSerializer, self).to_representation(instance)
        is_current = self.get_is_current(instance)
        if not is_current:
            for k in list(ret.keys()):
                if k not in ['url', 'id', 'name', 'is_current']:
                    ret.pop(k)
        return ret

    def get_is_current(self, obj):
        request = self.context['request']
        # master_user = get_master_user(request)
        master_user = request.user.master_user
        return obj.id == master_user.id


class MasterUserSetCurrentSerializer(serializers.Serializer):
    def create(self, validated_data):
        return validated_data

    def update(self, instance, validated_data):
        return self.create(validated_data)


class MemberMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = ['id', 'username', 'first_name', 'last_name', 'display_name', ]
        read_only_fields = ['id', 'username', 'first_name', 'last_name', 'display_name', ]

    def get_is_current(self, obj):
        member = self.context['request'].user.member
        return obj.id == member.id


class MemberSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='member-detail')
    master_user = MasterUserField()
    is_current = serializers.SerializerMethodField()
    join_date = DateTimeTzAwareField()
    groups = GroupField(many=True)
    groups_object = ReadonlyModelWithNameSerializer(source='groups', many=True)

    class Meta:
        model = Member
        fields = [
            'url', 'id', 'master_user', 'join_date', 'is_owner', 'is_admin', 'is_superuser', 'is_current',
            'is_deleted', 'username', 'first_name', 'last_name', 'display_name', 'email', 'groups', 'groups_object'
        ]
        read_only_fields = [
            'master_user', 'join_date', 'is_owner', 'is_superuser', 'is_current', 'is_deleted',
            'username', 'first_name', 'last_name', 'display_name', 'email',
        ]

    def get_is_current(self, obj):
        member = self.context['request'].user.member
        return obj.id == member.id


class GroupSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='group-detail')
    master_user = MasterUserField()
    members = MemberField(many=True)
    members_object = ReadonlyModelSerializer(source='members',
                                             fields=['username', 'first_name', 'last_name', 'display_name'], many=True)

    class Meta:
        model = Group
        fields = ['url', 'id', 'master_user', 'name', 'members', 'members_object']
