from rest_framework import serializers
from rest_framework.serializers import ListSerializer

from poms.api.fields import FilteredPrimaryKeyRelatedField
from poms.common.filters import ClassifierRootFilter
from poms.users.fields import MasterUserField
from poms.users.filters import OwnerByMasterUserFilter


class PomsSerializerBase(serializers.ModelSerializer):
    class Meta:
        fields = ['url', 'id']


class PomsClassSerializer(PomsSerializerBase):
    class Meta(PomsSerializerBase.Meta):
        fields = PomsSerializerBase.Meta.fields + ['system_code', 'name', 'description']


class ClassifierFieldBase(FilteredPrimaryKeyRelatedField):
    filter_backends = [OwnerByMasterUserFilter]


class ClassifierRootFieldBase(FilteredPrimaryKeyRelatedField):
    filter_backends = [OwnerByMasterUserFilter, ClassifierRootFilter]


class ClassifierRecursiveField(serializers.Serializer):
    def to_representation(self, instance):
        # context = {"parent": self.parent.object, "parent_serializer": self.parent}
        # cls = self.parent.__class__
        # return cls(instance=instance.children.all(), many=True).data

        if isinstance(self.parent, ListSerializer):
            cls = self.parent.parent.__class__
        else:
            cls = self.parent.__class__
        return cls(instance=instance, context=self.context).data

    def to_internal_value(self, data):
        if isinstance(self.parent, ListSerializer):
            cls = self.parent.parent.__class__
        else:
            cls = self.parent.__class__
        return cls(context=self.context).to_internal_value(data)
        # return super(RecursiveField, self).to_internal_value(data)


class ClassifierSerializerBase(PomsSerializerBase):
    id = serializers.IntegerField(read_only=False, required=False, allow_null=True)
    master_user = MasterUserField()
    children = ClassifierRecursiveField(many=True, required=False, allow_null=True)

    class Meta(PomsSerializerBase.Meta):
        # fields = PomsSerializerBase.Meta.fields + ['master_user', 'user_code', 'name', 'short_name', 'notes', 'parent', 'children', 'level']
        fields = PomsSerializerBase.Meta.fields + ['master_user', 'user_code', 'name', 'short_name', 'notes',
                                                   'level', 'children']

    def create(self, validated_data):
        validated_data.pop('id', None)
        children = validated_data.pop('children', None)
        # master_user = self.context['request'].user.master_user
        # validated_data['master_user'] = master_user
        instance = super(ClassifierSerializerBase, self).create(validated_data)
        self.save_tree(instance, children)
        return instance

    def update(self, instance, validated_data):
        validated_data.pop('id', None)
        children = validated_data.pop('children', None)
        instance = super(ClassifierSerializerBase, self).update(instance, validated_data)
        self.save_tree(instance, children)
        return instance

    def save_tree(self, node, children):
        if children is not None:
            cls = self.__class__
            processed = set()
            for child in children:
                # print(child)
                pk = child.pop('id', None)
                child_obj = node.children.get(pk=pk) if pk else None
                node_s = cls(instance=child_obj, data=child, context=self.context)
                node_s.is_valid(raise_exception=True)
                child_obj = node_s.save(parent=node)
                processed.add(child_obj.pk)
            node.children.exclude(pk__in=processed).delete()
