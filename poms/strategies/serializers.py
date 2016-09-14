from __future__ import unicode_literals

from rest_framework import serializers

from poms.common.serializers import ModelWithUserCodeSerializer
from poms.obj_perms.serializers import ModelWithObjectPermissionSerializer, AbstractBulkObjectPermissionSerializer
from poms.strategies.fields import Strategy1GroupField, Strategy1SubgroupField, Strategy2GroupField, \
    Strategy2SubgroupField, Strategy3GroupField, Strategy3SubgroupField, Strategy1Field, Strategy2Field, Strategy3Field
from poms.strategies.models import Strategy1Group, Strategy1Subgroup, Strategy1, Strategy2Group, Strategy2Subgroup, \
    Strategy2, Strategy3Group, Strategy3Subgroup, Strategy3
from poms.tags.fields import TagField
from poms.users.fields import MasterUserField


class Strategy1GroupSerializer(ModelWithObjectPermissionSerializer, ModelWithUserCodeSerializer):
    master_user = MasterUserField()
    tags = TagField(many=True, required=False, allow_null=True)

    class Meta:
        model = Strategy1Group
        fields = [
            'url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'public_name', 'notes', 'is_deleted', 'tags'
        ]


class Strategy1GroupBulkObjectPermissionSerializer(AbstractBulkObjectPermissionSerializer):
    content_objects = Strategy1GroupField(many=True, allow_null=False, allow_empty=False)

    class Meta:
        model = Strategy1Group


class Strategy1SubgroupSerializer(ModelWithObjectPermissionSerializer, ModelWithUserCodeSerializer):
    master_user = MasterUserField()
    group = Strategy1GroupField()
    tags = TagField(many=True, required=False, allow_null=True)

    class Meta:
        model = Strategy1Subgroup
        fields = [
            'url', 'id', 'master_user', 'group', 'user_code', 'name', 'short_name', 'public_name', 'is_deleted',
            'notes', 'tags'
        ]


class Strategy1SubgroupBulkObjectPermissionSerializer(AbstractBulkObjectPermissionSerializer):
    content_objects = Strategy1SubgroupField(many=True, allow_null=False, allow_empty=False)

    class Meta:
        model = Strategy1Subgroup


class Strategy1Serializer(ModelWithObjectPermissionSerializer, ModelWithUserCodeSerializer):
    master_user = MasterUserField()
    group = serializers.SerializerMethodField()
    subgroup = Strategy1SubgroupField()
    tags = TagField(many=True, required=False, allow_null=True)

    class Meta:
        model = Strategy1
        fields = [
            'url', 'id', 'master_user', 'group', 'subgroup', 'user_code', 'name', 'short_name', 'public_name',
            'notes', 'is_deleted', 'tags'
        ]

    def get_group(self, obj):
        subgroup = getattr(obj, 'subgroup', None)
        group = getattr(subgroup, 'group', None)
        return getattr(group, 'id', None)


class Strategy1BulkObjectPermissionSerializer(AbstractBulkObjectPermissionSerializer):
    content_objects = Strategy1Field(many=True, allow_null=False, allow_empty=False)

    class Meta:
        model = Strategy1


# 2

class Strategy2GroupSerializer(Strategy1GroupSerializer):
    class Meta(Strategy1GroupSerializer.Meta):
        model = Strategy2Group


class Strategy2GroupBulkObjectPermissionSerializer(AbstractBulkObjectPermissionSerializer):
    content_objects = Strategy2GroupField(many=True, allow_null=False, allow_empty=False)

    class Meta:
        model = Strategy2Group


class Strategy2SubgroupSerializer(Strategy1SubgroupSerializer):
    group = Strategy2GroupField()

    class Meta(Strategy1SubgroupSerializer.Meta):
        model = Strategy2Subgroup


class Strategy2SubgroupBulkObjectPermissionSerializer(AbstractBulkObjectPermissionSerializer):
    content_objects = Strategy2SubgroupField(many=True, allow_null=False, allow_empty=False)

    class Meta:
        model = Strategy2Group


class Strategy2Serializer(Strategy1Serializer):
    subgroup = Strategy2SubgroupField()

    class Meta(Strategy1Serializer.Meta):
        model = Strategy2


class Strategy2BulkObjectPermissionSerializer(AbstractBulkObjectPermissionSerializer):
    content_objects = Strategy2Field(many=True, allow_null=False, allow_empty=False)

    class Meta:
        model = Strategy2


# 3

class Strategy3GroupSerializer(Strategy1GroupSerializer):
    class Meta(Strategy1GroupSerializer.Meta):
        model = Strategy3Group


class Strategy3GroupBulkObjectPermissionSerializer(AbstractBulkObjectPermissionSerializer):
    content_objects = Strategy3GroupField(many=True, allow_null=False, allow_empty=False)

    class Meta:
        model = Strategy3Group


class Strategy3SubgroupSerializer(Strategy1SubgroupSerializer):
    group = Strategy3GroupField()

    class Meta(Strategy1SubgroupSerializer.Meta):
        model = Strategy3Subgroup


class Strategy3SubgroupBulkObjectPermissionSerializer(AbstractBulkObjectPermissionSerializer):
    content_objects = Strategy3SubgroupField(many=True, allow_null=False, allow_empty=False)

    class Meta:
        model = Strategy3Subgroup


class Strategy3Serializer(Strategy1Serializer):
    subgroup = Strategy3SubgroupField()

    class Meta(Strategy1Serializer.Meta):
        model = Strategy3


class Strategy3BulkObjectPermissionSerializer(AbstractBulkObjectPermissionSerializer):
    content_objects = Strategy3Field(many=True, allow_null=False, allow_empty=False)

    class Meta:
        model = Strategy3
