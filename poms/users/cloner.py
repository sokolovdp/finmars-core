import logging
from collections import defaultdict

from django.conf import settings
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from poms.accounts.models import AccountType, Account
from poms.chats.models import ThreadGroup
from poms.counterparties.models import CounterpartyGroup, Counterparty, ResponsibleGroup, Responsible
from poms.currencies.models import Currency, CurrencyHistory
from poms.instruments.models import PricingPolicy, DailyPricingModel, InstrumentClass, AccrualCalculationModel, \
    PaymentSizeDetail, Periodicity, CostMethod, InstrumentType, Instrument, ManualPricingFormula, PriceHistory, \
    AccrualCalculationSchedule, InstrumentFactorSchedule, EventScheduleConfig, EventSchedule, EventScheduleAction
from poms.integrations.models import PriceDownloadScheme, ProviderClass, AccrualScheduleDownloadMethod, \
    FactorScheduleDownloadMethod, InstrumentDownloadScheme, InstrumentDownloadSchemeInput, \
    CurrencyMapping, InstrumentTypeMapping, AccrualCalculationModelMapping, \
    PeriodicityMapping
from poms.portfolios.models import Portfolio
from poms.strategies.models import Strategy1Group, Strategy1Subgroup, Strategy1, Strategy2Group, Strategy2Subgroup, \
    Strategy2, Strategy3Group, Strategy3Subgroup, Strategy3
from poms.tags.models import Tag
from poms.transactions.models import TransactionClass, ActionClass, EventClass, NotificationClass, TransactionTypeGroup, \
    TransactionType, TransactionTypeInput, TransactionTypeActionInstrument, TransactionTypeActionTransaction
from poms.ui.models import TemplateListLayout, TemplateEditLayout
from poms.users.models import Group

_l = logging.getLogger('poms.users.cloner')


