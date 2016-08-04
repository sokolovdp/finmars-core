from __future__ import unicode_literals

from rest_framework import serializers

from poms.common.serializers import ModelWithUserCodeSerializer
from poms.obj_perms.serializers import ModelWithObjectPermissionSerializer
from poms.tags.fields import TagContentTypeField
from poms.tags.models import Tag
from poms.users.fields import MasterUserField


class TagSerializer(ModelWithObjectPermissionSerializer, ModelWithUserCodeSerializer):
    master_user = MasterUserField()
    content_types = TagContentTypeField(many=True)

    # account_types = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    # accounts = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    # currencies = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    # instrument_types = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    # instruments = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    # counterparties = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    # responsibles = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    # strategy_groups = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    # strategy_subgroups = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    # strategies = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    # portfolios = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    # transaction_types = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Tag
        fields = [
            'url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'public_name', 'notes', 'content_types',
            # 'account_types', 'accounts', 'currencies', 'instrument_types', 'instruments',
            # 'counterparties', 'responsibles',
            # 'strategy_groups', 'strategy_subgroups', 'strategies',
            # 'portfolios', 'transaction_types'
        ]
