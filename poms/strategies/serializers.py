from __future__ import unicode_literals

from poms.common.serializers import ModelWithUserCodeSerializer
from poms.obj_perms.serializers import ModelWithObjectPermissionSerializer
from poms.strategies.fields import Strategy1GroupField, Strategy1SubgroupField, Strategy2GroupField, \
    Strategy2SubgroupField, Strategy3GroupField, Strategy3SubgroupField
from poms.strategies.models import Strategy1Group, Strategy1Subgroup, Strategy1, Strategy2Group, Strategy2Subgroup, \
    Strategy2, Strategy3Group, Strategy3Subgroup, Strategy3
from poms.tags.serializers import ModelWithTagSerializer
from poms.users.fields import MasterUserField


class Strategy1GroupSerializer(ModelWithObjectPermissionSerializer, ModelWithUserCodeSerializer,
                               ModelWithTagSerializer):
    master_user = MasterUserField()

    # tags = TagField(many=True, required=False, allow_null=True)
    # tags_object = TagViewSerializer(source='tags', many=True, read_only=True)

    class Meta:
        model = Strategy1Group
        fields = [
            'url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'public_name', 'notes', 'is_deleted',
            # 'tags', 'tags_object'
        ]


class Strategy1GroupViewSerializer(ModelWithObjectPermissionSerializer):
    class Meta:
        model = Strategy1Group
        fields = [
            'url', 'id', 'user_code', 'name', 'short_name', 'public_name', 'notes', 'is_deleted',
        ]


class Strategy1SubgroupSerializer(ModelWithObjectPermissionSerializer, ModelWithUserCodeSerializer,
                                  ModelWithTagSerializer):
    master_user = MasterUserField()
    group = Strategy1GroupField()
    group_object = Strategy1GroupViewSerializer(source='group', read_only=True)

    # tags = TagField(many=True, required=False, allow_null=True)
    # tags_object = TagViewSerializer(source='tags', many=True, read_only=True)

    class Meta:
        model = Strategy1Subgroup
        fields = [
            'url', 'id', 'master_user', 'group', 'group_object', 'user_code', 'name', 'short_name', 'public_name',
            'is_deleted', 'notes',
            # 'tags', 'tags_object',
        ]


class Strategy1SubgroupViewSerializer(ModelWithObjectPermissionSerializer):
    group_object = Strategy1GroupViewSerializer(source='group', read_only=True)

    class Meta:
        model = Strategy1Subgroup
        fields = [
            'url', 'id', 'group', 'group_object', 'user_code', 'name', 'short_name', 'public_name',
            'is_deleted', 'notes',
        ]


class Strategy1Serializer(ModelWithObjectPermissionSerializer, ModelWithUserCodeSerializer, ModelWithTagSerializer):
    master_user = MasterUserField()
    subgroup = Strategy1SubgroupField()
    subgroup_object = Strategy1SubgroupViewSerializer(source='subgroup', read_only=True)

    # tags = TagField(many=True, required=False, allow_null=True)
    # tags_object = TagViewSerializer(source='tags', many=True, read_only=True)

    class Meta:
        model = Strategy1
        fields = [
            'url', 'id', 'master_user', 'subgroup', 'subgroup_object', 'user_code', 'name', 'short_name',
            'public_name', 'notes', 'is_deleted',
            # 'tags', 'tags_object'
        ]


class Strategy1ViewSerializer(ModelWithObjectPermissionSerializer):
    subgroup_object = Strategy1SubgroupViewSerializer(source='subgroup', read_only=True)

    class Meta:
        model = Strategy1
        fields = [
            'url', 'id', 'subgroup', 'subgroup_object', 'user_code', 'name', 'short_name',
            'public_name', 'notes', 'is_deleted',
        ]


# 2 --------------------------------------------------------------------------------------------------------------------

class Strategy2GroupSerializer(Strategy1GroupSerializer):
    class Meta(Strategy1GroupSerializer.Meta):
        model = Strategy2Group


class Strategy2GroupViewSerializer(Strategy1GroupViewSerializer):
    class Meta(Strategy1GroupViewSerializer.Meta):
        model = Strategy2Group


class Strategy2SubgroupSerializer(Strategy1SubgroupSerializer):
    group = Strategy2GroupField()
    group_object = Strategy2GroupViewSerializer(source='group', read_only=True)

    class Meta(Strategy1SubgroupSerializer.Meta):
        model = Strategy2Subgroup


class Strategy2SubgroupViewSerializer(Strategy1SubgroupViewSerializer):
    group = Strategy2GroupField()
    group_object = Strategy2GroupViewSerializer(source='group', read_only=True)

    class Meta(Strategy1SubgroupViewSerializer.Meta):
        model = Strategy2Subgroup


class Strategy2Serializer(Strategy1Serializer):
    subgroup = Strategy2SubgroupField()
    subgroup_object = Strategy2SubgroupViewSerializer(source='subgroup', read_only=True)

    class Meta(Strategy1Serializer.Meta):
        model = Strategy2


class Strategy2ViewSerializer(Strategy1ViewSerializer):
    subgroup_object = Strategy2SubgroupViewSerializer(source='subgroup', read_only=True)

    class Meta(Strategy1ViewSerializer.Meta):
        model = Strategy2


# 3 --------------------------------------------------------------------------------------------------------------------


class Strategy3GroupSerializer(Strategy1GroupSerializer):
    class Meta(Strategy1GroupSerializer.Meta):
        model = Strategy3Group


class Strategy3GroupViewSerializer(Strategy1GroupViewSerializer):
    class Meta(Strategy1GroupViewSerializer.Meta):
        model = Strategy3Group


class Strategy3SubgroupSerializer(Strategy1SubgroupSerializer):
    group = Strategy3GroupField()
    group_object = Strategy3GroupViewSerializer(source='group', read_only=True)

    class Meta(Strategy1SubgroupSerializer.Meta):
        model = Strategy3Subgroup


class Strategy3SubgroupViewSerializer(Strategy1SubgroupViewSerializer):
    group = Strategy3GroupField()
    group_object = Strategy3GroupViewSerializer(source='group', read_only=True)

    class Meta(Strategy1SubgroupViewSerializer.Meta):
        model = Strategy3Subgroup


class Strategy3Serializer(Strategy1Serializer):
    subgroup = Strategy3SubgroupField()
    subgroup_object = Strategy3SubgroupViewSerializer(source='subgroup', read_only=True)

    class Meta(Strategy1Serializer.Meta):
        model = Strategy3


class Strategy3ViewSerializer(Strategy1ViewSerializer):
    subgroup_object = Strategy3SubgroupViewSerializer(source='subgroup', read_only=True)

    class Meta(Strategy1ViewSerializer.Meta):
        model = Strategy3
