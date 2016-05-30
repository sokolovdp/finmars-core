from __future__ import unicode_literals

from rest_framework import serializers

from poms.ui.fields import LayoutContentTypeField
from poms.ui.models import TemplateListLayout, TemplateEditLayout, ListLayout, EditLayout
from poms.users.fields import MasterUserField, HiddenMemberField


class TemplateListLayoutSerializer(serializers.ModelSerializer):
    master_user = MasterUserField()
    content_type = LayoutContentTypeField()
    json_data = serializers.JSONField()

    class Meta:
        model = TemplateListLayout
        fields = ['url', 'id', 'master_user', 'content_type', 'name', 'json_data']


class TemplateEditLayoutSerializer(serializers.ModelSerializer):
    master_user = MasterUserField()
    content_type = LayoutContentTypeField()
    json_data = serializers.JSONField()

    class Meta:
        model = TemplateEditLayout
        fields = ['url', 'id', 'master_user', 'content_type', 'json_data']


class ListLayoutSerializer(serializers.ModelSerializer):
    member = HiddenMemberField()
    content_type = LayoutContentTypeField()
    json_data = serializers.JSONField()

    class Meta:
        model = ListLayout
        fields = ['url', 'id', 'member', 'content_type', 'name', 'json_data']


class EditLayoutSerializer(serializers.ModelSerializer):
    member = HiddenMemberField()
    content_type = LayoutContentTypeField()
    json_data = serializers.JSONField()

    class Meta:
        model = EditLayout
        fields = ['url', 'id', 'member', 'content_type', 'json_data']
