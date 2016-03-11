from __future__ import unicode_literals

from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers

from poms.api.fields import CurrentMasterUserDefault
from poms.currencies.models import Currency, CurrencyHistory


class CurrencySerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='currency-detail')
    master_user = serializers.HiddenField(default=CurrentMasterUserDefault())

    class Meta:
        model = Currency
        fields = ['url', 'id', 'master_user', 'code', 'name', 'is_global']
        readonly_fields = ['is_global']


class CurrencyHistorySerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='currencyhistory-detail')
    fx_rate_expr = serializers.CharField(max_length=50, write_only=True, required=False, allow_null=True,
                                         help_text=_('Expression to calculate fx rate (for example 1/75)'))

    class Meta:
        model = CurrencyHistory
        fields = ['url', 'id', 'currency', 'date', 'fx_rate', 'fx_rate_expr']

    def validate(self, data):
        fx_rate_expr = data.pop('fx_rate_expr', None)
        if fx_rate_expr:
            import simpleeval
            try:
                data['fx_rate'] = simpleeval.simple_eval(fx_rate_expr)
            except (simpleeval.InvalidExpression, ArithmeticError) as e:
                raise serializers.ValidationError({'fx_rate_expr':force_text(e)})
        return data
