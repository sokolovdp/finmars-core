import pprint

from rest_framework import serializers
from rest_framework.exceptions import APIException
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
        # print('%s -> %s' % (instance.pk, getattr(instance, '_cached_children', 'LOL')))
        return cls(instance=instance, context=self.context).data

    def to_internal_value(self, data):
        # if isinstance(self.parent, ListSerializer):
        #     cls = self.parent.parent.__class__
        # else:
        #     cls = self.parent.__class__
        # s = cls(context=self.context, data=data)
        # s.is_valid(raise_exception=True)
        # return s.validated_data
        return data


class ClassifierSerializerBase(PomsSerializerBase):
    id = serializers.IntegerField(read_only=False, required=False, allow_null=True)
    master_user = MasterUserField()
    children = ClassifierRecursiveField(source='get_children', many=True, required=False, allow_null=True)

    # children = ClassifierRecursiveField(many=True, required=False, allow_null=True)

    class Meta(PomsSerializerBase.Meta):
        # fields = PomsSerializerBase.Meta.fields + ['master_user', 'user_code', 'name', 'short_name', 'notes', 'parent', 'children', 'level']
        fields = PomsSerializerBase.Meta.fields + ['master_user', 'user_code', 'name', 'short_name', 'notes',
                                                   'level', 'children']

    def create(self, validated_data):
        validated_data.pop('id', None)
        # children = validated_data.pop('children', None)
        children = validated_data.pop('get_children', None)
        instance = super(ClassifierSerializerBase, self).create(validated_data)
        self.save_tree(instance, children)
        return instance

    def update(self, instance, validated_data):
        pprint.pprint(validated_data)

        validated_data.pop('id', None)
        # children = validated_data.pop('children', None)
        children = validated_data.pop('get_children', [])

        if instance.is_leaf_node() and children:
            raise APIException("Can't add children to leaf node")

        instance = super(ClassifierSerializerBase, self).update(instance, validated_data)
        self.save_tree(instance, children)
        return instance

    def save_tree(self, node, children):
        cls = self.__class__
        # processed = set()

        # root = SimpleLazyObject(lambda: node.get_root())
        # print('root: ', root)

        context = {}
        context.update(self.context)
        if node.is_root_node():
            processed = context['processed'] = set()
            processed.add(node.pk)
            root = context['root_node'] = node
            # family_cache = context['family_cache'] = {n.pk: n for n in node.get_family()}
        else:
            processed = self.context['processed']
            root = self.context['root_node']
            # family_cache = context['family_cache']

        for child_data in children:
            child_pk = child_data.pop('id', None)

            if child_pk in processed:
                raise APIException('Tree node  with id %s already processed' % child_pk)

            if child_pk:
                child_obj = root.get_family().get(pk=child_pk)
                if child_obj.parent_id != node.id:
                    child_obj.parent = node
            else:
                child_obj = None

            node_s = cls(instance=child_obj, data=child_data, context=context)
            node_s.is_valid(raise_exception=True)
            child_obj = node_s.save(parent=node)
            processed.add(child_obj.pk)

        if node.is_root_node():
            # print('processed', processed)
            node.get_family().exclude(pk__in=processed).delete()
