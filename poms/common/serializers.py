from rest_framework import serializers

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


class ClassifierSerializerBase(PomsSerializerBase):
    master_user = MasterUserField()

    class Meta(PomsSerializerBase.Meta):
        fields = PomsSerializerBase.Meta.fields + ['master_user', 'user_code', 'name', 'short_name', 'notes',
                                                   'parent', 'children', 'level']
