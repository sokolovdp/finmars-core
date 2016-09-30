from django.core.exceptions import ObjectDoesNotExist

from poms.common import formula
from poms.instruments.models import Instrument, DailyPricingModel
from poms.obj_perms.utils import assign_perms
from poms.transactions.models import Transaction, ComplexTransaction


class TransactionTypeProcessor(object):
    def __init__(self, transaction_type, input_values):
        assert transaction_type is not None, "transaction_type can't be None"
        self._transaction_type = transaction_type
        self._input_values = input_values or {}
        self._instruments = []
        self._instruments_errors = []
        self._complex_transaction = None
        self._transactions = []
        self._transactions_errors = []
        self._save = False
        self._id_seq = 0
        self._transaction_order_seq = 0

    @property
    def has_errors(self):
        for errors in self._instruments_errors:
            if errors:
                return True
        for errors in self._transactions_errors:
            if errors:
                return True
        return False

    @property
    def instruments(self):
        return self._instruments

    @property
    def instruments_errors(self):
        return self._instruments_errors

    @property
    def complex_transaction(self):
        if self._complex_transaction is None:
            self._complex_transaction = ComplexTransaction(transaction_type=self._transaction_type)
            if self._save:
                self._complex_transaction.save()
            else:
                self._complex_transaction.id = self._next_id()
        return self._complex_transaction

    @property
    def complex_transaction(self):
        if self._complex_transaction is None:
            self._complex_transaction = ComplexTransaction(transaction_type=self._transaction_type)
            if self._save:
                self._complex_transaction.save()
            else:
                self._complex_transaction.id = self._next_id()
        return self._complex_transaction

    @property
    def transactions(self):
        return self._transactions

    @property
    def transactions_errors(self):
        return self._transactions_errors

    def run(self, save=False):
        self._save = save
        return self._process()

    def _process(self):
        values = self._input_values

        master_user = self._transaction_type.master_user
        user_object_permissions = self._transaction_type.user_object_permissions.select_related('permission').all()
        group_object_permissions = self._transaction_type.group_object_permissions.select_related('permission').all()
        daily_pricing_model = DailyPricingModel.objects.get(pk=DailyPricingModel.SKIP)

        instrument_map = {}
        actions = self._transaction_type.actions.order_by('order').all()
        for order, action in enumerate(actions, start=1):
            try:
                action_instrument = action.transactiontypeactioninstrument
            except ObjectDoesNotExist:
                action_instrument = None
            try:
                action_transaction = action.transactiontypeactiontransaction
            except ObjectDoesNotExist:
                action_transaction = None

            if action_instrument:
                user_code = formula.safe_eval(action_instrument.user_code, names=values)
                if user_code:
                    try:
                        instrument = Instrument.objects.get(master_user=master_user, user_code=user_code)
                        self._instruments.append(instrument)
                        self._instruments_errors.append({})
                        continue
                    except ObjectDoesNotExist:
                        pass

                errors = {}
                instrument = Instrument(master_user=master_user)
                # results[action_instr.order] = instr
                instrument.user_code = user_code
                self._set_simple(instrument, 'name', action_instrument, 'name', values, '')
                self._set_simple(instrument, 'short_name', action_instrument, 'short_name', values, '')
                self._set_simple(instrument, 'public_name', action_instrument, 'public_name', values, '')
                self._set_simple(instrument, 'notes', action_instrument, 'notes', values, '')
                self._set_relation(instrument, 'instrument_type', action_instrument, 'instrument_type', values, master_user.instrument_type)
                self._set_relation(instrument, 'pricing_currency', action_instrument, 'pricing_currency', values, master_user.currency)
                self._set_simple(instrument, 'price_multiplier', action_instrument, 'price_multiplier', values, 0.0)
                self._set_relation(instrument, 'accrued_currency', action_instrument, 'accrued_currency', values, master_user.currency)
                self._set_simple(instrument, 'accrued_multiplier', action_instrument, 'accrued_multiplier', values, 0.0)
                self._set_relation(instrument, 'payment_size_detail', action_instrument, 'payment_size_detail', values)
                self._set_simple(instrument, 'default_price', action_instrument, 'default_price', values)
                self._set_simple(instrument, 'default_accrued', action_instrument, 'default_accrued', values)
                self._set_simple(instrument, 'user_text_1', action_instrument, 'user_text_1', values, '')
                self._set_simple(instrument, 'user_text_2', action_instrument, 'user_text_2', values, '')
                self._set_simple(instrument, 'user_text_3', action_instrument, 'user_text_3', values, '')
                self._set_simple(instrument, 'reference_for_pricing', action_instrument, 'reference_for_pricing', values, '')
                self._set_relation(instrument, 'price_download_scheme', action_instrument, 'price_download_scheme', values)
                self._set_relation(instrument, 'daily_pricing_model', action_instrument, 'daily_pricing_model', values, daily_pricing_model)
                self._set_simple(instrument, 'maturity_date', action_instrument, 'maturity_date', values)

                if self._save:
                    instrument.save()
                    self._instrument_assign_permission(instrument, user_object_permissions, group_object_permissions)
                else:
                    instrument.id = self._next_id()
                instrument_map[action.id] = instrument
                self._instruments.append(instrument)
                self._instruments_errors.append(errors)

            elif action_transaction:
                errors = {}
                transaction = Transaction(master_user=master_user)
                transaction.complex_transaction = self.complex_transaction
                transaction.complex_transaction_order = self._next_transaction_order()
                transaction.transaction_class = action_transaction.transaction_class

                self._set_relation(transaction, 'portfolio', action_transaction, 'portfolio', values, master_user.portfolio)
                self._set_relation(transaction, 'instrument', action_transaction, 'instrument', values)
                if action_transaction.instrument_phantom is not None:
                    transaction.instrument = instrument_map[action_transaction.instrument_phantom_id]
                self._set_relation(transaction, 'transaction_currency', action_transaction, 'transaction_currency', values, master_user.currency)
                self._set_simple(transaction, 'position_size_with_sign', action_transaction, 'position_size_with_sign', values)
                self._set_relation(transaction, 'settlement_currency', action_transaction, 'settlement_currency', values, master_user.currency)
                self._set_simple(transaction, 'cash_consideration', action_transaction, 'cash_consideration', values, 0.0)
                self._set_simple(transaction, 'principal_with_sign', action_transaction, 'principal_with_sign', values, 0.0)
                self._set_simple(transaction, 'carry_with_sign', action_transaction, 'carry_with_sign', values, 0.0)
                self._set_simple(transaction, 'overheads_with_sign', action_transaction, 'overheads_with_sign', values, 0.0)
                self._set_relation(transaction, 'account_position', action_transaction, 'account_position', values, master_user.account)
                self._set_relation(transaction, 'account_cash', action_transaction, 'account_cash', values, master_user.account)
                self._set_relation(transaction, 'account_interim', action_transaction, 'account_interim', values, master_user.account)
                self._set_simple(transaction, 'accounting_date', action_transaction, 'accounting_date', values)
                self._set_simple(transaction, 'cash_date', action_transaction, 'cash_date', values)
                self._set_relation(transaction, 'strategy1_position', action_transaction, 'strategy1_position', values, master_user.strategy1)
                self._set_relation(transaction, 'strategy1_cash', action_transaction, 'strategy1_cash', values, master_user.strategy1)
                self._set_relation(transaction, 'strategy2_position', action_transaction, 'strategy2_position', values, master_user.strategy2)
                self._set_relation(transaction, 'strategy2_cash', action_transaction, 'strategy2_cash', values, master_user.strategy2)
                self._set_relation(transaction, 'strategy3_position', action_transaction, 'strategy3_position', values, master_user.strategy3)
                self._set_relation(transaction, 'strategy3_cash', action_transaction, 'strategy3_cash', values, master_user.strategy3)
                self._set_simple(transaction, 'factor', action_transaction, 'factor', values, 0.0)
                self._set_simple(transaction, 'trade_price', action_transaction, 'trade_price', values, 0.0)
                self._set_simple(transaction, 'principal_amount', action_transaction, 'principal_amount', values, 0.0)
                self._set_simple(transaction, 'carry_amount', action_transaction, 'carry_amount', values, 0.0)
                self._set_relation(transaction, 'responsible', action_transaction, 'responsible', values, master_user.responsible)
                self._set_relation(transaction, 'counterparty', action_transaction, 'counterparty', values, master_user.counterparty)

                transaction.transaction_date = min(transaction.accounting_date, transaction.cash_date)
                if self._save:
                    transaction.save()
                else:
                    transaction.id = self._next_id()

                self._transactions.append(transaction)
                self._transactions_errors.append(errors)
        return self._instruments, self._transactions

    def _next_id(self):
        self._id_seq -= 1
        return self._id_seq

    def _next_transaction_order(self):
        self._transaction_order_seq += 1
        return self._transaction_order_seq

    def _set_simple(self, target, target_attr_name, source, source_attr_name, values, default_value=None):
        value = getattr(source, source_attr_name)
        if value:
            try:
                value = formula.safe_eval(value, names=values)
            except formula.InvalidExpression:
                return
                pass
        else:
            value = default_value
        setattr(target, target_attr_name, value)

    def _set_relation(self, target, target_attr_name, source, source_attr_name, values, default_value=None):
        value = getattr(source, source_attr_name, None)
        if value:
            pass
        else:
            from_input = getattr(source, '%s_input' % source_attr_name)
            if from_input:
                value = values[from_input.name]
        if not value:
            value = default_value
        setattr(target, target_attr_name, value)

    def _instrument_assign_permission(self, instr, user_object_permissions, group_object_permissions):
        perms_map = {
            'add_transactiontype': 'add_instrument',
            'view_transactiontype': 'view_instrument',
            'change_transactiontype': 'change_instrument',
            'delete_transactiontype': 'delete_instrument',
        }
        for uop in user_object_permissions:
            if uop.permission.codename in perms_map:
                perm = perms_map[uop.permission.codename]
                assign_perms(instr, members=[uop.member], groups=None, perms=[perm])
        for gop in group_object_permissions:
            if gop.permission.codename in perms_map:
                perm = perms_map[gop.permission.codename]
                assign_perms(instr, members=None, groups=[gop.group], perms=[perm])
