from django.core.exceptions import ObjectDoesNotExist
from django.utils.text import Truncator
from django.utils.translation import ugettext_lazy
from mptt.utils import get_cached_trees
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import ListSerializer

from poms.audit import history
from poms.common.fields import PrimaryKeyRelatedFilteredField, UserCodeField
from poms.common.filters import ClassifierRootFilter
from poms.users.filters import OwnerByMasterUserFilter


class AbstractPomsSerializer(serializers.ModelSerializer):
    class Meta:
        fields = [
            'url',
            'id'
        ]


class PomsClassSerializer(AbstractPomsSerializer):
    class Meta(AbstractPomsSerializer.Meta):
        fields = AbstractPomsSerializer.Meta.fields + [
            'system_code',
            'name',
            'description'
        ]


class ModelWithUserCodeSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        super(ModelWithUserCodeSerializer, self).__init__(*args, **kwargs)
        self.fields['user_code'] = UserCodeField()

    def to_internal_value(self, data):
        ret = super(ModelWithUserCodeSerializer, self).to_internal_value(data)

        # for correct message on unique error
        user_code = ret.get('user_code', None)
        if not user_code:
            user_code = ret.get('name', '')
            user_code = Truncator(user_code).chars(25, truncate='')
            ret['user_code'] = user_code

        return ret


class AbstractClassifierField(PrimaryKeyRelatedFilteredField):
    filter_backends = [
        OwnerByMasterUserFilter
    ]


class AbstractClassifierRootField(PrimaryKeyRelatedFilteredField):
    filter_backends = [
        OwnerByMasterUserFilter,
        ClassifierRootFilter
    ]


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
        # print(data)
        if isinstance(self.parent, ListSerializer):
            cls = self.parent.parent.__class__
        else:
            cls = self.parent.__class__
        s = cls(context=self.context, data=data)
        s.is_valid(raise_exception=True)
        return s.validated_data
        # return data


# class ClassifierSerializerBase(PomsSerializerBase, ModelWithObjectPermissionSerializer):
#     id = serializers.IntegerField(read_only=False, required=False, allow_null=True)
#     master_user = MasterUserField()
#     children = ClassifierRecursiveField(source='get_children', many=True, required=False, allow_null=True)
#
#     class Meta(PomsSerializerBase.Meta):
#         fields = PomsSerializerBase.Meta.fields + [
#             'master_user',
#             'user_code',
#             'name',
#             'short_name',
#             'notes',
#             'level',
#             'children'
#         ]
#
#     def to_representation(self, instance):
#         ret = super(ClassifierSerializerBase, self).to_representation(instance)
#         if not instance.is_root_node():
#             ret.pop("granted_permissions", None)
#             ret.pop("user_object_permissions", None)
#             ret.pop("group_object_permissions", None)
#         return ret
#
#     def create(self, validated_data):
#         validated_data.pop('id', None)
#         # children = validated_data.pop('children', None)
#         children = validated_data.pop('get_children', None)
#         instance = super(ClassifierSerializerBase, self).create(validated_data)
#         self.save_tree(instance, children)
#         return instance
#
#     def update(self, instance, validated_data):
#         validated_data.pop('id', None)
#         children = validated_data.pop('get_children', [])
#         instance = super(ClassifierSerializerBase, self).update(instance, validated_data)
#         if instance.is_root_node() or not instance.is_leaf_node() or settings.CLASSIFIER_RELAX_UPDATE_MODE:
#             self.save_tree(instance, children)
#         else:
#             if children:
#                 raise ValidationError("Can't add children to leaf node")
#         return instance
#
#     def save_tree(self, node, children):
#         # processed = set()
#         # root = SimpleLazyObject(lambda: node.get_root())
#         # print('root: ', root)
#
#         if not children:
#             return
#
#         context = {}
#         context.update(self.context)
#         if node.is_root_node():
#             processed = context['processed'] = set()
#             processed.add(node.pk)
#             root = context['root_node'] = node
#             # family_cache = context['family_cache'] = {n.pk: n for n in node.get_family()}
#         else:
#             processed = self.context['processed']
#             root = self.context['root_node']
#             # family_cache = context['family_cache']
#
#         for child_data in children:
#             child_pk = child_data.pop('id', None)
#
#             if child_pk in processed:
#                 raise ValidationError('Tree node with id %s already processed' % child_pk)
#
#             if child_pk:
#                 child_obj = root.get_family().get(pk=child_pk)
#                 if child_obj.parent_id != node.id:
#                     child_obj.parent = node
#             else:
#                 child_obj = None
#
#             node_s = self.__class__(instance=child_obj, data=child_data, context=context)
#             node_s.is_valid(raise_exception=True)
#             child_obj = node_s.save(parent=node)
#             processed.add(child_obj.pk)
#
#         if node.is_root_node():
#             # print('processed', processed)
#             node.get_family().exclude(pk__in=processed).delete()
#
#     def save_object_permission(self, instance, user_object_permissions, group_object_permissions, created):
#         if instance.is_root_node():
#             super(ClassifierSerializerBase, self).save_object_permission(instance, user_object_permissions,
#                                                                          group_object_permissions, created)


