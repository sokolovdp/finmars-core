from __future__ import unicode_literals

from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers

from poms.currencies.fields import CurrencyField
from poms.currencies.models import Currency, CurrencyHistory
from poms.users.fields import MasterUserField


class CurrencySerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='currency-detail')
    master_user = MasterUserField()

    class Meta:
        model = Currency
        fields = ['url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'notes', 'is_global', 'is_system']
        readonly_fields = ['is_system', 'is_global']


class CurrencyHistorySerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='currencyhistory-detail')
    master_user = MasterUserField()
    currency = CurrencyField()
    fx_rate_expr = serializers.CharField(max_length=50, write_only=True, required=False, allow_null=True,
                                         help_text=_('Expression to calculate fx rate (for example 1/75)'))

    class Meta:
        model = CurrencyHistory
        fields = ['url', 'id', 'master_user', 'currency', 'date', 'fx_rate', 'fx_rate_expr', 'is_global']
        readonly_fields = ['is_global']

    def validate(self, data):
        fx_rate_expr = data.pop('fx_rate_expr', None)
        if fx_rate_expr:
            import simpleeval
            try:
                data['fx_rate'] = simpleeval.simple_eval(fx_rate_expr)
            except (simpleeval.InvalidExpression, ArithmeticError) as e:
                raise serializers.ValidationError({'fx_rate_expr': force_text(e)})
        return data
