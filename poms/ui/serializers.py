from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import IntegrityError
from mptt.utils import get_cached_trees
from rest_framework import serializers

from poms.common.serializers import (
    ModelMetaSerializer,
    ModelWithTimeStampSerializer,
    ModelWithUserCodeSerializer,
)
from poms.ui.fields import LayoutContentTypeField, ListLayoutField
from poms.ui.models import (
    Bookmark,
    ColorPalette,
    ColorPaletteColor,
    ColumnSortData,
    ComplexTransactionUserField,
    ConfigurationExportLayout,
    ContextMenuLayout,
    CrossEntityAttributeExtension,
    DashboardLayout,
    Draft,
    EditLayout,
    EntityTooltip,
    InstrumentUserField,
    ListLayout,
    MemberLayout,
    MobileLayout,
    PortalInterfaceAccessModel,
    TemplateLayout,
    TransactionUserField,
    UserInterfaceAccessModel,
)
from poms.users.fields import HiddenMemberField, MasterUserField


class PortalInterfaceAccessModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortalInterfaceAccessModel
        fields = [
            "id",
            "value",
            "user_code",
            "name",
        ]


class UserInterfaceAccessModelSerializer(ModelWithUserCodeSerializer):
    member = HiddenMemberField()
    allowed_items = serializers.ListField(allow_null=False)

    class Meta:
        model = UserInterfaceAccessModel
        fields = [
            "id",
            "name",
            "role",
            "user_code",
            "configuration_code",
            "allowed_items",
            "created_at",
            "modified_at",
            "member",
        ]


class ComplexTransactionUserFieldSerializer(ModelWithUserCodeSerializer, ModelMetaSerializer):
    master_user = MasterUserField()

    class Meta:
        model = ComplexTransactionUserField
        fields = [
            "id",
            "master_user",
            "key",
            "name",
            "is_active",
            "user_code",
            "configuration_code",
        ]


class TransactionUserFieldSerializer(ModelWithUserCodeSerializer, ModelMetaSerializer):
    master_user = MasterUserField()

    class Meta:
        model = TransactionUserField
        fields = [
            "id",
            "master_user",
            "key",
            "name",
            "is_active",
            "user_code",
            "configuration_code",
        ]


class ColorPaletteColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = ColorPaletteColor
        fields = [
            "id",
            "order",
            "name",
            "value",
            "tooltip",
        ]


class ColorPaletteSerializer(ModelWithUserCodeSerializer, ModelMetaSerializer):
    master_user = MasterUserField()

    colors = ColorPaletteColorSerializer(many=True)

    class Meta:
        model = ColorPalette
        fields = [
            "id",
            "master_user",
            "name",
            "user_code",
            "short_name",
            "is_default",
            "colors",
        ]

    def save_colors(self, instance, colors):
        for color in colors:
            try:
                item = ColorPaletteColor.objects.get(color_palette=instance, order=color["order"])
                self._save_item_color(color, item)

            except ColorPaletteColor.DoesNotExist:
                item = ColorPaletteColor.objects.create(color_palette=instance, order=color["order"])
                self._save_item_color(color, item)

    @staticmethod
    def _save_item_color(color, item):
        item.tooltip = color["tooltip"]
        item.value = color["value"]
        item.name = color["name"]
        item.save()

    def create(self, validated_data):
        colors = validated_data.pop("colors")

        instance = super().create(validated_data)

        self.save_colors(instance=instance, colors=colors)

        return instance

    def update(self, instance, validated_data):
        colors = validated_data.pop("colors")

        instance = super().update(instance, validated_data)

        self.save_colors(instance=instance, colors=colors)

        return instance


class EntityTooltipSerializer(ModelMetaSerializer):
    master_user = MasterUserField()

    content_type = LayoutContentTypeField()

    class Meta:
        model = EntityTooltip
        fields = [
            "id",
            "master_user",
            "content_type",
            "name",
            "key",
            "text",
        ]


class CrossEntityAttributeExtensionSerializer(serializers.ModelSerializer):
    master_user = MasterUserField()

    context_content_type = LayoutContentTypeField()
    content_type_from = LayoutContentTypeField()
    content_type_to = LayoutContentTypeField()

    class Meta:
        model = CrossEntityAttributeExtension
        fields = [
            "id",
            "master_user",
            "context_content_type",
            "content_type_from",
            "content_type_to",
            "extension_type",
            "key_from",
            "key_to",
            "value_to",
        ]


