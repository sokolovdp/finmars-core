from __future__ import unicode_literals

from django.contrib import admin
from django.contrib.contenttypes.models import ContentType

from poms.accounts.models import Account
from poms.audit.admin import HistoricalAdmin
from poms.common.admin import ClassModelAdmin
from poms.counterparties.models import Responsible, Counterparty
from poms.currencies.models import Currency
from poms.instruments.models import Instrument, PaymentSizeDetail, DailyPricingModel, InstrumentType
from poms.obj_attrs.admin import AbstractAttributeTypeAdmin, AbstractAttributeInline, \
    AbstractAttributeTypeOptionInline, AbstractAttributeTypeClassifierInline
from poms.obj_perms.admin import UserObjectPermissionInline, \
    GroupObjectPermissionInline
from poms.portfolios.models import Portfolio
from poms.strategies.models import Strategy3, Strategy2, Strategy1
from poms.transactions.models import TransactionClass, Transaction, TransactionType, TransactionTypeInput, \
    TransactionAttributeType, ActionClass, EventToHandle, \
    ExternalCashFlow, ExternalCashFlowStrategy, NotificationClass, EventClass, PeriodicityGroup, \
    TransactionTypeActionInstrument, \
    TransactionTypeActionTransaction, ComplexTransaction, TransactionTypeGroup

admin.site.register(TransactionClass, ClassModelAdmin)
admin.site.register(ActionClass, ClassModelAdmin)
admin.site.register(EventClass, ClassModelAdmin)
admin.site.register(NotificationClass, ClassModelAdmin)
admin.site.register(PeriodicityGroup, ClassModelAdmin)


class TransactionTypeGroupAdmin(HistoricalAdmin):
    model = TransactionTypeGroup
    list_display = ['id', 'name', 'master_user']
    raw_id_fields = ['master_user']
    inlines = [
        UserObjectPermissionInline,
        GroupObjectPermissionInline,
    ]


admin.site.register(TransactionTypeGroup, TransactionTypeGroupAdmin)


# admin.site.register(TransactionTypeGroupUserObjectPermission, UserObjectPermissionAdmin)
# admin.site.register(TransactionTypeGroupGroupObjectPermission, GroupObjectPermissionAdmin)


class TransactionTypeInputInline(admin.TabularInline):
    model = TransactionTypeInput
    extra = 0
    fields = ('id', 'name', 'value_type', 'content_type', 'verbose_name', 'order',)
    readonly_fields = ('id',)

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name == 'content_type':
            qs = kwargs.get('queryset', db_field.remote_field.model.objects)
            models = [Account, Instrument, InstrumentType, Currency, Counterparty, Responsible, Strategy1, Strategy2,
                      Strategy3, DailyPricingModel, PaymentSizeDetail, Portfolio]
            ctypes = [ContentType.objects.get_for_model(model).pk for model in models]
            kwargs['queryset'] = qs.filter(pk__in=ctypes)
        return super(TransactionTypeInputInline, self).formfield_for_foreignkey(db_field, request=request, **kwargs)

        # if db_field.name == 'permissions':
        #     qs = kwargs.get('queryset', db_field.remote_field.model.objects)
        #     kwargs['queryset'] = qs.select_related('content_type')
        # return super(GroupAdmin, self).formfield_for_manytomany(db_field, request=request, **kwargs)


# class TransactionTypeItemInline(admin.StackedInline):
#     model = TransactionTypeItem
#     extra = 0
#
#     fields = (
#         'order', 'transaction_class',
#         ('instrument', 'instrument_input'),
#         ('transaction_currency', 'transaction_currency_input'),
#         ('position_size_with_sign', 'position_size_with_sign_expr'),
#         ('settlement_currency', 'settlement_currency_input'),
#         ('cash_consideration', 'cash_consideration_expr'),
#         ('account_position', 'account_position_input'),
#         ('account_cash', 'account_cash_input'),
#         ('account_interim', 'account_interim_input'),
#
#         ('strategy1_position', 'strategy1_position_input'),
#         ('strategy1_cash', 'strategy1_cash_input'),
#         ('strategy2_position', 'strategy2_position_input'),
#         ('strategy2_cash', 'strategy2_cash_input'),
#         ('strategy3_position', 'strategy3_position_input'),
#         ('strategy3_cash', 'strategy3_cash_input'),
#
#         ('accounting_date', 'accounting_date_expr'),
#         ('cash_date', 'cash_date_expr'),
#     )


