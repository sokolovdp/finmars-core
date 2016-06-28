from __future__ import unicode_literals

from rest_framework import serializers

from poms.common.serializers import ClassifierSerializerBase, ClassifierNodeSerializerBase
from poms.obj_perms.serializers import ModelWithObjectPermissionSerializer
from poms.strategies.models import Strategy1, Strategy2, Strategy3
from poms.tags.fields import TagField
from poms.users.fields import MasterUserField


class StrategyBaseSerializer(ClassifierSerializerBase, ModelWithObjectPermissionSerializer):
    master_user = MasterUserField()
    tags = TagField(many=True, required=False, allow_null=True)

    class Meta(ClassifierSerializerBase.Meta):
        fields = ['url', 'master_user', ] + ClassifierSerializerBase.Meta.fields + ['tags', ]

    def to_representation(self, instance):
        ret = super(StrategyBaseSerializer, self).to_representation(instance)
        if not instance.is_root_node():
            ret.pop("url", None)
            ret.pop("granted_permissions", None)
            ret.pop("user_object_permissions", None)
            ret.pop("group_object_permissions", None)
        return ret

    def save_object_permission(self, instance, *args, **kwargs):
        if instance.is_root_node():
            super(StrategyBaseSerializer, self).save_object_permission(instance, *args, **kwargs)


class StrategyBaseNodeSerializer(ClassifierNodeSerializerBase, ModelWithObjectPermissionSerializer):
    tags = TagField(many=True, required=False, allow_null=True)

    class Meta(ClassifierNodeSerializerBase.Meta):
        fields = ClassifierNodeSerializerBase.Meta.fields + ['tags']

    def to_representation(self, instance):
        ret = super(StrategyBaseNodeSerializer, self).to_representation(instance)
        if not instance.is_root_node():
            ret.pop("granted_permissions", None)
            ret.pop("user_object_permissions", None)
            ret.pop("group_object_permissions", None)
        return ret

    def save_object_permission(self, instance, *args, **kwargs):
        if instance.is_root_node():
            super(StrategyBaseNodeSerializer, self).save_object_permission(*args, **kwargs)


class Strategy1Serializer(StrategyBaseSerializer):
    # url = serializers.HyperlinkedIdentityField(view_name='strategy1-detail')
    class Meta(StrategyBaseSerializer.Meta):
        model = Strategy1


class Strategy1NodeSerializer(StrategyBaseNodeSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='strategy1node-detail')

    class Meta(StrategyBaseNodeSerializer.Meta):
        model = Strategy1


class Strategy2Serializer(StrategyBaseSerializer):
    class Meta(StrategyBaseSerializer.Meta):
        model = Strategy2


class Strategy2NodeSerializer(StrategyBaseNodeSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='strategy2node-detail')

    class Meta(StrategyBaseNodeSerializer.Meta):
        model = Strategy2


class Strategy3Serializer(StrategyBaseSerializer):
    class Meta(StrategyBaseSerializer.Meta):
        model = Strategy3


class Strategy3NodeSerializer(StrategyBaseNodeSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='strategy3node-detail')

    class Meta(StrategyBaseNodeSerializer.Meta):
        model = Strategy3