class ColumnSortDataSerializer(serializers.ModelSerializer):
    member = HiddenMemberField()
    data = serializers.JSONField(allow_null=False)

    class Meta:
        model = ColumnSortData
        fields = [
            "id",
            "member",
            "name",
            "user_code",
            "column_key",
            "is_common",
            "data",
        ]


class InstrumentUserFieldSerializer(ModelWithUserCodeSerializer, ModelMetaSerializer):
    master_user = MasterUserField()

    class Meta:
        model = InstrumentUserField
        fields = [
            "id",
            "master_user",
            "key",
            "name",
            "user_code",
            "configuration_code",
        ]


class TemplateLayoutSerializer(ModelWithUserCodeSerializer):
    member = HiddenMemberField()
    data = serializers.JSONField(allow_null=False)

    class Meta:
        model = TemplateLayout
        fields = [
            "id",
            "member",
            "type",
            "name",
            "user_code",
            "is_default",
            "data",
        ]


class ContextMenuLayoutSerializer(ModelWithTimeStampSerializer, ModelWithUserCodeSerializer):
    member = HiddenMemberField()
    data = serializers.JSONField(allow_null=False)

    class Meta:
        model = ContextMenuLayout
        fields = [
            "id",
            "member",
            "type",
            "name",
            "user_code",
            "configuration_code",
            "data",
            "origin_for_global_layout",
            "sourced_from_global_layout",
        ]


class ListLayoutSerializer(ModelWithTimeStampSerializer, ModelWithUserCodeSerializer):
    member = HiddenMemberField()
    content_type = LayoutContentTypeField()
    data = serializers.JSONField(allow_null=False)

    class Meta:
        model = ListLayout
        fields = [
            "id",
            "member",
            "content_type",
            "name",
            "user_code",
            "configuration_code",
            "is_default",
            "is_active",
            "is_systemic",
            "data",
            "origin_for_global_layout",
            "sourced_from_global_layout",
        ]

    def to_representation(self, instance):
        return super().to_representation(instance)


class ListLayoutLightSerializer(ModelWithTimeStampSerializer, ModelWithUserCodeSerializer):
    member = HiddenMemberField()
    content_type = LayoutContentTypeField()

    class Meta:
        model = ListLayout
        fields = [
            "id",
            "member",
            "content_type",
            "name",
            "user_code",
            "configuration_code",
            "is_default",
            "is_active",
            "is_systemic",
            "origin_for_global_layout",
            "sourced_from_global_layout",
        ]


class DashboardLayoutSerializer(ModelWithTimeStampSerializer, ModelWithUserCodeSerializer):
    member = HiddenMemberField()
    data = serializers.JSONField(allow_null=False)

    class Meta:
        model = DashboardLayout
        fields = [
            "id",
            "member",
            "name",
            "user_code",
            "configuration_code",
            "is_default",
            "is_active",
            "data",
            "origin_for_global_layout",
            "sourced_from_global_layout",
        ]


class DashboardLayoutLightSerializer(ModelWithTimeStampSerializer, ModelWithUserCodeSerializer):
    member = HiddenMemberField()

    class Meta:
        model = DashboardLayout
        fields = [
            "id",
            "member",
            "name",
            "user_code",
            "configuration_code",
            "is_default",
            "is_active",
            "origin_for_global_layout",
            "sourced_from_global_layout",
        ]


class MemberLayoutSerializer(ModelWithTimeStampSerializer, ModelWithUserCodeSerializer):
    member = HiddenMemberField()
    data = serializers.JSONField(allow_null=False)

    class Meta:
        model = MemberLayout
        fields = [
            "id",
            "member",
            "name",
            "user_code",
            "configuration_code",
            "is_default",
            "is_active",
            "data",
            "origin_for_global_layout",
            "sourced_from_global_layout",
        ]


class MobileLayoutSerializer(ModelWithTimeStampSerializer, ModelWithUserCodeSerializer):
    member = HiddenMemberField()
    data = serializers.JSONField(allow_null=False)

    class Meta:
        model = MobileLayout
        fields = [
            "id",
            "member",
            "name",
            "user_code",
            "configuration_code",
            "is_default",
            "is_active",
            "data",
        ]