def input_filter_by_master_user(form, field_name, master_user):
    f = form.base_fields[field_name]
    f.queryset = f.queryset.filter(master_user=master_user)


def input_filter_owner(form, field_name, transaction_type):
    f = form.base_fields[field_name]
    f.queryset = f.queryset.filter(transaction_type=transaction_type)


class TransactionTypeActionInstrumentInline(admin.StackedInline):
    model = TransactionTypeActionInstrument
    extra = 0
    fields = (
        'order',
        'user_code',
        ('name', 'short_name', 'public_name',),
        'notes',
        ('instrument_type', 'instrument_type_input',),
        ('pricing_currency', 'pricing_currency_input',),
        'price_multiplier',
        ('accrued_currency', 'accrued_currency_input',),
        'accrued_multiplier',
        ('daily_pricing_model', 'daily_pricing_model_input',),
        ('payment_size_detail', 'payment_size_detail_input',),
        ('default_price', 'default_accrued',),
        ('user_text_1', 'user_text_2', 'user_text_3',),
    )

    raw_id_fields = (
        'instrument_type', 'instrument_type_input',
        'pricing_currency', 'pricing_currency_input',
        'accrued_currency', 'accrued_currency_input',
        'daily_pricing_model_input',
        'payment_size_detail_input',
    )

    # def get_formset(self, request, obj=None, **kwargs):
    #     f = super(TransactionTypeActionInstrumentInline, self).get_formset(request, obj=obj, **kwargs)
    #     input_filter_by_master_user(f.form, 'instrument_type', obj.master_user)
    #     input_filter_owner(f.form, 'instrument_type_input', obj)
    #     input_filter_by_master_user(f.form, 'pricing_currency', obj.master_user)
    #     input_filter_owner(f.form, 'pricing_currency_input', obj)
    #     input_filter_by_master_user(f.form, 'accrued_currency', obj.master_user)
    #     input_filter_owner(f.form, 'accrued_currency_input', obj)
    #     return f

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name.endswith('_input'):
            qs = kwargs.get('queryset', db_field.remote_field.model.objects)
            kwargs['queryset'] = qs.select_related('content_type')
        return super(TransactionTypeActionInstrumentInline, self).formfield_for_foreignkey(db_field, request=request,
                                                                                           **kwargs)


