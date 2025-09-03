from django.contrib.contenttypes.models import ContentType
from mptt.utils import get_cached_trees
from rest_framework import serializers
from rest_framework.serializers import ListSerializer

from poms.common.fields import PrimaryKeyRelatedFilteredField, UserCodeField
from poms.common.filters import ClassifierRootFilter
from poms.iam.serializers import IamProtectedSerializer
from poms.system_messages.handlers import send_system_message
from poms.users.filters import OwnerByMasterUserFilter
from poms.users.utils import (
    get_master_user_from_context,
    get_member_from_context,
    get_realm_code_from_context,
    get_space_code_from_context,
)


class BulkSerializer(serializers.Serializer):
    ids = serializers.ListField(child=serializers.IntegerField())


class PomsClassSerializer(serializers.ModelSerializer):
    class Meta:
        fields = [
            "id",
            "user_code",
            "name",
            "description",
        ]


class ModelOwnerSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        from poms.users.serializers import MemberLightViewSerializer

        representation = super().to_representation(instance)

        serializer = MemberLightViewSerializer(instance=instance.owner)

        representation["owner"] = serializer.data

        return representation

    def create(self, validated_data):
        # You should have 'request' in the serializer context !!!
        request = self.context.get("request", None)
        if request and hasattr(request, "user"):
            validated_data["owner"] = request.user.member

        return super().create(validated_data)


class ModelMetaSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        representation = super().to_representation(instance)

        representation["meta"] = {
            "content_type": f"{self.Meta.model._meta.app_label}.{self.Meta.model._meta.model_name}",
            "app_label": self.Meta.model._meta.app_label,
            "model_name": self.Meta.model._meta.model_name,
            "space_code": get_space_code_from_context(self.context),
            "realm_code": get_realm_code_from_context(self.context),
        }

        return representation


class ModelWithTimeStampSerializer(serializers.ModelSerializer):
    modified_at = serializers.ReadOnlyField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["created_at"] = serializers.DateTimeField(read_only=True)
        self.fields["modified_at"] = serializers.DateTimeField(read_only=True)
        self.fields["deleted_at"] = serializers.DateTimeField(read_only=True)

    def validate(self, data):
        if self.instance and "modified_at" in data and data["modified_at"] != self.instance.modified_at:
            raise serializers.ValidationError("Synchronization error")

        return data


class ModelWithUserCodeSerializer(ModelMetaSerializer, ModelOwnerSerializer, IamProtectedSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["user_code"] = UserCodeField()
        self.fields["deleted_user_code"] = UserCodeField(read_only=True)

    def to_internal_value(self, data):
        return super().to_internal_value(data)

    def create(self, validated_data):
        instance = super().create(validated_data)

        member = get_member_from_context(self.context)
        master_user = get_master_user_from_context(self.context)

        entity_name = self.Meta.model._meta.model_name

        send_system_message(
            master_user=master_user,
            performed_by=member.username,
            section="data",
            type="success",
            title=f"New {entity_name} (manual)",
            description=f"New {entity_name} created (manual) - {instance.name}",
        )

        return instance

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)

        member = get_member_from_context(self.context)
        master_user = get_master_user_from_context(self.context)

        entity_name = self.Meta.model._meta.model_name

        send_system_message(
            master_user=master_user,
            performed_by=member.username,
            section="data",
            type="warning",
            title=f"Edit {entity_name} (manual)",
            description=f"{entity_name} edited (manual) - {instance.name}",
        )

        return instance


class AbstractClassifierField(PrimaryKeyRelatedFilteredField):
    filter_backends = [OwnerByMasterUserFilter]


class AbstractClassifierRootField(PrimaryKeyRelatedFilteredField):
    filter_backends = [OwnerByMasterUserFilter, ClassifierRootFilter]


class ClassifierRecursiveField(serializers.Serializer):
    def to_representation(self, instance):
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
        s = cls(context=self.context, data=data)
        s.is_valid(raise_exception=True)
        return s.validated_data


class ClassifierListSerializer(serializers.ListSerializer):
    def get_attribute(self, instance):
        return get_cached_trees(instance.classifiers.all())


class ContentTypeSerializer(serializers.ModelSerializer):
    app_model = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ContentType
        fields = [
            "id",
            "app_model",
        ]
        read_only_fields = fields

    @staticmethod
    def get_app_model(obj) -> str:
        return f"{obj.app_label}.{obj.model}"


class RealmMigrateSchemeSerializer(serializers.Serializer):
    realm_code = serializers.CharField(required=True)
    space_code = serializers.CharField(required=True)


class ModelWithObjectStateSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["is_active"] = serializers.BooleanField(default=True, required=False)
        self.fields["actual_at"] = serializers.DateTimeField(allow_null=True, required=False)
        self.fields["source_type"] = serializers.ChoiceField(
            choices=("manual", "external"), default="manual", required=False
        )
        self.fields["source_origin"] = serializers.CharField(default="manual", required=False)
        self.fields["external_id"] = serializers.CharField(allow_null=True, required=False)
        self.fields["is_manual_locked"] = serializers.BooleanField(default=False, required=False)
        self.fields["is_locked"] = serializers.BooleanField(default=True, required=False)

    def validate(self, data):
        if data.get("source_type", "manual") == "manual" and (
            data.get("source_origin") and data["source_origin"] != "manual"
        ):
            raise serializers.ValidationError("Object is protected from external changes")

        return data