class ClassifierListSerializer(serializers.ListSerializer):
    def get_attribute(self, instance):
        tree = get_cached_trees(instance.classifiers.all())
        return tree


class AbstractClassifierSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=False, required=False, allow_null=True)
    children = ClassifierRecursiveField(source='get_children', many=True, required=False, allow_null=True)

    class Meta(AbstractPomsSerializer.Meta):
        list_serializer_class = ClassifierListSerializer
        fields = [
            'id',
            'name',
            'level',
            'children'
        ]
        # extra_kwargs = {'user_code': {'required': False}}

    def __init__(self, *args, **kwargs):
        show_children = kwargs.pop('show_children', True)
        super(AbstractClassifierSerializer, self).__init__(*args, **kwargs)
        if not show_children:
            self.fields.pop('children')

    def create(self, validated_data):
        validated_data.pop('id', None)
        children = validated_data.pop('get_children', None)
        instance = super(AbstractClassifierSerializer, self).create(validated_data)
        self.save_tree(instance, children)
        return instance

    def update(self, instance, validated_data):
        validated_data.pop('id', None)
        children = validated_data.pop('get_children', [])
        instance = super(AbstractClassifierSerializer, self).update(instance, validated_data)
        # if instance.is_root_node() or not instance.is_leaf_node() or settings.CLASSIFIER_RELAX_UPDATE_MODE:
        self.save_tree(instance, children)
        # else:
        #     if children:
        #         raise ValidationError("Can't add children to leaf node")
        return instance

    def save_tree(self, node, children):
        # processed = set()
        # root = SimpleLazyObject(lambda: node.get_root())
        # print('root: ', root)

        if not children:
            return

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
                raise ValidationError('Tree node with id %s already processed' % child_pk)

            if child_pk:
                child_obj = root.get_family().get(pk=child_pk)
                if child_obj.parent_id != node.id:
                    child_obj.parent = node
            else:
                child_obj = None

            node_s = self.__class__(instance=child_obj, data=child_data, context=context)
            node_s.is_valid(raise_exception=True)
            child_obj = node_s.save(parent=node)
            processed.add(child_obj.pk)

        if node.is_root_node():
            # print('processed', processed)
            node.get_family().exclude(pk__in=processed).delete()


class AbstractClassifierNodeSerializer(AbstractPomsSerializer):
    attribute_type = serializers.PrimaryKeyRelatedField(read_only=True)
    parent = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta(AbstractPomsSerializer.Meta):
        fields = AbstractPomsSerializer.Meta.fields + [
            'attribute_type',
            'name',
            'parent',
            'level',
            'tree_id',
            # 'children',
        ]


class BulkModelSerializer(serializers.Serializer):
    default_error_messages = {
        'invalid': ugettext_lazy('Invalid data')
    }

    def __init__(self, child_serializer_class=None, queryset=None, **kwargs):
        super(BulkModelSerializer, self).__init__(**kwargs)
        self.child_serializer_class = child_serializer_class
        self.queryset = queryset

    def get_child_serializer(self, instance=None, data=None, many=False):
        return self.child_serializer_class(context=self.context, instance=instance, data=data, many=many)

    def validate(self, attrs):
        # print('validate:', 'attrs =', attrs)
        # for cattrs in attrs:
        #     print('cattrs =', cattrs)
        #     self.get_base_serializer(data=cattrs).is_valid(raise_exception=True)
        return attrs

    def to_internal_value(self, data):
        ret = []
        if not isinstance(data, (list, tuple)):
            self.fail('invalid')
            # message = self.error_messages['invalid'].format(
            #     datatype=type(data).__name__
            # )
            # raise ValidationError({
            #     api_settings.NON_FIELD_ERRORS_KEY: [message]
            # })

        errors = []
        has_errors = False
        for cattrs in data:
            schild = self.get_child_serializer(data=cattrs, many=False)
            if schild.is_valid(raise_exception=False):
                data = schild.validated_data
                if 'id' not in data:
                    data = data.copy()
                    data['id'] = int(cattrs.get('id', None))
                ret.append(data)
                errors.append({})
            else:
                errors.append(schild.errors)
                has_errors = True
        if has_errors:
            raise ValidationError(errors)

        return ret

    def to_representation(self, instance):
        return self.get_child_serializer(instance=instance, many=True).to_representation(instance)

    def save(self, **kwargs):
        ret = []
        for cattrs in self.validated_data:
            data = cattrs.copy()
            pk = data.pop('id', None)
            instance = None
            if pk is not None:
                try:
                    instance = self.queryset.get(pk=pk)
                except ObjectDoesNotExist:
                    pass
            schild = self.get_child_serializer(instance=instance, data=data, many=False)

            with history.enable():
                if instance is not None:
                    history.set_flag_change()
                    instance = schild.update(instance, data)
                else:
                    history.set_flag_addition()
                    instance = schild.create(data)
                history.set_actor_content_object(instance)

            ret.append(instance)
        return ret