class TransactionTypeActionTransactionInline(admin.StackedInline):
    model = TransactionTypeActionTransaction
    extra = 0
    fields = (
        'order',
        'transaction_class',
        ('portfolio', 'portfolio_input'),
        ('instrument', 'instrument_input', 'instrument_phantom'),
        ('transaction_currency', 'transaction_currency_input'),
        'position_size_with_sign',
        ('settlement_currency', 'settlement_currency_input'),
        'cash_consideration',
        'principal_with_sign',
        'carry_with_sign',
        'overheads_with_sign',
        ('account_position', 'account_position_input'),
        ('account_cash', 'account_cash_input'),
        ('account_interim', 'account_interim_input'),
        'accounting_date',
        'cash_date',
        ('strategy1_position', 'strategy1_position_input'),
        ('strategy1_cash', 'strategy1_cash_input'),
        ('strategy2_position', 'strategy2_position_input'),
        ('strategy2_cash', 'strategy2_cash_input'),
        ('strategy3_position', 'strategy3_position_input'),
        ('strategy3_cash', 'strategy3_cash_input'),
        'factor',
        'trade_price',
        'principal_amount',
        'carry_amount',
        'overheads',
        ('responsible', 'responsible_input'),
        ('counterparty', 'counterparty_input'),
    )
    raw_id_fields = (
        'portfolio',
        'instrument',
        'transaction_currency',
        'settlement_currency',
        'account_position',
        'account_cash',
        'account_interim',
        'strategy1_position',
        'strategy1_cash',
        'strategy2_position',
        'strategy2_cash',
        'strategy3_position',
        'strategy3_cash',
        'responsible',
        'counterparty',
    )

    # def get_formset(self, request, obj=None, **kwargs):
    #     f = super(TransactionTypeActionTransactionInline, self).get_formset(request, obj=obj, **kwargs)
    #     input_filter_by_master_user(f.form, 'portfolio', obj.master_user)
    #     input_filter_owner(f.form, 'portfolio_input', obj)
    #     input_filter_by_master_user(f.form, 'instrument', obj.master_user)
    #     input_filter_owner(f.form, 'instrument_input', obj)
    #     input_filter_owner(f.form, 'instrument_phantom', obj)
    #     input_filter_by_master_user(f.form, 'transaction_currency', obj.master_user)
    #     input_filter_owner(f.form, 'transaction_currency_input', obj)
    #     input_filter_by_master_user(f.form, 'settlement_currency', obj.master_user)
    #     input_filter_owner(f.form, 'settlement_currency_input', obj)
    #     input_filter_by_master_user(f.form, 'account_position', obj.master_user)
    #     input_filter_owner(f.form, 'account_position_input', obj)
    #     input_filter_by_master_user(f.form, 'account_cash', obj.master_user)
    #     input_filter_owner(f.form, 'account_cash_input', obj)
    #     input_filter_by_master_user(f.form, 'account_interim', obj.master_user)
    #     input_filter_owner(f.form, 'account_interim_input', obj)
    #     input_filter_by_master_user(f.form, 'strategy1_position', obj.master_user)
    #     input_filter_owner(f.form, 'strategy1_position_input', obj)
    #     input_filter_by_master_user(f.form, 'strategy2_position', obj.master_user)
    #     input_filter_owner(f.form, 'strategy2_position_input', obj)
    #     input_filter_by_master_user(f.form, 'strategy3_position', obj.master_user)
    #     input_filter_owner(f.form, 'strategy3_position_input', obj)
    #     input_filter_by_master_user(f.form, 'responsible', obj.master_user)
    #     input_filter_owner(f.form, 'responsible_input', obj)
    #     input_filter_by_master_user(f.form, 'counterparty', obj.master_user)
    #     input_filter_owner(f.form, 'counterparty_input', obj)
    #     return f

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name.endswith('_input'):
            qs = kwargs.get('queryset', db_field.remote_field.model.objects)
            kwargs['queryset'] = qs.select_related('content_type')
        return super(TransactionTypeActionTransactionInline, self).formfield_for_foreignkey(db_field, request=request,
                                                                                            **kwargs)


class EventToHandleInline(admin.StackedInline):
    model = EventToHandle
    list_display = ['id', 'master_user', 'name']
    raw_id_fields = ['master_user']
    extra = 0


class TransactionTypeAdmin(HistoricalAdmin):
    model = TransactionType
    list_display = ['id', 'name', 'master_user']
    list_select_related = ['master_user']
    raw_id_fields = ['master_user', 'group']
    filter_horizontal = ['instrument_types']
    inlines = [
        TransactionTypeInputInline,
        TransactionTypeActionInstrumentInline,
        TransactionTypeActionTransactionInline,
        EventToHandleInline,
        UserObjectPermissionInline,
        GroupObjectPermissionInline,
    ]

    def get_inline_instances(self, request, obj=None):
        if obj:
            return super(TransactionTypeAdmin, self).get_inline_instances(request, obj)
        return []

    def get_readonly_fields(self, request, obj=None):
        fields = super(TransactionTypeAdmin, self).get_readonly_fields(request, obj)
        if obj:
            fields += ('master_user',)
        else:
            fields += ('instrument_types',)
        return fields

    def get_formset(self, request, obj=None, **kwargs):
        f = super(TransactionTypeAdmin, self).get_formset(request, obj=obj, **kwargs)
        input_filter_by_master_user(f.form, 'instrument_types', obj.master_user)
        input_filter_by_master_user(f.form, 'portfolios', obj.master_user)
        return f


admin.site.register(TransactionType, TransactionTypeAdmin)


# admin.site.register(TransactionTypeUserObjectPermission, UserObjectPermissionAdmin)
# admin.site.register(TransactionTypeGroupObjectPermission, GroupObjectPermissionAdmin)


class ComplexTransactionAdmin(HistoricalAdmin):
    model = ComplexTransaction
    list_select_related = ['transaction_type', 'transaction_type__master_user']
    list_display = ['id', 'transaction_type', 'master_user', 'code']
    raw_id_fields = ['transaction_type']

    def master_user(self, obj):
        return obj.transaction_type.master_user

    master_user.admin_order_field = 'transaction_type__master_user'


admin.site.register(ComplexTransaction, ComplexTransactionAdmin)