class ConfigurationExportLayoutSerializer(ModelWithTimeStampSerializer):
    member = HiddenMemberField()
    data = serializers.JSONField(allow_null=False)

    class Meta:
        model = ConfigurationExportLayout
        fields = [
            "id",
            "member",
            "name",
            "is_default",
            "data",
        ]


class EditLayoutSerializer(ModelWithTimeStampSerializer, ModelWithUserCodeSerializer):
    member = HiddenMemberField()
    content_type = LayoutContentTypeField()
    data = serializers.JSONField(allow_null=False)

    class Meta:
        model = EditLayout
        fields = [
            "id",
            "member",
            "content_type",
            "name",
            "user_code",
            "configuration_code",
            "is_default",
            "is_active",
            "data",
            "origin_for_global_layout",
            "sourced_from_global_layout",
        ]


class BookmarkRecursiveField(serializers.Serializer):
    def to_representation(self, instance):
        if isinstance(self.parent, serializers.ListSerializer):
            cls = self.parent.parent.__class__
        else:
            cls = self.parent.__class__
        return cls(instance=instance, context=self.context).data

    def to_internal_value(self, data):
        if isinstance(self.parent, serializers.ListSerializer):
            cls = self.parent.parent.__class__
        else:
            cls = self.parent.__class__
        s = cls(context=self.context, data=data)
        s.is_valid(raise_exception=True)
        return s.validated_data


class BookmarkListSerializer(serializers.ListSerializer):
    def get_attribute(self, instance):
        return get_cached_trees(instance.children.all())


class BookmarkSerializer(serializers.ModelSerializer):
    member = HiddenMemberField()
    id = serializers.IntegerField(read_only=False, required=False, allow_null=True)
    name = serializers.CharField(allow_null=False, allow_blank=False)
    uri = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    list_layout = ListLayoutField(required=False, allow_null=True)
    data = serializers.JSONField(required=False, allow_null=True)

    children = BookmarkRecursiveField(source="get_children", many=True, required=False, allow_null=True)

    class Meta:
        list_serializer_class = BookmarkListSerializer
        model = Bookmark
        fields = [
            "id",
            "member",
            "name",
            "uri",
            "list_layout",
            "data",
            "children",
        ]

    def create(self, validated_data):
        children = validated_data.pop("get_children", validated_data.pop("children", serializers.empty))
        instance = super().create(validated_data)
        if children is not serializers.empty:
            self.save_children(instance, children)
        return instance

    def update(self, instance, validated_data):
        children = validated_data.pop("get_children", validated_data.pop("children", serializers.empty))
        instance = super().update(instance, validated_data)
        if children is not serializers.empty:
            self.save_children(instance, children)
        return instance

    def save_children(self, instance, children_tree):
        children_tree = children_tree or []

        if len(children_tree) == 0:
            instance.children.all().delete()
            return

        processed = set()
        for node in children_tree:
            self.save_child(instance, node, instance, processed)

        instance.children.exclude(pk__in=processed).delete()

    def save_child(self, instance, node, parent, processed):
        if "id" in node:
            try:
                o = Bookmark.objects.get(member=instance.member, tree_id=parent.tree_id, pk=node.pop("id"))
            except ObjectDoesNotExist:
                o = Bookmark()
        else:
            o = Bookmark()
        o.parent = parent
        o.member = instance.member
        children = node.pop("get_children", node.pop("children", []))
        for k, v in node.items():
            setattr(o, k, v)
        try:
            o.save()
        except IntegrityError as e:
            raise ValidationError(str(e)) from e

        processed.add(o.id)

        for c in children:
            self.save_child(instance, c, o, processed)


# class ConfigurationSerializer(serializers.ModelSerializer):
#     master_user = MasterUserField()
#     data = serializers.JSONField(allow_null=False)
#
#     class Meta:
#         model = Configuration
#         fields = ['id', 'master_user', 'name', 'description', 'data']


class DraftSerializer(ModelWithTimeStampSerializer, ModelMetaSerializer):
    member = HiddenMemberField()
    data = serializers.JSONField(allow_null=False)

    class Meta:
        model = Draft
        fields = [
            "id",
            "member",
            "name",
            "modified_at",
            "created_at",
            "user_code",
            "data",
        ]
