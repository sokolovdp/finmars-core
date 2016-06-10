from __future__ import unicode_literals

from rest_framework import serializers

from poms.obj_perms.serializers import ModelWithObjectPermissionSerializer
from poms.tags.fields import TagContentTypeField
from poms.tags.models import Tag
from poms.users.fields import MasterUserField


class TagSerializer(ModelWithObjectPermissionSerializer):
    master_user = MasterUserField()
    content_types = TagContentTypeField(many=True)

    account_types = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    accounts = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    currencies = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    instrument_types = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    instruments = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    counterparties = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    responsibles = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    strategies1 = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    strategies2 = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    strategies3 = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    portfolios = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    transaction_types = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Tag
        fields = [
            'url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'notes', 'content_types',
            'account_types', 'accounts', 'currencies', 'instrument_types', 'instruments',
            'counterparties', 'responsibles', 'strategies1', 'strategies2', 'strategies3',
            'portfolios', 'transaction_types'
        ]
