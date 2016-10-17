import logging

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from poms.accounts.models import AccountType, Account
from poms.chats.models import ThreadGroup
from poms.counterparties.models import CounterpartyGroup, Counterparty, ResponsibleGroup, Responsible
from poms.currencies.models import Currency, CurrencyHistory
from poms.instruments.models import PricingPolicy, DailyPricingModel, InstrumentClass, AccrualCalculationModel, \
    PaymentSizeDetail, Periodicity, CostMethod, InstrumentType, Instrument, ManualPricingFormula, PriceHistory, \
    AccrualCalculationSchedule, InstrumentFactorSchedule, EventScheduleConfig
from poms.integrations.models import PriceDownloadScheme, ProviderClass
from poms.transactions.models import TransactionClass, ActionClass, EventClass, NotificationClass
from poms.users.models import Group, Member

_l = logging.getLogger('poms.users.cloner')


class FullDataCloner(object):
    def __init__(self, source_master_user):
        self.source_master_user = source_master_user

        self.pk_map = {}

    @transaction.atomic()
    def clone(self):
        _l.debug('clone: master_user=%s', self.source_master_user.pk)
        self.target_master_user = self._simple_clone(None, self.source_master_user, 'name', 'language', 'timezone')

        self._load_consts()

        self._users()
        self._accounts()
        self._chats()
        self._counterparties()

        self._instruments_1()
        self._integrations_1()

        self._currencies()

        self._instruments_2()

        transaction.set_rollback(True)

    def _load_consts(self):
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

        for source in TransactionClass.objects.all():
            self._add_pk_map(source, source)

        for source in ActionClass.objects.all():
            self._add_pk_map(source, source)

        for source in EventClass.objects.all():
            self._add_pk_map(source, source)

        for source in NotificationClass.objects.all():
            self._add_pk_map(source, source)

    def _users(self):
        for source in Group.objects.filter(master_user=self.source_master_user):
            self._simple_clone(None, source, 'master_user', 'name')

        for source in Member.objects.select_related('user').filter(master_user=self.source_master_user):
            self._add_pk_map(source.user, source.user)
            self._simple_clone(None, source, 'master_user', 'user', 'username', 'first_name', 'last_name', 'email',
                               'join_date', 'is_owner', 'is_admin', 'is_deleted', 'groups')

    def _accounts(self):
        for source in AccountType.objects.filter(master_user=self.source_master_user):
            self._simple_clone(None, source, 'master_user', 'user_code', 'name', 'short_name',
                               'public_name', 'notes', 'is_deleted', 'show_transaction_details',
                               'transaction_details_expr')

        for source in Account.objects.filter(master_user=self.source_master_user):
            self._simple_clone(None, source, 'master_user', 'user_code', 'name', 'short_name',
                               'public_name', 'notes', 'is_deleted', 'type', 'is_valid_for_all_portfolios')

    def _chats(self):
        for source in ThreadGroup.objects.filter(master_user=self.source_master_user):
            self._simple_clone(None, source, 'master_user', 'name', 'is_deleted')

    def _counterparties(self):
        for source in CounterpartyGroup.objects.filter(master_user=self.source_master_user):
            self._simple_clone(None, source, 'master_user', 'user_code', 'name', 'short_name',
                               'public_name', 'notes', 'is_deleted')

        for source in Counterparty.objects.filter(master_user=self.source_master_user):
            self._simple_clone(None, source, 'master_user', 'user_code', 'name', 'short_name',
                               'public_name', 'notes', 'is_deleted', 'group', 'is_valid_for_all_portfolios')

        for source in ResponsibleGroup.objects.filter(master_user=self.source_master_user):
            self._simple_clone(None, source, 'master_user', 'user_code', 'name', 'short_name',
                               'public_name', 'notes', 'is_deleted')

        for source in Responsible.objects.filter(master_user=self.source_master_user):
            self._simple_clone(None, source, 'master_user', 'user_code', 'name', 'short_name',
                               'public_name', 'notes', 'is_deleted', 'group', 'is_valid_for_all_portfolios')

    def _currencies(self):
        for source in Currency.objects.filter(master_user=self.source_master_user):
            self._simple_clone(None, source, 'master_user', 'user_code', 'name', 'short_name',
                               'public_name', 'notes', 'is_deleted', 'reference_for_pricing', 'daily_pricing_model',
                               'price_download_scheme')

        for source in CurrencyHistory.objects.filter(currency__master_user=self.source_master_user):
            self._simple_clone(None, source, 'currency', 'pricing_policy', 'date', 'fx_rate',
                               pk_map=False)

    def _instruments_1(self):
        for source in PricingPolicy.objects.filter(master_user=self.source_master_user):
            self._simple_clone(None, source, 'master_user', 'user_code', 'name', 'short_name',
                               'public_name', 'notes', 'expr')

    def _instruments_2(self):
        for source in InstrumentType.objects.filter(master_user=self.source_master_user):
            self._simple_clone(None, source, 'master_user', 'user_code', 'name', 'short_name',
                               'public_name', 'notes', 'is_deleted', 'instrument_class')

        for source in Instrument.objects.filter(master_user=self.source_master_user):
            self._simple_clone(None, source, 'master_user', 'user_code', 'name', 'short_name',
                               'public_name', 'notes', 'is_deleted', 'instrument_type', 'is_active',
                               'pricing_currency', 'price_multiplier',
                               'accrued_currency', 'accrued_multiplier',
                               'payment_size_detail',
                               'default_price', 'default_accrued',
                               'user_text_1', 'user_text_2', 'user_text_3',
                               'reference_for_pricing', 'daily_pricing_model', 'price_download_scheme',
                               'maturity_date')

        for source in ManualPricingFormula.objects.filter(instrument__master_user=self.source_master_user):
            self._simple_clone(None, source, 'instrument', 'pricing_policy', 'expr', 'notes')

        for source in AccrualCalculationSchedule.objects.filter(instrument__master_user=self.source_master_user):
            self._simple_clone(None, source, 'instrument', 'accrual_start_date', 'first_payment_date', 'accrual_size',
                               'accrual_calculation_model', 'periodicity', 'periodicity_n', 'notes')

        for source in InstrumentFactorSchedule.objects.filter(instrument__master_user=self.source_master_user):
            self._simple_clone(None, source, 'instrument', 'effective_date', 'factor_value')

        for source in PriceHistory.objects.filter(instrument__master_user=self.source_master_user):
            self._simple_clone(None, source, 'instrument', 'pricing_policy', 'date', 'principal_price', 'accrued_price',
                               pk_map=False)

        for source in EventScheduleConfig.objects.filter(master_user=self.source_master_user):
            self._simple_clone(None, source, 'master_user', 'name', 'description', 'notification_class',
                               'notify_in_n_days', 'action_text', 'action_is_sent_to_pending',
                               'action_is_book_automatic')

    def _instruments_3(self):
        # TODO: InstrumentType - 'one_off_event', 'regular_event', 'factor_same', 'factor_up', 'factor_down',

        # TODO: EventSchedule

        # TODO: EventScheduleAction

        pass

    def _integrations_1(self):
        for source in PriceDownloadScheme.objects.filter(master_user=self.source_master_user):
            self._simple_clone(None, source, 'master_user', 'scheme_name', 'provider',
                               'bid0', 'bid1', 'bid2', 'bid_multiplier',
                               'ask0', 'ask1', 'ask2', 'ask_multiplier', 'last',
                               'last', 'mid', 'mid_multiplier',
                               'bid_history', 'bid_history_multiplier',
                               'ask_history', 'ask_history_multiplier',
                               'mid_history', 'mid_history_multiplier',
                               'last_history', 'last_history_multiplier',
                               'currency_fxrate', 'currency_fxrate_multiplier')

    def _add_pk_map(self, target, source):
        content_type = ContentType.objects.get_for_model(target)
        key = (content_type.pk, source.pk)
        self.pk_map[key] = target.pk

    def _get_related_from_pk_map(self, model, pk):
        if pk is None:
            return None
        content_type = ContentType.objects.get_for_model(model)
        key = (content_type.pk, pk)
        return self.pk_map[key]

    def _simple_clone(self, target, source, *fields, pk_map=True):
        content_type = ContentType.objects.get_for_model(source)
        if target is None:
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
        if settings.DEBUG:
            _l.debug('cloned - %s: %s -> %s', content_type, source.pk, target.pk)

        for item in fields:
            field = target._meta.get_field(item)
            if field.many_to_many:
                values = getattr(source, item).values_list('id', flat=True)
                values = [self._get_related_from_pk_map(field.rel.to, pk) for pk in values]
                values = field.rel.to.objects.filter(pk__in=values)
                setattr(target, item, values)

        if pk_map:
            self._add_pk_map(target, source)

    def _attribute_type_clone(self, target_model):
        pass

    def _object_permission_clone(self, target_model):
        pass
