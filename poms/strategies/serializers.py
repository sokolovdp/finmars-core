from __future__ import unicode_literals

from poms.common.serializers import ModelWithUserCodeSerializer
from poms.obj_perms.serializers import ModelWithObjectPermissionSerializer
from poms.strategies.fields import Strategy1GroupField, Strategy1SubgroupField, Strategy2GroupField, \
    Strategy2SubgroupField, Strategy3GroupField, Strategy3SubgroupField
from poms.strategies.models import Strategy1Group, Strategy1Subgroup, Strategy1, Strategy2Group, Strategy2Subgroup, \
    Strategy2, Strategy3Group, Strategy3Subgroup, Strategy3
from poms.tags.fields import TagField
from poms.users.fields import MasterUserField


class Strategy1GroupSerializer(ModelWithObjectPermissionSerializer, ModelWithUserCodeSerializer):
    master_user = MasterUserField()
    tags = TagField(many=True, required=False, allow_null=True)

    class Meta:
        model = Strategy1Group
        fields = ['url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'public_name', 'notes', 'tags']


class Strategy1SubgroupSerializer(ModelWithObjectPermissionSerializer, ModelWithUserCodeSerializer):
    group = Strategy1GroupField()
    tags = TagField(many=True, required=False, allow_null=True)

    class Meta:
        model = Strategy1Subgroup
        fields = ['url', 'id', 'group', 'user_code', 'name', 'short_name', 'public_name', 'notes', 'tags']


class Strategy1Serializer(ModelWithObjectPermissionSerializer, ModelWithUserCodeSerializer):
    subgroup = Strategy1SubgroupField()
    tags = TagField(many=True, required=False, allow_null=True)

    class Meta:
        model = Strategy1
        fields = ['url', 'id', 'subgroup', 'user_code', 'name', 'short_name', 'public_name', 'notes', 'tags']


# 2

class Strategy2GroupSerializer(Strategy1GroupSerializer):
    class Meta(Strategy1GroupSerializer.Meta):
        model = Strategy2Group


class Strategy2SubgroupSerializer(Strategy1SubgroupSerializer):
    group = Strategy2GroupField()

    class Meta(Strategy1SubgroupSerializer.Meta):
        model = Strategy2Subgroup


class Strategy2Serializer(Strategy1Serializer):
    subgroup = Strategy2SubgroupField()

    class Meta(Strategy1Serializer.Meta):
        model = Strategy2


# 3

class Strategy3GroupSerializer(Strategy1GroupSerializer):
    class Meta(Strategy1GroupSerializer.Meta):
        model = Strategy3Group


class Strategy3SubgroupSerializer(Strategy1SubgroupSerializer):
    group = Strategy3GroupField()

    class Meta(Strategy1SubgroupSerializer.Meta):
        model = Strategy3Subgroup


class Strategy3Serializer(Strategy1Serializer):
    subgroup = Strategy3SubgroupField()

    class Meta(Strategy1Serializer.Meta):
        model = Strategy3