class FullDataCloner(object):
    def __init__(self, source_master_user):
        self._source_master_user = source_master_user
        self._target_master_user = None

        self._pk_map = defaultdict(dict)
        self._source_objects = defaultdict(dict)
        self._target_objects = defaultdict(dict)

    @transaction.atomic()
    def clone(self):
        _l.debug('clone: master_user=%s', self._source_master_user.pk)
        self._target_master_user = self._simple_clone(None, self._source_master_user, 'name', 'language', 'timezone')

        self._load_consts()

        self._users_1()
        self._accounts()
        self._chats()
        self._counterparties()

        self._instruments_1()
        self._integrations_1()

        self._currencies()

        self._instruments_2()

        self._portfolios_1()
        self._strategies_1()

        self._transactions_1()

        # the end
        self._instruments_3()
        self._integrations_2()

        self._simple_clone(self._target_master_user, self._source_master_user,
                           'currency',
                           'system_currency',
                           'account_type',
                           'account',
                           'counterparty_group',
                           'counterparty',
                           'responsible_group',
                           'responsible',
                           'instrument_type',
                           'portfolio',
                           'strategy1_group',
                           'strategy1_subgroup',
                           'strategy1',
                           'strategy2_group',
                           'strategy2_subgroup',
                           'strategy2',
                           'strategy3_group',
                           'strategy3_subgroup',
                           'strategy3',
                           'thread_group',
                           'notification_business_days'
                           )

        self._tags()
        self._ui()

        transaction.set_rollback(True)

    def _load_consts(self):
        for source in ContentType.objects.all():
            self._add_pk_map(source, source)

        for source in Permission.objects.all():
            self._add_pk_map(source, source)

        for source in InstrumentClass.objects.all():
            self._add_pk_map(source, source)

        for source in DailyPricingModel.objects.all():
            self._add_pk_map(source, source)

        for source in AccrualCalculationModel.objects.all():
            self._add_pk_map(source, source)

        for source in PaymentSizeDetail.objects.all():
            self._add_pk_map(source, source)

        for source in Periodicity.objects.all():
            self._add_pk_map(source, source)

        for source in CostMethod.objects.all():
            self._add_pk_map(source, source)

        for source in ProviderClass.objects.all():
            self._add_pk_map(source, source)

        for source in FactorScheduleDownloadMethod.objects.all():
            self._add_pk_map(source, source)

        for source in AccrualScheduleDownloadMethod.objects.all():
            self._add_pk_map(source, source)

        for source in TransactionClass.objects.all():
            self._add_pk_map(source, source)

        for source in ActionClass.objects.all():
            self._add_pk_map(source, source)

        for source in EventClass.objects.all():
            self._add_pk_map(source, source)

        for source in NotificationClass.objects.all():
            self._add_pk_map(source, source)

    def _users_1(self):
        # _l.debug('clone %s', Group)
        # for source in Group.objects.filter(master_user=self._source_master_user):
        #     self._simple_clone(None, source, 'master_user', 'name')
        self._simple_list_clone(Group, None, 'master_user', 'name')

    def _accounts(self):
        # _l.debug('clone %s', AccountType)
        # for source in AccountType.objects.filter(master_user=self._source_master_user):
        #     self._simple_clone(None, source, 'master_user', 'user_code', 'name', 'short_name',
        #                        'public_name', 'notes', 'is_deleted', 'show_transaction_details',
        #                        'transaction_details_expr')
        self._simple_list_clone(AccountType, None, 'master_user', 'user_code', 'name', 'short_name',
                                'public_name', 'notes', 'is_deleted', 'show_transaction_details',
                                'transaction_details_expr')

        # _l.debug('clone %s', Account)
        # for source in Account.objects.filter(master_user=self._source_master_user):
        #     self._simple_clone(None, source, 'master_user', 'user_code', 'name', 'short_name',
        #                        'public_name', 'notes', 'is_deleted', 'type', 'is_valid_for_all_portfolios')
        self._simple_list_clone(Account, None, 'master_user', 'user_code', 'name', 'short_name',
                                'public_name', 'notes', 'is_deleted', 'type', 'is_valid_for_all_portfolios')

    def _chats(self):
        # _l.debug('clone %s', ThreadGroup)
        # for source in ThreadGroup.objects.filter(master_user=self._source_master_user):
        #     self._simple_clone(None, source, 'master_user', 'name', 'is_deleted')
        self._simple_list_clone(ThreadGroup, None, 'master_user', 'name', 'is_deleted')

    def _counterparties(self):
        # _l.debug('clone %s', CounterpartyGroup)
        # for source in CounterpartyGroup.objects.filter(master_user=self._source_master_user):
        #     self._simple_clone(None, source, 'master_user', 'user_code', 'name', 'short_name',
        #                        'public_name', 'notes', 'is_deleted')
        self._simple_list_clone(CounterpartyGroup, None, 'master_user', 'user_code', 'name', 'short_name',
                                'public_name', 'notes', 'is_deleted')

        # _l.debug('clone %s', Counterparty)
        # for source in Counterparty.objects.filter(master_user=self._source_master_user):
        #     self._simple_clone(None, source, 'master_user', 'user_code', 'name', 'short_name',
        #                        'public_name', 'notes', 'is_deleted', 'group', 'is_valid_for_all_portfolios')
        self._simple_list_clone(Counterparty, None, 'master_user', 'user_code', 'name', 'short_name',
                                'public_name', 'notes', 'is_deleted', 'group', 'is_valid_for_all_portfolios')

        # _l.debug('clone %s', ResponsibleGroup)
        # for source in ResponsibleGroup.objects.filter(master_user=self._source_master_user):
        #     self._simple_clone(None, source, 'master_user', 'user_code', 'name', 'short_name',
        #                        'public_name', 'notes', 'is_deleted')
        self._simple_list_clone(ResponsibleGroup, None, 'master_user', 'user_code', 'name', 'short_name',
                                'public_name', 'notes', 'is_deleted')

        # _l.debug('clone %s', Responsible)
        # for source in Responsible.objects.filter(master_user=self._source_master_user):
        #     self._simple_clone(None, source, 'master_user', 'user_code', 'name', 'short_name',
        #                        'public_name', 'notes', 'is_deleted', 'group', 'is_valid_for_all_portfolios')
        self._simple_list_clone(Responsible, None, 'master_user', 'user_code', 'name', 'short_name',
                                'public_name', 'notes', 'is_deleted', 'group', 'is_valid_for_all_portfolios')

    def _currencies(self):
        # _l.debug('clone %s', Currency)
        # for source in Currency.objects.filter(master_user=self._source_master_user):
        #     self._simple_clone(None, source, 'master_user', 'user_code', 'name', 'short_name',
        #                        'public_name', 'notes', 'is_deleted', 'reference_for_pricing', 'daily_pricing_model',
        #                        'price_download_scheme')
        self._simple_list_clone(Currency, None, 'master_user', 'user_code', 'name', 'short_name',
                                'public_name', 'notes', 'is_deleted', 'reference_for_pricing', 'daily_pricing_model',
                                'price_download_scheme')

        # _l.debug('clone %s', CurrencyHistory)
        # for source in CurrencyHistory.objects.filter(currency__master_user=self._source_master_user):
        #     self._simple_clone(None, source, 'currency', 'pricing_policy', 'date', 'fx_rate',
        #                        pk_map=False)
        self._simple_list_clone(CurrencyHistory, 'currency__master_user', 'currency', 'pricing_policy', 'date',
                                'fx_rate', pk_map=False)

    def _instruments_1(self):
        # _l.debug('clone %s', PricingPolicy)
        # for source in PricingPolicy.objects.filter(master_user=self._source_master_user):
        #     self._simple_clone(None, source, 'master_user', 'user_code', 'name', 'short_name',
        #                        'public_name', 'notes', 'expr')
        self._simple_list_clone(PricingPolicy, None, 'master_user', 'user_code', 'name', 'short_name',
                                'public_name', 'notes', 'expr')

    def _instruments_2(self):
        # _l.debug('clone %s', InstrumentType)
        # for source in InstrumentType.objects.filter(master_user=self._source_master_user):
        #     self._simple_clone(None, source, 'master_user', 'user_code', 'name', 'short_name',
        #                        'public_name', 'notes', 'is_deleted', 'instrument_class', store=True)
        self._simple_list_clone(InstrumentType, None, 'master_user', 'user_code', 'name', 'short_name',
                                'public_name', 'notes', 'is_deleted', 'instrument_class', store=True)

        # _l.debug('clone %s', Instrument)
        # for source in Instrument.objects.filter(master_user=self._source_master_user):
        #     self._simple_clone(None, source, 'master_user', 'user_code', 'name', 'short_name',
        #                        'public_name', 'notes', 'is_deleted', 'instrument_type', 'is_active',
        #                        'pricing_currency', 'price_multiplier',
        #                        'accrued_currency', 'accrued_multiplier',
        #                        'payment_size_detail',
        #                        'default_price', 'default_accrued',
        #                        'user_text_1', 'user_text_2', 'user_text_3',
        #                        'reference_for_pricing', 'daily_pricing_model', 'price_download_scheme',
        #                        'maturity_date')
        self._simple_list_clone(Instrument, None, 'master_user', 'user_code', 'name', 'short_name',
                                'public_name', 'notes', 'is_deleted', 'instrument_type', 'is_active',
                                'pricing_currency', 'price_multiplier',
                                'accrued_currency', 'accrued_multiplier',
                                'payment_size_detail',
                                'default_price', 'default_accrued',
                                'user_text_1', 'user_text_2', 'user_text_3',
                                'reference_for_pricing', 'daily_pricing_model', 'price_download_scheme',
                                'maturity_date')

        # _l.debug('clone %s', ManualPricingFormula)
        # for source in ManualPricingFormula.objects.filter(instrument__master_user=self._source_master_user):
        #     self._simple_clone(None, source, 'instrument', 'pricing_policy', 'expr', 'notes')
        self._simple_list_clone(ManualPricingFormula, 'instrument__master_user', 'instrument', 'pricing_policy', 'expr',
                                'notes')

        # _l.debug('clone %s', AccrualCalculationSchedule)
        # for source in AccrualCalculationSchedule.objects.filter(instrument__master_user=self._source_master_user):
        #     self._simple_clone(None, source, 'instrument', 'accrual_start_date', 'first_payment_date', 'accrual_size',
        #                        'accrual_calculation_model', 'periodicity', 'periodicity_n', 'notes')
        self._simple_list_clone(AccrualCalculationSchedule, 'instrument__master_user', 'instrument',
                                'accrual_start_date', 'first_payment_date', 'accrual_size',
                                'accrual_calculation_model', 'periodicity', 'periodicity_n', 'notes')

        # _l.debug('clone %s', InstrumentFactorSchedule)
        # for source in InstrumentFactorSchedule.objects.filter(instrument__master_user=self._source_master_user):
        #     self._simple_clone(None, source, 'instrument', 'effective_date', 'factor_value')
        self._simple_list_clone(InstrumentFactorSchedule, 'instrument__master_user', 'instrument', 'effective_date',
                                'factor_value')

        # _l.debug('clone %s', PriceHistory)
        # for source in PriceHistory.objects.filter(instrument__master_user=self._source_master_user):
        #     self._simple_clone(None, source, 'instrument', 'pricing_policy', 'date', 'principal_price', 'accrued_price',
        #                        pk_map=False)
        self._simple_list_clone(PriceHistory, 'instrument__master_user', 'instrument', 'pricing_policy', 'date',
                                'principal_price', 'accrued_price', pk_map=False)

        # _l.debug('clone %s', EventScheduleConfig)
        # for source in EventScheduleConfig.objects.filter(master_user=self._source_master_user):
        #     self._simple_clone(None, source, 'master_user', 'name', 'description', 'notification_class',
        #                        'notify_in_n_days', 'action_text', 'action_is_sent_to_pending',
        #                        'action_is_book_automatic')
        self._simple_list_clone(EventScheduleConfig, None, 'master_user', 'name', 'description', 'notification_class',
                                'notify_in_n_days', 'action_text', 'action_is_sent_to_pending',
                                'action_is_book_automatic')

    def _instruments_3(self):
        # _l.debug('clone %s', InstrumentType)
        # for source in self._source_get_objects(InstrumentType).values():
        #     target_pk = self._get_related_from_pk_map(source, source.pk)
        #     target = self._target_get_object(source, target_pk)
        #     self._simple_clone(target, source, 'one_off_event', 'regular_event', 'factor_same', 'factor_up',
        #                        'factor_down', pk_map=False)
        self._simple_list_clone_2(InstrumentType, None, 'one_off_event', 'regular_event', 'factor_same', 'factor_up',
                                  'factor_down', pk_map=False)

        # _l.debug('clone %s', EventSchedule)
        # for source in EventSchedule.objects.filter(instrument__master_user=self._source_master_user):
        #     self._simple_clone(None, source, 'instrument', 'name', 'description', 'event_class',
        #                        'notification_class', 'effective_date', 'notify_in_n_days',
        #                        'periodicity', 'periodicity_n', 'final_date', 'is_auto_generated',
        #                        'accrual_calculation_schedule', 'factor_schedule')
        self._simple_list_clone(EventSchedule, 'instrument__master_user', 'instrument', 'name', 'description',
                                'event_class',
                                'notification_class', 'effective_date', 'notify_in_n_days',
                                'periodicity', 'periodicity_n', 'final_date', 'is_auto_generated',
                                'accrual_calculation_schedule', 'factor_schedule')

        # _l.debug('clone %s', EventScheduleAction)
        # for source in EventScheduleAction.objects.filter(
        #         event_schedule__instrument__master_user=self._source_master_user):
        #     self._simple_clone(None, source, 'event_schedule', 'transaction_type', 'text', 'is_sent_to_pending',
        #                        'is_book_automatic', 'button_position')
        self._simple_list_clone(EventScheduleAction, 'event_schedule__instrument__master_user', 'event_schedule',
                                'transaction_type', 'text', 'is_sent_to_pending',
                                'is_book_automatic', 'button_position')

    def _integrations_1(self):
        # _l.debug('clone %s', PriceDownloadScheme)
        # for source in PriceDownloadScheme.objects.filter(master_user=self._source_master_user):
        #     self._simple_clone(None, source, 'master_user', 'scheme_name', 'provider',
        #                        'bid0', 'bid1', 'bid2', 'bid_multiplier',
        #                        'ask0', 'ask1', 'ask2', 'ask_multiplier', 'last',
        #                        'last', 'mid', 'mid_multiplier',
        #                        'bid_history', 'bid_history_multiplier',
        #                        'ask_history', 'ask_history_multiplier',
        #                        'mid_history', 'mid_history_multiplier',
        #                        'last_history', 'last_history_multiplier',
        #                        'currency_fxrate', 'currency_fxrate_multiplier')
        self._simple_list_clone(PriceDownloadScheme, None, 'master_user', 'scheme_name', 'provider',
                                'bid0', 'bid1', 'bid2', 'bid_multiplier',
                                'ask0', 'ask1', 'ask2', 'ask_multiplier', 'last',
                                'last', 'mid', 'mid_multiplier',
                                'bid_history', 'bid_history_multiplier',
                                'ask_history', 'ask_history_multiplier',
                                'mid_history', 'mid_history_multiplier',
                                'last_history', 'last_history_multiplier',
                                'currency_fxrate', 'currency_fxrate_multiplier')

    def _integrations_2(self):
        # _l.debug('clone %s', InstrumentDownloadScheme)
        # for source in InstrumentDownloadScheme.objects.filter(master_user=self._source_master_user):
        #     self._simple_clone(None, source, 'master_user', 'scheme_name', 'provider', 'reference_for_pricing',
        #                        'user_code', 'name', 'short_name', 'public_name', 'notes', 'instrument_type',
        #                        'pricing_currency', 'price_multiplier', 'accrued_currency', 'accrued_multiplier',
        #                        'maturity_date', 'user_text_1', 'user_text_2', 'user_text_3', 'payment_size_detail',
        #                        'daily_pricing_model', 'price_download_scheme', 'default_price', 'default_accrued',
        #                        'factor_schedule_method', 'accrual_calculation_schedule_method')
        self._simple_list_clone(InstrumentDownloadScheme, None, 'master_user', 'scheme_name', 'provider',
                                'reference_for_pricing',
                                'user_code', 'name', 'short_name', 'public_name', 'notes', 'instrument_type',
                                'pricing_currency', 'price_multiplier', 'accrued_currency', 'accrued_multiplier',
                                'maturity_date', 'user_text_1', 'user_text_2', 'user_text_3', 'payment_size_detail',
                                'daily_pricing_model', 'price_download_scheme', 'default_price', 'default_accrued',
                                'factor_schedule_method', 'accrual_calculation_schedule_method')

        # _l.debug('clone %s', InstrumentDownloadSchemeInput)
        # for source in InstrumentDownloadSchemeInput.objects.filter(scheme__master_user=self._source_master_user):
        #     self._simple_clone(None, source, 'scheme', 'name', 'field')
        self._simple_list_clone(InstrumentDownloadSchemeInput, 'scheme__master_user', 'scheme', 'name', 'field')

        # _l.debug('clone %s', InstrumentDownloadSchemeAttribute)
        # for source in InstrumentDownloadSchemeAttribute.objects.filter(scheme__master_user=self._source_master_user):
        #     # self._simple_clone(None, source, 'scheme', 'attribute_type', 'value')
        #     pass
        # TODO: uncomment after attributes
        # self._simple_list_clone(InstrumentDownloadSchemeAttribute, 'scheme__master_user', 'scheme', 'attribute_type', 'value')

        # _l.debug('clone %s', CurrencyMapping)
        # for source in CurrencyMapping.objects.filter(master_user=self._source_master_user):
        #     self._simple_clone(None, source, 'master_user', 'provider', 'value', 'currency')
        self._simple_list_clone(CurrencyMapping, None, 'master_user', 'provider', 'value', 'currency')

        # _l.debug('clone %s', InstrumentTypeMapping)
        # for source in InstrumentTypeMapping.objects.filter(master_user=self._source_master_user):
        #     self._simple_clone(None, source, 'master_user', 'provider', 'value', 'instrument_type')
        self._simple_list_clone(InstrumentTypeMapping, None, 'master_user', 'provider', 'value', 'instrument_type')

        # _l.debug('clone %s', InstrumentAttributeValueMapping)
        # for source in InstrumentAttributeValueMapping.objects.filter(master_user=self._source_master_user):
        #     # self._simple_clone(None, source, 'master_user', 'provider', 'value', 'attribute_type', 'value_string',
        #     #                    'value_float', 'value_date', 'classifier')
        #     pass
        # TODO: uncomment after attributes
        # self._simple_list_clone(InstrumentAttributeValueMapping, None, 'master_user', 'provider', 'value',
        #                         'attribute_type', 'value_string', 'value_float', 'value_date', 'classifier')

        # _l.debug('clone %s', AccrualCalculationModelMapping)
        # for source in AccrualCalculationModelMapping.objects.filter(master_user=self._source_master_user):
        #     self._simple_clone(None, source, 'master_user', 'provider', 'value', 'accrual_calculation_model')
        self._simple_list_clone(AccrualCalculationModelMapping, None, 'master_user', 'provider', 'value',
                                'accrual_calculation_model')

        # _l.debug('clone %s', PeriodicityMapping)
        # for source in PeriodicityMapping.objects.filter(master_user=self._source_master_user):
        #     self._simple_clone(None, source, 'master_user', 'provider', 'value', 'periodicity')
        self._simple_list_clone(PeriodicityMapping, None, 'master_user', 'provider', 'value', 'periodicity')

    def _portfolios_1(self):
        # _l.debug('clone %s', Portfolio)
        # for source in Portfolio.objects.filter(master_user=self._source_master_user):
        #     self._simple_clone(None, source, 'master_user', 'user_code', 'name', 'short_name',
        #                        'public_name', 'notes', 'is_deleted', store=True)
        self._simple_list_clone(Portfolio, None, 'master_user', 'user_code', 'name', 'short_name',
                                'public_name', 'notes', 'is_deleted', store=True)

    def _portfolios_2(self):
        # _l.debug('clone %s', Portfolio)
        # for source in self._source_get_objects(Portfolio).values():
        #     target_pk = self._get_related_from_pk_map(source, source.pk)
        #     target = self._target_get_object(source, target_pk)
        #     self._simple_clone(target, source, 'accounts', 'responsibles', 'counterparties', 'transaction_types',
        #                        pk_map=False)
        self._simple_list_clone_2(Portfolio, None, 'accounts', 'responsibles', 'counterparties', 'transaction_types',
                                  pk_map=False)

    def _strategies_1(self):
        # _l.debug('clone %s', Strategy1Group)
        # for source in Strategy1Group.objects.filter(master_user=self._source_master_user):
        #     self._simple_clone(None, source, 'master_user', 'user_code', 'name', 'short_name',
        #                        'public_name', 'notes', 'is_deleted')
        self._simple_list_clone(Strategy1Group, None, 'master_user', 'user_code', 'name', 'short_name',
                                'public_name', 'notes', 'is_deleted')

        # _l.debug('clone %s', Strategy1Subgroup)
        # for source in Strategy1Subgroup.objects.filter(group__master_user=self._source_master_user):
        #     self._simple_clone(None, source, 'master_user', 'group', 'user_code', 'name', 'short_name',
        #                        'public_name', 'notes', 'is_deleted')
        self._simple_list_clone(Strategy1Subgroup, 'group__master_user', 'master_user', 'group', 'user_code', 'name',
                                'short_name',
                                'public_name', 'notes', 'is_deleted')

        # _l.debug('clone %s', Strategy1)
        # for source in Strategy1.objects.filter(subgroup__group__master_user=self._source_master_user):
        #     self._simple_clone(None, source, 'master_user', 'subgroup', 'user_code', 'name', 'short_name',
        #                        'public_name', 'notes', 'is_deleted')
        self._simple_list_clone(Strategy1, 'subgroup__group__master_user', 'master_user', 'subgroup', 'user_code',
                                'name', 'short_name', 'public_name', 'notes', 'is_deleted')

        # _l.debug('clone %s', Strategy2Group)
        # for source in Strategy2Group.objects.filter(master_user=self._source_master_user):
        #     self._simple_clone(None, source, 'master_user', 'user_code', 'name', 'short_name',
        #                        'public_name', 'notes', 'is_deleted')
        self._simple_list_clone(Strategy2Group, None, 'master_user', 'user_code', 'name', 'short_name',
                                'public_name', 'notes', 'is_deleted')

        # _l.debug('clone %s', Strategy2Subgroup)
        # for source in Strategy2Subgroup.objects.filter(group__master_user=self._source_master_user):
        #     self._simple_clone(Strategy2Subgroup, source, 'master_user', 'group', 'user_code', 'name', 'short_name',
        #                        'public_name', 'notes', 'is_deleted')
        self._simple_list_clone(Strategy2Subgroup, 'group__master_user', 'master_user', 'group', 'user_code', 'name',
                                'short_name', 'public_name', 'notes', 'is_deleted')

        # _l.debug('clone %s', Strategy2)
        # for source in Strategy2.objects.filter(subgroup__group__master_user=self._source_master_user):
        #     self._simple_clone(None, source, 'master_user', 'subgroup', 'user_code', 'name', 'short_name',
        #                        'public_name', 'notes', 'is_deleted')
        self._simple_list_clone(Strategy2, 'subgroup__group__master_user', 'master_user', 'subgroup', 'user_code',
                                'name', 'short_name', 'public_name', 'notes', 'is_deleted')

        # _l.debug('clone %s', Strategy3Group)
        # for source in Strategy3Group.objects.filter(master_user=self._source_master_user):
        #     self._simple_clone(None, source, 'master_user', 'user_code', 'name', 'short_name',
        #                        'public_name', 'notes', 'is_deleted')
        self._simple_list_clone(Strategy3Group, None, 'master_user', 'user_code', 'name', 'short_name',
                                'public_name', 'notes', 'is_deleted')

        # _l.debug('clone %s', Strategy3Subgroup)
        # for source in Strategy3Subgroup.objects.filter(group__master_user=self._source_master_user):
        #     self._simple_clone(None, source, 'master_user', 'group', 'user_code', 'name', 'short_name',
        #                        'public_name', 'notes', 'is_deleted')
        self._simple_list_clone(Strategy3Subgroup, 'group__master_user', 'master_user', 'group', 'user_code', 'name',
                                'short_name', 'public_name', 'notes', 'is_deleted')

        # _l.debug('clone %s', Strategy3)
        # for source in Strategy3.objects.filter(subgroup__group__master_user=self._source_master_user):
        #     self._simple_clone(None, source, 'master_user', 'subgroup', 'user_code', 'name', 'short_name',
        #                        'public_name', 'notes', 'is_deleted')
        self._simple_list_clone(Strategy3, 'subgroup__group__master_user', 'master_user', 'subgroup', 'user_code',
                                'name', 'short_name', 'public_name', 'notes', 'is_deleted')

    def _transactions_1(self):
        # _l.debug('clone %s', TransactionTypeGroup)
        # for source in TransactionTypeGroup.objects.filter(master_user=self._source_master_user):
        #     self._simple_clone(None, source, 'master_user', 'user_code', 'name', 'short_name',
        #                        'public_name', 'notes', 'is_deleted')
        self._simple_list_clone(TransactionTypeGroup, None, 'master_user', 'user_code', 'name', 'short_name',
                                'public_name', 'notes', 'is_deleted')

        # _l.debug('clone %s', TransactionType)
        # for source in TransactionType.objects.filter(master_user=self._source_master_user):
        #     self._simple_clone(None, source, 'master_user', 'user_code', 'name', 'short_name',
        #                        'public_name', 'notes', 'is_deleted', 'group', 'display_expr', 'instrument_types',
        #                        'is_valid_for_all_portfolios', 'is_valid_for_all_instruments',
        #                        'book_transaction_layout_json')
        self._simple_list_clone(TransactionType, None, 'master_user', 'user_code', 'name', 'short_name',
                                'public_name', 'notes', 'is_deleted', 'group', 'display_expr', 'instrument_types',
                                'is_valid_for_all_portfolios', 'is_valid_for_all_instruments',
                                'book_transaction_layout_json')

        # _l.debug('clone %s', TransactionTypeInput)
        # for source in TransactionTypeInput.objects.filter(transaction_type__master_user=self._source_master_user):
        #     self._simple_clone(None, source, 'transaction_type', 'name', 'verbose_name', 'value_type', 'content_type',
        #                        'order', 'is_fill_from_context', 'value', 'account', 'instrument_type', 'instrument',
        #                        'currency', 'counterparty', 'responsible', 'portfolio', 'strategy1', 'strategy2',
        #                        'strategy3', 'daily_pricing_model', 'payment_size_detail', 'price_download_scheme')
        self._simple_list_clone(TransactionTypeInput, 'transaction_type__master_user',
                                'transaction_type', 'name', 'verbose_name', 'value_type', 'content_type',
                                'order', 'is_fill_from_context', 'value', 'account', 'instrument_type', 'instrument',
                                'currency', 'counterparty', 'responsible', 'portfolio', 'strategy1', 'strategy2',
                                'strategy3', 'daily_pricing_model', 'payment_size_detail', 'price_download_scheme')

        # _l.debug('clone %s', TransactionTypeActionInstrument)
        # for source in TransactionTypeActionInstrument.objects.filter(
        #         transaction_type__master_user=self._source_master_user):
        #     self._simple_clone(None, source, 'transaction_type', 'order', 'action_notes',
        #                        'user_code', 'name', 'public_name', 'short_name', 'notes', 'instrument_type',
        #                        'instrument_type_input', 'pricing_currency', 'pricing_currency_input',
        #                        'price_multiplier', 'accrued_currency', 'accrued_currency_input', 'accrued_multiplier',
        #                        'payment_size_detail', 'payment_size_detail_input', 'default_price', 'default_accrued',
        #                        'user_text_1', 'user_text_2', 'user_text_3', 'reference_for_pricing',
        #                        'daily_pricing_model', 'daily_pricing_model_input', 'price_download_scheme',
        #                        'price_download_scheme_input', 'maturity_date')
        self._simple_list_clone(TransactionTypeActionInstrument, 'transaction_type__master_user',
                                'transaction_type', 'order', 'action_notes',
                                'user_code', 'name', 'public_name', 'short_name', 'notes', 'instrument_type',
                                'instrument_type_input', 'pricing_currency', 'pricing_currency_input',
                                'price_multiplier', 'accrued_currency', 'accrued_currency_input', 'accrued_multiplier',
                                'payment_size_detail', 'payment_size_detail_input', 'default_price', 'default_accrued',
                                'user_text_1', 'user_text_2', 'user_text_3', 'reference_for_pricing',
                                'daily_pricing_model', 'daily_pricing_model_input', 'price_download_scheme',
                                'price_download_scheme_input', 'maturity_date')

        # _l.debug('clone %s', TransactionTypeActionTransaction)
        # for source in TransactionTypeActionTransaction.objects.filter(
        #         transaction_type__master_user=self._source_master_user):
        #     self._simple_clone(None, source, 'transaction_type', 'order', 'action_notes',
        #                        'transaction_class', 'portfolio', 'portfolio_input', 'instrument', 'instrument_input',
        #                        'instrument_phantom', 'transaction_currency', 'transaction_currency_input',
        #                        'position_size_with_sign', 'settlement_currency', 'settlement_currency_input',
        #                        'cash_consideration', 'principal_with_sign', 'carry_with_sign', 'overheads_with_sign',
        #                        'account_position', 'account_position_input', 'account_cash', 'account_cash_input',
        #                        'account_interim', 'account_interim_input', 'accounting_date', 'cash_date',
        #                        'strategy1_position', 'strategy1_position_input', 'strategy1_cash',
        #                        'strategy1_cash_input', 'strategy2_position', 'strategy2_position_input',
        #                        'strategy2_cash', 'strategy2_cash_input', 'strategy3_position',
        #                        'strategy3_position_input', 'strategy3_cash', 'strategy3_cash_input',
        #                        'reference_fx_rate', 'factor', 'trade_price', 'principal_amount', 'carry_amount',
        #                        'overheads', 'responsible', 'responsible_input', 'counterparty', 'counterparty_input', )
        self._simple_list_clone(TransactionTypeActionTransaction, 'transaction_type__master_user',
                                'transaction_type', 'order', 'action_notes',
                                'transaction_class', 'portfolio', 'portfolio_input', 'instrument', 'instrument_input',
                                'instrument_phantom', 'transaction_currency', 'transaction_currency_input',
                                'position_size_with_sign', 'settlement_currency', 'settlement_currency_input',
                                'cash_consideration', 'principal_with_sign', 'carry_with_sign', 'overheads_with_sign',
                                'account_position', 'account_position_input', 'account_cash', 'account_cash_input',
                                'account_interim', 'account_interim_input', 'accounting_date', 'cash_date',
                                'strategy1_position', 'strategy1_position_input', 'strategy1_cash',
                                'strategy1_cash_input', 'strategy2_position', 'strategy2_position_input',
                                'strategy2_cash', 'strategy2_cash_input', 'strategy3_position',
                                'strategy3_position_input', 'strategy3_cash', 'strategy3_cash_input',
                                'reference_fx_rate', 'factor', 'trade_price', 'principal_amount', 'carry_amount',
                                'overheads', 'responsible', 'responsible_input', 'counterparty', 'counterparty_input', )

    def _tags(self):
        # _l.debug('clone %s', Tag)
        # for source in Tag.objects.filter(master_user=self._source_master_user):
        #     self._simple_clone(None, source, 'master_user', 'user_code', 'name', 'short_name', 'public_name', 'notes',
        #                        'content_types', 'account_types', 'accounts', 'currencies', 'instrument_types',
        #                        'instruments', 'counterparty_groups', 'counterparties', 'responsible_groups',
        #                        'responsibles', 'portfolios', 'transaction_type_groups', 'transaction_types',
        #                        'strategy1_groups', 'strategy1_subgroups', 'strategies1', 'strategy2_groups',
        #                        'strategy2_subgroups', 'strategies2', 'strategy3_groups', 'strategy3_subgroups',
        #                        'strategies3', 'thread_groups', )
        self._simple_list_clone(Tag, None, 'master_user', 'user_code', 'name', 'short_name', 'public_name', 'notes',
                                'content_types', 'account_types', 'accounts', 'currencies', 'instrument_types',
                                'instruments', 'counterparty_groups', 'counterparties', 'responsible_groups',
                                'responsibles', 'portfolios', 'transaction_type_groups', 'transaction_types',
                                'strategy1_groups', 'strategy1_subgroups', 'strategies1', 'strategy2_groups',
                                'strategy2_subgroups', 'strategies2', 'strategy3_groups', 'strategy3_subgroups',
                                'strategies3', 'thread_groups', )

    def _ui(self):
        # _l.debug('clone %s', TemplateListLayout)
        # for source in TemplateListLayout.objects.filter(master_user=self._source_master_user):
        #     self._simple_clone(None, source, 'content_type', 'json_data', 'name', 'is_default', pk_map=False)
        self._simple_list_clone(TemplateListLayout, None, 'content_type', 'json_data', 'name', 'is_default',
                                pk_map=False)

        # _l.debug('clone %s', TemplateEditLayout)
        # for source in TemplateEditLayout.objects.filter(master_user=self._source_master_user):
        #     self._simple_clone(None, source, 'content_type', 'json_data', pk_map=False)
        self._simple_list_clone(TemplateEditLayout, None, 'content_type', 'json_data', pk_map=False)

    def _attribute_types(self, type_model, classifier_model, value_model):
        _l.debug('clone %s', type_model)
        for source in type_model.objects.filter(master_user=self._source_master_user):
            self._simple_clone(None, source, 'master_user', 'user_code', 'name', 'short_name',
                               'public_name', 'notes', 'value_type', 'order')

        _l.debug('clone %s', classifier_model)
        for source in classifier_model.objects.filter(attribute_type__master_user=self._source_master_user):
            # TODO: classifier is tree!
            # self._simple_clone(None, source, 'attribute_type', 'name')
            pass

        _l.debug('clone %s', value_model)
        for source in value_model.objects.filter(attribute_type__master_user=self._source_master_user):
            # TODO: uncomment when classifier is ready
            # self._simple_clone(None, source, 'attribute_type', 'content_object', 'classifier')
            pass

    def _object_permissions(self, object_permission_model):
        _l.debug('clone %s', object_permission_model)
        for source in object_permission_model.filter(content_object__master_user=self._source_master_user):
            self._simple_clone(None, source, 'content_object', 'group', 'permission', 'value_string', 'value_float',
                               'value_date')

    def _simple_list_clone(self, model, master_user_path, *fields, pk_map=True, store=False):
        # _l.debug('clone %s', model)

        fields_select_related = []
        fields_prefetch_related = []
        for item in fields:
            field = model._meta.get_field(item)
            if field.one_to_one:
                pass
            elif field.one_to_many:
                # fields_select_related.append(field.name)
                pass
            elif field.many_to_many:
                fields_prefetch_related.append(field.name)

        if not master_user_path:
            master_user_path = 'master_user'

        qs = model.objects.filter(**{master_user_path: self._source_master_user})

        if fields_select_related:
            qs = qs.select_related(*fields_select_related)
        if fields_prefetch_related:
            qs = qs.prefetch_related(*fields_prefetch_related)

        _l.debug('clone %s: count=%s', model._meta.model_name, qs.count())
        for source in qs:
            self._simple_clone(None, source, *fields, pk_map=pk_map, store=store)

    def _simple_list_clone_2(self, model, master_user_path, *fields, pk_map=True, store=False):
        _l.debug('clone2 %s ', model._meta.model_name)
        for source in self._source_get_objects(model).values():
            target_pk = self._get_related_from_pk_map(source, source.pk)
            target = self._target_get_object(source, target_pk)
            self._simple_clone(target, source, *fields, pk_map=False)

    def _simple_clone(self, target, source, *fields, pk_map=True, store=False):
        content_type = ContentType.objects.get_for_model(source)
        if not target:
            target = content_type.model_class()()

        for item in fields:
            field = target._meta.get_field(item)

            if field.one_to_one:
                attr_name = field.get_attname()
                value = getattr(source, attr_name)
                value = self._get_related_from_pk_map(field.related_model, value)
                setattr(target, attr_name, value)
            elif field.one_to_many:
                pass
            elif field.many_to_one:
                attr_name = field.get_attname()
                value = getattr(source, attr_name)
                value = self._get_related_from_pk_map(field.related_model, value)
                setattr(target, attr_name, value)
            elif field.many_to_many:
                pass
            else:
                value = getattr(source, item)
                setattr(target, item, value)

        target.save()
        # if settings.DEBUG:
        #     _l.debug('cloned - %s: %s -> %s', content_type, source.pk, target.pk)

        for item in fields:
            field = target._meta.get_field(item)
            if field.many_to_many:
                values = getattr(source, item).values_list('id', flat=True)
                values = [self._get_related_from_pk_map(field.rel.to, pk) for pk in values]
                values = field.rel.to.objects.filter(pk__in=values)
                setattr(target, item, values)

        if pk_map:
            self._add_pk_map(target, source)

        if store:
            self._source_add_object(source)
            self._target_add_object(target)

        return target

    def _source_add_object(self, source):
        content_type = ContentType.objects.get_for_model(source)
        objects = self._source_objects[content_type.id]
        objects[source.id] = source

    def _source_get_objects(self, source):
        content_type = ContentType.objects.get_for_model(source)
        objects = self._source_objects[content_type.id]
        return objects

    def _source_get_object(self, source, pk):
        content_type = ContentType.objects.get_for_model(source)
        objects = self._source_objects[content_type.id]
        return objects[pk]

    def _target_add_object(self, target):
        content_type = ContentType.objects.get_for_model(target)
        objects = self._target_objects[content_type.id]
        objects[target.id] = target

    def _target_get_objects(self, target):
        content_type = ContentType.objects.get_for_model(target)
        objects = self._target_objects[content_type.id]
        return objects

    def _target_get_object(self, target, pk):
        content_type = ContentType.objects.get_for_model(target)
        objects = self._target_objects[content_type.id]
        return objects[pk]

    def _add_pk_map(self, target, source):
        content_type = ContentType.objects.get_for_model(target)
        cobjects = self._pk_map[content_type.pk]
        cobjects[source.pk] = target.pk

    def _get_related_from_pk_map(self, model, pk):
        if pk is None:
            return None
        content_type = ContentType.objects.get_for_model(model)
        objects = self._pk_map[content_type.pk]
        return objects[pk]
