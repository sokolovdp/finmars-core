from __future__ import unicode_literals

from django.conf import settings
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.utils import translation
from django.utils.translation import ugettext_lazy
from rest_framework import serializers
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.fields import empty

from poms.accounts.fields import AccountTypeField, AccountField
from poms.chats.fields import ThreadGroupField
from poms.common.fields import DateTimeTzAwareField
from poms.counterparties.fields import CounterpartyField, ResponsibleField, CounterpartyGroupField, \
    ResponsibleGroupField
from poms.currencies.fields import CurrencyField
from poms.instruments.fields import InstrumentTypeField
from poms.portfolios.fields import PortfolioField
from poms.strategies.fields import Strategy1Field, Strategy2Field, Strategy3Field, Strategy1SubgroupField, \
    Strategy1GroupField, Strategy2GroupField, Strategy2SubgroupField, Strategy3GroupField, Strategy3SubgroupField
from poms.users.fields import MasterUserField, MemberField, GroupField
from poms.users.models import MasterUser, UserProfile, Group, Member, TIMEZONE_CHOICES
from poms.users.utils import get_user_from_context, get_master_user_from_context, get_member_from_context


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
        user = get_user_from_context(self.context)
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
        profile_data = validated_data.pop('profile', empty)

        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.email = validated_data.get('email', instance.email)
        instance.save()

        if profile_data is not empty:
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
        user = get_user_from_context(self.context)
        if not user.check_password(attrs['password']):
            raise serializers.ValidationError({'password': 'bad password'})
        return attrs

    def create(self, validated_data):
        user = get_user_from_context(self.context)
        user.set_password(validated_data['new_password'])
        return validated_data

    def update(self, instance, validated_data):
        return self.create(validated_data)


