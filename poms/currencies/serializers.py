from __future__ import unicode_literals

from rest_framework import serializers

from poms.common.fields import FloatEvalField
from poms.common.serializers import ModelWithUserCodeSerializer, ReadonlyNamedModelSerializer
from poms.currencies.fields import CurrencyField
from poms.currencies.models import Currency, CurrencyHistory
from poms.instruments.fields import PricingPolicyField
from poms.integrations.fields import PriceDownloadSchemeField
from poms.obj_perms.serializers import ReadonlyNamedModelWithObjectPermissionSerializer
from poms.tags.fields import TagField
from poms.users.fields import MasterUserField


class CurrencySerializer(ModelWithUserCodeSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='currency-detail')
    master_user = MasterUserField()
    price_download_scheme = PriceDownloadSchemeField(allow_null=True)
    tags = TagField(many=True, required=False, allow_null=True)
    tags_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='tags', many=True)

    class Meta:
        model = Currency
        fields = [
            'url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'notes',
            'reference_for_pricing', 'daily_pricing_model', 'price_download_scheme',
            'is_default', 'is_deleted', 'tags', 'tags_object',
        ]


class CurrencyHistorySerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='currencyhistory-detail')
    currency = CurrencyField()
    currency_object = ReadonlyNamedModelSerializer(source='currency')
    pricing_policy = PricingPolicyField(allow_null=False)
    pricing_policy_object = ReadonlyNamedModelSerializer(source='pricing_policy')
    fx_rate = FloatEvalField()

    class Meta:
        model = CurrencyHistory
        fields = [
            'url', 'id', 'currency', 'currency_object', 'pricing_policy', 'pricing_policy_object', 'date', 'fx_rate'
        ]

    def __init__(self, *args, **kwargs):
        super(CurrencyHistorySerializer, self).__init__(*args, **kwargs)
        if 'request' not in self.context:
            self.fields.pop('url')
