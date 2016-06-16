from __future__ import unicode_literals

from rest_framework import serializers

from poms.ui.fields import LayoutContentTypeField
from poms.ui.models import TemplateListLayout, TemplateEditLayout, ListLayout, EditLayout
from poms.users.fields import MasterUserField, HiddenMemberField


class TemplateListLayoutSerializer(serializers.ModelSerializer):
    master_user = MasterUserField()
    content_type = LayoutContentTypeField()
    data = serializers.JSONField(allow_null=False)

    class Meta:
        model = TemplateListLayout
        fields = ['url', 'id', 'master_user', 'content_type', 'name', 'data']


class TemplateEditLayoutSerializer(serializers.ModelSerializer):
    master_user = MasterUserField()
    content_type = LayoutContentTypeField()
    data = serializers.JSONField(allow_null=False)

    class Meta:
        model = TemplateEditLayout
        fields = ['url', 'id', 'master_user', 'content_type', 'data']


class ListLayoutSerializer(serializers.ModelSerializer):
    member = HiddenMemberField()
    content_type = LayoutContentTypeField()
    data = serializers.JSONField(allow_null=False)

    class Meta:
        model = ListLayout
        fields = ['url', 'id', 'member', 'content_type', 'name', 'data']


class EditLayoutSerializer(serializers.ModelSerializer):
    member = HiddenMemberField()
    content_type = LayoutContentTypeField()
    data = serializers.JSONField(allow_null=False)

    class Meta:
        model = EditLayout
        fields = ['url', 'id', 'member', 'content_type', 'data']