# class EventToHandleAdmin(HistoricalAdmin):
#     model = EventToHandle
#     list_display = ['id', 'master_user', 'name', 'transaction_type']
#     raw_id_fields = ['master_user', 'transaction_type']
#
#
# admin.site.register(EventToHandle, HistoricalAdmin)


# class TransactionAttributeInline(AbstractAttributeInline):
#     model = TransactionAttribute
#     fields = ['attribute_type', 'value_string', 'value_float', 'value_date']
#     raw_id_fields = ['attribute_type']


class TransactionAdmin(HistoricalAdmin):
    model = Transaction
    list_select_related = ['master_user', 'complex_transaction', 'transaction_class',
                           'instrument', 'transaction_currency', 'settlement_currency',
                           'portfolio', 'account_cash', 'account_position', 'account_interim',
                           'strategy1_position', 'strategy1_cash', 'strategy2_position', 'strategy2_cash',
                           'strategy3_position', 'strategy3_cash']
    list_display = ['id', 'master_user', 'is_canceled',
                    'complex_transaction', 'complex_transaction_order',
                    'transaction_class',
                    'transaction_date', 'accounting_date', 'cash_date',
                    'instrument', 'transaction_currency',
                    'position_size_with_sign',
                    'settlement_currency', 'cash_consideration',
                    'principal_with_sign', 'carry_with_sign', 'overheads_with_sign',
                    'account_cash', 'account_position', 'account_interim',
                    'strategy1_position', 'strategy1_cash', 'strategy2_position', 'strategy2_cash',
                    'strategy3_position', 'strategy3_cash',
                    ]
    list_filter = ['is_canceled']
    ordering = ['transaction_date', 'id']
    date_hierarchy = 'transaction_date'
    raw_id_fields = ['master_user', 'complex_transaction', 'portfolio', 'instrument', 'transaction_currency',
                     'settlement_currency',
                     'account_position', 'account_cash', 'account_interim', 'responsible', 'counterparty',
                     'strategy1_position', 'strategy1_cash', 'strategy2_position', 'strategy2_cash',
                     'strategy3_position', 'strategy3_cash', ]
    inlines = [
        AbstractAttributeInline,
    ]
    fields = (
        'master_user',
        'transaction_code',
        ('complex_transaction', 'complex_transaction_order'),
        'transaction_class',
        ('instrument', 'transaction_currency', 'position_size_with_sign'),
        ('settlement_currency', 'cash_consideration'),
        ('principal_with_sign', 'carry_with_sign', 'overheads_with_sign'),
        ('accounting_date', 'cash_date'),
        'portfolio',
        ('account_position', 'account_cash', 'account_interim'),
        ('strategy1_position', 'strategy1_cash'),
        ('strategy2_position', 'strategy2_cash'),
        ('strategy3_position', 'strategy3_cash'),
        ('responsible', 'counterparty'),
        'reference_fx_rate',
        'is_locked',
        'is_canceled',
        'factor',
        'trade_price',
        'principal_amount', 'carry_amount', 'overheads',
    )


admin.site.register(Transaction, TransactionAdmin)


class TransactionAttributeTypeAdmin(AbstractAttributeTypeAdmin):
    list_display = ['id', 'master_user', 'name', 'value_type']
    list_select_related = ['master_user']
    raw_id_fields = ['master_user']
    inlines = [
        AbstractAttributeTypeClassifierInline,
        AbstractAttributeTypeOptionInline,
        UserObjectPermissionInline,
        GroupObjectPermissionInline,
    ]


admin.site.register(TransactionAttributeType, TransactionAttributeTypeAdmin)


# admin.site.register(TransactionAttributeTypeOption, AbstractAttributeTypeOptionAdmin)
# admin.site.register(TransactionAttributeTypeUserObjectPermission, UserObjectPermissionAdmin)
# admin.site.register(TransactionAttributeTypeGroupObjectPermission, GroupObjectPermissionAdmin)


class ExternalCashFlowStrategyInline(admin.TabularInline):
    model = ExternalCashFlowStrategy
    raw_id_fields = ['strategy1', 'strategy2', 'strategy3']
    extra = 0


class ExternalCashFlowAdmin(HistoricalAdmin):
    model = ExternalCashFlow
    inlines = [ExternalCashFlowStrategyInline]
    raw_id_fields = ['portfolio', 'account', 'currency']


admin.site.register(ExternalCashFlow, ExternalCashFlowAdmin)
