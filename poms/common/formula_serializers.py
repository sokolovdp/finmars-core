# from rest_framework import serializers
#
# from poms.accounts.models import Account
# from poms.currencies.models import Currency
# from poms.instruments.models import InstrumentType, Instrument
# from poms.portfolios.models import Portfolio
# from poms.strategies.models import Strategy1, Strategy2, Strategy3
# from poms.transactions.models import Transaction
#
#
# class EvalAccountSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Account
#         fields = ('id', 'user_code', 'name', 'short_name', 'notes',)
#         read_only_fields = fields
#
#
# class EvalCurrencySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Currency
#         fields = ('id', 'user_code', 'name', 'short_name', 'notes',)
#         read_only_fields = fields
#
#
# class EvalInstrumentTypeSerializer(serializers.ModelSerializer):
#     instrument_class = serializers.PrimaryKeyRelatedField(read_only=True)
#
#     class Meta:
#         model = InstrumentType
#         fields = ('id', 'user_code', 'name', 'short_name', 'notes', 'instrument_class',)
#         read_only_fields = fields
#
#
# class EvalInstrumentSerializer(serializers.ModelSerializer):
#     instrument_type = EvalInstrumentTypeSerializer(read_only=True)
#     pricing_currency = EvalCurrencySerializer(read_only=True)
#     accrued_currency = EvalCurrencySerializer(read_only=True)
#     daily_pricing_model = serializers.PrimaryKeyRelatedField(read_only=True)
#     payment_size_detail = serializers.PrimaryKeyRelatedField(read_only=True)
#
#     class Meta:
#         model = Instrument
#         fields = ('id', 'instrument_type', 'user_code', 'name', 'short_name', 'notes',
#                   'pricing_currency', 'price_multiplier', 'accrued_currency', 'accrued_multiplier',
#                   'daily_pricing_model', 'payment_size_detail', 'default_price', 'default_accrued',)
#         read_only_fields = fields
#
#
# class EvalPortfolioSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Portfolio
#         fields = ('id', 'user_code', 'name', 'short_name', 'notes',)
#         read_only_fields = fields
#
#
# class EvalStrategy1Serializer(serializers.ModelSerializer):
#     class Meta:
#         model = Strategy1
#         fields = ('id', 'user_code', 'name', 'short_name', 'notes',)
#         read_only_fields = fields
#
#
# class EvalStrategy2Serializer(serializers.ModelSerializer):
#     class Meta:
#         model = Strategy2
#         fields = ('id', 'user_code', 'name', 'short_name', 'notes',)
#         read_only_fields = fields
#
#
# class EvalStrategy3Serializer(serializers.ModelSerializer):
#     class Meta:
#         model = Strategy3
#         fields = ('id', 'user_code', 'name', 'short_name', 'notes',)
#         read_only_fields = fields
#
#
# class EvalTransactionSerializer(serializers.ModelSerializer):
#     transaction_class = serializers.PrimaryKeyRelatedField(read_only=True)
#     complex_transaction = serializers.PrimaryKeyRelatedField(read_only=True)
#     portfolio = EvalPortfolioSerializer(read_only=True)
#     transaction_currency = EvalCurrencySerializer(read_only=True)
#     instrument = EvalInstrumentSerializer(read_only=True)
#     settlement_currency = EvalCurrencySerializer(read_only=True)
#     account_cash = EvalAccountSerializer(read_only=True)
#     account_position = EvalAccountSerializer(read_only=True)
#     account_interim = EvalAccountSerializer(read_only=True)
#     strategy1_position = EvalStrategy1Serializer(read_only=True)
#     strategy1_cash = EvalStrategy1Serializer(read_only=True)
#     strategy2_position = EvalStrategy2Serializer(read_only=True)
#     strategy2_cash = EvalStrategy2Serializer(read_only=True)
#     strategy3_position = EvalStrategy3Serializer(read_only=True)
#     strategy3_cash = EvalStrategy3Serializer(read_only=True)
#
#     class Meta:
#         model = Transaction
#         fields = ('id', 'transaction_code',
#                   'transaction_class',
#                   'complex_transaction', 'complex_transaction_order',
#                   'portfolio',
#                   'transaction_currency', 'instrument',
#                   'position_size_with_sign',
#                   'settlement_currency', 'cash_consideration',
#                   'principal_with_sign', 'carry_with_sign', 'overheads_with_sign',
#                   'accounting_date', 'cash_date', 'transaction_date',
#                   'account_cash', 'account_position', 'account_interim',
#                   'strategy1_position', 'strategy1_cash',
#                   'strategy2_position', 'strategy2_cash',
#                   'strategy3_position', 'strategy3_cash',
#                   'reference_fx_rate',
#                   # 'is_locked', 'is_canceled',
#                   'factor', 'trade_price',
#                   'principal_amount', 'carry_amount', 'overheads',
#                   # 'responsible', 'counterparty',
#                   )
#         read_only_fields = fields