class UserUnsubscribeSerializer(serializers.Serializer):
    email = serializers.EmailField(allow_null=False, allow_blank=False, required=True, write_only=True)

    def validate(self, attrs):
        user = get_user_from_context(self.context)
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
    currency_object = serializers.PrimaryKeyRelatedField(source='currency', read_only=True)
    account_type = AccountTypeField()
    account_type_object = serializers.PrimaryKeyRelatedField(source='account_type', read_only=True)
    account = AccountField()
    account_object = serializers.PrimaryKeyRelatedField(source='account', read_only=True)
    counterparty_group = CounterpartyGroupField()
    counterparty_group_object = serializers.PrimaryKeyRelatedField(source='counterparty_group', read_only=True)
    counterparty = CounterpartyField()
    counterparty_object = serializers.PrimaryKeyRelatedField(source='counterparty', read_only=True)
    responsible_group = ResponsibleGroupField()
    responsible_group_object = serializers.PrimaryKeyRelatedField(source='responsible_group', read_only=True)
    responsible = ResponsibleField()
    responsible_object = serializers.PrimaryKeyRelatedField(source='responsible', read_only=True)
    instrument_type = InstrumentTypeField()
    instrument_type_object = serializers.PrimaryKeyRelatedField(source='instrument_type', read_only=True)
    portfolio = PortfolioField()
    portfolio_object = serializers.PrimaryKeyRelatedField(source='portfolio', read_only=True)
    strategy1_group = Strategy1GroupField()
    strategy1_group_object = serializers.PrimaryKeyRelatedField(source='strategy1_group', read_only=True)
    strategy1_subgroup = Strategy1SubgroupField()
    strategy1_subgroup_object = serializers.PrimaryKeyRelatedField(source='strategy1_subgroup', read_only=True)
    strategy1 = Strategy1Field()
    strategy1_object = serializers.PrimaryKeyRelatedField(source='strategy1', read_only=True)
    strategy2_group = Strategy2GroupField()
    strategy2_group_object = serializers.PrimaryKeyRelatedField(source='strategy2_group', read_only=True)
    strategy2_subgroup = Strategy2SubgroupField()
    strategy2_subgroup_object = serializers.PrimaryKeyRelatedField(source='strategy2_subgroup', read_only=True)
    strategy2 = Strategy2Field()
    strategy2_object = serializers.PrimaryKeyRelatedField(source='strategy2', read_only=True)
    strategy3_group = Strategy3GroupField()
    strategy3_group_object = serializers.PrimaryKeyRelatedField(source='strategy3_group', read_only=True)
    strategy3_subgroup = Strategy3SubgroupField()
    strategy3_subgroup_object = serializers.PrimaryKeyRelatedField(source='strategy3_subgroup', read_only=True)
    strategy3 = Strategy3Field()
    strategy3_object = serializers.PrimaryKeyRelatedField(source='strategy3', read_only=True)
    thread_group = ThreadGroupField()
    thread_group_object = serializers.PrimaryKeyRelatedField(source='thread_group', read_only=True)

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

    def __init__(self, *args, **kwargs):
        super(MasterUserSerializer, self).__init__(*args, **kwargs)

        from poms.currencies.serializers import CurrencyViewSerializer
        self.fields['currency_object'] = CurrencyViewSerializer(source='currency', read_only=True)

        from poms.accounts.serializers import AccountTypeViewSerializer, AccountViewSerializer
        self.fields['account_type_object'] = AccountTypeViewSerializer(source='account_type', read_only=True)
        self.fields['account_object'] = AccountViewSerializer(source='account', read_only=True)

        from poms.counterparties.serializers import CounterpartyGroupViewSerializer, CounterpartyViewSerializer, ResponsibleGroupViewSerializer, ResponsibleViewSerializer
        self.fields['counterparty_group_object'] = CounterpartyGroupViewSerializer(source='counterparty_group', read_only=True)
        self.fields['counterparty_object'] = CounterpartyViewSerializer(source='counterparty', read_only=True)
        self.fields['responsible_group_object'] = ResponsibleGroupViewSerializer(source='responsible_group', read_only=True)
        self.fields['responsible_object'] = ResponsibleViewSerializer(source='responsible', read_only=True)

        from poms.instruments.serializers import InstrumentTypeViewSerializer
        self.fields['instrument_type_object'] = InstrumentTypeViewSerializer(source='instrument_type', read_only=True)

        from poms.portfolios.serializers import PortfolioViewSerializer
        self.fields['portfolio_object'] = PortfolioViewSerializer(source='portfolio', read_only=True)

        from poms.strategies.serializers import Strategy1GroupViewSerializer, Strategy1SubgroupViewSerializer,\
            Strategy1ViewSerializer,Strategy2GroupViewSerializer, Strategy2SubgroupViewSerializer, \
            Strategy2ViewSerializer, Strategy3GroupViewSerializer, Strategy3SubgroupViewSerializer, Strategy3ViewSerializer
        self.fields['strategy1_group_object'] = Strategy1GroupViewSerializer(source='strategy1_group', read_only=True)
        self.fields['strategy1_subgroup_object'] = Strategy1SubgroupViewSerializer(source='strategy1_subgrou', read_only=True)
        self.fields['strategy1_object'] = Strategy1ViewSerializer(source='strategy1', read_only=True)
        self.fields['strategy2_group_object'] = Strategy2GroupViewSerializer(source='strategy2_group', read_only=True)
        self.fields['strategy2_subgroup_object'] = Strategy2SubgroupViewSerializer(source='strategy2_subgroup', read_only=True)
        self.fields['strategy2_object'] = Strategy2ViewSerializer(source='strategy2', read_only=True)
        self.fields['strategy3_group_object'] = Strategy3GroupViewSerializer(source='strategy3_group', read_only=True)
        self.fields['strategy3_subgroup_object'] = Strategy3SubgroupViewSerializer(source='strategy3_subgroup', read_only=True)
        self.fields['strategy3_object'] = Strategy3ViewSerializer(source='strategy3', read_only=True)

        from poms.chats.serializers import ThreadGroupViewSerializer
        self.fields['thread_group_object'] = ThreadGroupViewSerializer(source='thread_group', read_only=True)


    def to_representation(self, instance):
        ret = super(MasterUserSerializer, self).to_representation(instance)
        is_current = self.get_is_current(instance)
        if not is_current:
            for k in list(ret.keys()):
                if k not in ['url', 'id', 'name', 'is_current']:
                    ret.pop(k)
        return ret

    def get_is_current(self, obj):
        master_user = get_master_user_from_context(self.context)
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
        member = get_member_from_context(self.context)
        return obj.id == member.id


class MemberSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='member-detail')
    master_user = MasterUserField()
    is_current = serializers.SerializerMethodField()
    join_date = DateTimeTzAwareField()
    groups = GroupField(many=True)
    groups_object = serializers.PrimaryKeyRelatedField(source='groups', read_only=True, many=True)

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

    def __init__(self, *args, **kwargs):
        super(MemberSerializer, self).__init__(*args, **kwargs)

        self.fields['groups_object'] = GroupViewSerializer(source='groups', many=True, read_only=True)

    def get_is_current(self, obj):
        member = get_member_from_context(self.context)
        return obj.id == member.id


class MemberViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = ['id', 'username', 'first_name', 'last_name', 'display_name', ]
        read_only_fields = ['id', 'username', 'first_name', 'last_name', 'display_name', ]

    def get_is_current(self, obj):
        member = get_member_from_context(self.context)
        return obj.id == member.id


class GroupSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='group-detail')
    master_user = MasterUserField()
    members = MemberField(many=True)
    members_object = serializers.PrimaryKeyRelatedField(source='members', read_only=True, many=True)

    class Meta:
        model = Group
        fields = ['url', 'id', 'master_user', 'name', 'members', 'members_object']

    def __init__(self, *args, **kwargs):
        super(GroupSerializer, self).__init__(*args, **kwargs)

        self.fields['members_object'] = MemberViewSerializer(source='members', many=True, read_only=True)


class GroupViewSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='group-detail')

    class Meta:
        model = Group
        fields = ['url', 'id', 'name']
