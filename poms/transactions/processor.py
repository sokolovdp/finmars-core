from datetime import date

from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy

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
                errors = {}
                try:
                    user_code = formula.safe_eval(action_instrument.user_code, names=values)
                except formula.InvalidExpression as e:
                    self._set_eval_error(errors, 'user_code', action_instrument.user_code, e)
                    user_code = None

                if user_code:
                    try:
                        instrument = Instrument.objects.get(master_user=master_user, user_code=user_code)
                        self._instruments.append(instrument)
                        self._instruments_errors.append({})
                        continue
                    except ObjectDoesNotExist:
                        pass

                instrument = Instrument(master_user=master_user)
                # results[action_instr.order] = instr
                instrument.user_code = user_code
                self._set_val(errors=errors,
                              target=instrument,
                              target_attr_name='name',
                              source=action_instrument,
                              source_attr_name='name',
                              values=values,
                              default_value='')
                self._set_val(errors=errors,
                              target=instrument,
                              target_attr_name='short_name',
                              source=action_instrument,
                              source_attr_name='short_name',
                              values=values,
                              default_value='')
                self._set_val(errors=errors, target=instrument,
                              target_attr_name='public_name',
                              source=action_instrument,
                              source_attr_name='public_name',
                              values=values,
                              default_value='')
                self._set_val(errors=errors, target=instrument,
                              target_attr_name='notes',
                              source=action_instrument,
                              source_attr_name='notes',
                              values=values,
                              default_value='')
                self._set_rel(errors=errors,
                              target=instrument,
                              target_attr_name='instrument_type',
                              source=action_instrument,
                              source_attr_name='instrument_type',
                              values=values,
                              default_value=master_user.instrument_type)
                self._set_rel(errors=errors, target=instrument,
                              target_attr_name='pricing_currency',
                              source=action_instrument,
                              source_attr_name='pricing_currency',
                              values=values,
                              default_value=master_user.currency)
                self._set_val(errors=errors,
                              target=instrument,
                              target_attr_name='price_multiplier',
                              source=action_instrument,
                              source_attr_name='price_multiplier',
                              values=values,
                              default_value=0.0)
                self._set_rel(errors=errors,
                              target=instrument,
                              target_attr_name='accrued_currency',
                              source=action_instrument,
                              source_attr_name='accrued_currency',
                              values=values,
                              default_value=master_user.currency)
                self._set_val(errors=errors,
                              target=instrument,
                              target_attr_name='accrued_multiplier',
                              source=action_instrument,
                              source_attr_name='accrued_multiplier',
                              values=values,
                              default_value=0.0)
                self._set_rel(errors=errors,
                              target=instrument,
                              target_attr_name='payment_size_detail',
                              source=action_instrument,
                              source_attr_name='payment_size_detail',
                              values=values,
                              default_value=None)
                self._set_val(errors=errors,
                              target=instrument,
                              target_attr_name='default_price',
                              source=action_instrument,
                              source_attr_name='default_price',
                              values=values,
                              default_value=0.0)
                self._set_val(errors=errors,
                              target=instrument,
                              target_attr_name='default_accrued',
                              source=action_instrument,
                              source_attr_name='default_accrued',
                              values=values,
                              default_value=0.0)
                self._set_val(errors=errors,
                              target=instrument,
                              target_attr_name='user_text_1',
                              source=action_instrument,
                              source_attr_name='user_text_1',
                              values=values,
                              default_value='')
                self._set_val(errors=errors,
                              target=instrument,
                              target_attr_name='user_text_2',
                              source=action_instrument,
                              source_attr_name='user_text_2',
                              values=values,
                              default_value='')
                self._set_val(errors=errors,
                              target=instrument,
                              target_attr_name='user_text_3',
                              source=action_instrument,
                              source_attr_name='user_text_3',
                              values=values,
                              default_value='')
                self._set_val(errors=errors,
                              target=instrument,
                              target_attr_name='reference_for_pricing',
                              source=action_instrument,
                              source_attr_name='reference_for_pricing',
                              values=values,
                              default_value='')
                self._set_rel(errors=errors,
                              target=instrument,
                              target_attr_name='price_download_scheme',
                              source=action_instrument,
                              source_attr_name='price_download_scheme',
                              values=values,
                              default_value=None)
                self._set_rel(errors=errors,
                              target=instrument,
                              target_attr_name='daily_pricing_model',
                              source=action_instrument,
                              source_attr_name='daily_pricing_model',
                              values=values,
                              default_value=daily_pricing_model)
                self._set_val(errors=errors,
                              target=instrument,
                              target_attr_name='maturity_date',
                              source=action_instrument,
                              source_attr_name='maturity_date',
                              values=values,
                              default_value=date.max)

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

                self._set_rel(errors=errors, target=transaction,
                              target_attr_name='portfolio',
                              source=action_transaction,
                              source_attr_name='portfolio',
                              values=values,
                              default_value=master_user.portfolio)
                self._set_rel(errors=errors,
                              target=transaction,
                              target_attr_name='instrument',
                              source=action_transaction,
                              source_attr_name='instrument',
                              values=values,
                              default_value=None)
                if action_transaction.instrument_phantom is not None:
                    transaction.instrument = instrument_map[action_transaction.instrument_phantom_id]
                self._set_rel(errors=errors,
                              target=transaction,
                              target_attr_name='transaction_currency',
                              source=action_transaction,
                              source_attr_name='transaction_currency',
                              values=values,
                              default_value=master_user.currency)
                self._set_val(errors=errors,
                              target=transaction,
                              target_attr_name='position_size_with_sign',
                              source=action_transaction,
                              source_attr_name='position_size_with_sign',
                              values=values,
                              default_value=0.0)
                self._set_rel(errors=errors,
                              target=transaction,
                              target_attr_name='settlement_currency',
                              source=action_transaction,
                              source_attr_name='settlement_currency',
                              values=values,
                              default_value=master_user.currency)
                self._set_val(errors=errors,
                              target=transaction,
                              target_attr_name='cash_consideration',
                              source=action_transaction,
                              source_attr_name='cash_consideration',
                              values=values,
                              default_value=0.0)
                self._set_val(errors=errors,
                              target=transaction,
                              target_attr_name='principal_with_sign',
                              source=action_transaction,
                              source_attr_name='principal_with_sign',
                              values=values,
                              default_value=0.0)
                self._set_val(errors=errors,
                              target=transaction,
                              target_attr_name='carry_with_sign',
                              source=action_transaction,
                              source_attr_name='carry_with_sign',
                              values=values,
                              default_value=0.0)
                self._set_val(errors=errors,
                              target=transaction,
                              target_attr_name='overheads_with_sign',
                              source=action_transaction,
                              source_attr_name='overheads_with_sign',
                              values=values,
                              default_value=0.0)
                self._set_rel(errors=errors,
                              target=transaction,
                              target_attr_name='account_position',
                              source=action_transaction,
                              source_attr_name='account_position',
                              values=values,
                              default_value=master_user.account)
                self._set_rel(errors=errors,
                              target=transaction,
                              target_attr_name='account_cash',
                              source=action_transaction,
                              source_attr_name='account_cash',
                              values=values,
                              default_value=master_user.account)
                self._set_rel(errors=errors,
                              target=transaction,
                              target_attr_name='account_interim',
                              source=action_transaction,
                              source_attr_name='account_interim',
                              values=values,
                              default_value=master_user.account)
                self._set_val(errors=errors,
                              target=transaction,
                              target_attr_name='accounting_date',
                              source=action_transaction,
                              source_attr_name='accounting_date',
                              values=values,
                              default_value=None)
                self._set_val(errors=errors,
                              target=transaction,
                              target_attr_name='cash_date',
                              source=action_transaction,
                              source_attr_name='cash_date',
                              values=values,
                              default_value=None)
                self._set_rel(errors=errors,
                              target=transaction,
                              target_attr_name='strategy1_position',
                              source=action_transaction,
                              source_attr_name='strategy1_position',
                              values=values,
                              default_value=master_user.strategy1)
                self._set_rel(errors=errors,
                              target=transaction,
                              target_attr_name='strategy1_cash',
                              source=action_transaction,
                              source_attr_name='strategy1_cash',
                              values=values,
                              default_value=master_user.strategy1)
                self._set_rel(errors=errors,
                              target=transaction,
                              target_attr_name='strategy2_position',
                              source=action_transaction,
                              source_attr_name='strategy2_position',
                              values=values,
                              default_value=master_user.strategy2)
                self._set_rel(errors=errors,
                              target=transaction,
                              target_attr_name='strategy2_cash',
                              source=action_transaction,
                              source_attr_name='strategy2_cash',
                              values=values,
                              default_value=master_user.strategy2)
                self._set_rel(errors=errors,
                              target=transaction,
                              target_attr_name='strategy3_position',
                              source=action_transaction,
                              source_attr_name='strategy3_position',
                              values=values,
                              default_value=master_user.strategy3)
                self._set_rel(errors=errors,
                              target=transaction,
                              target_attr_name='strategy3_cash',
                              source=action_transaction,
                              source_attr_name='strategy3_cash',
                              values=values,
                              default_value=master_user.strategy3)
                self._set_val(errors=errors,
                              target=transaction,
                              target_attr_name='factor',
                              source=action_transaction,
                              source_attr_name='factor',
                              values=values,
                              default_value=0.0)
                self._set_val(errors=errors,
                              target=transaction,
                              target_attr_name='trade_price',
                              source=action_transaction,
                              source_attr_name='trade_price',
                              values=values,
                              default_value=0.0)
                self._set_val(errors=errors, target=transaction,
                              target_attr_name='principal_amount',
                              source=action_transaction,
                              source_attr_name='principal_amount',
                              values=values,
                              default_value=0.0)
                self._set_val(errors=errors,
                              target=transaction,
                              target_attr_name='carry_amount',
                              source=action_transaction,
                              source_attr_name='carry_amount',
                              values=values,
                              default_value=0.0)
                self._set_rel(errors=errors,
                              target=transaction,
                              target_attr_name='responsible',
                              source=action_transaction,
                              source_attr_name='responsible',
                              values=values,
                              default_value=master_user.responsible)
                self._set_rel(errors=errors,
                              target=transaction,
                              target_attr_name='counterparty',
                              source=action_transaction,
                              source_attr_name='counterparty',
                              values=values,
                              default_value=master_user.counterparty)

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

    def _set_val(self, errors, target, target_attr_name, source, source_attr_name, values, default_value):
        value = getattr(source, source_attr_name)
        if value:
            try:
                value = formula.safe_eval(value, names=values)
            except formula.InvalidExpression as e:
                self._set_eval_error(errors, source_attr_name, value, e)
                return
        else:
            value = default_value
        setattr(target, target_attr_name, value)

    def _set_rel(self, errors, target, target_attr_name, source, source_attr_name, values, default_value):
        value = getattr(source, source_attr_name, None)
        if value:
            pass
        else:
            from_input = getattr(source, '%s_input' % source_attr_name)
            if from_input:
                value = values[from_input.name]
        if not value:
            value = default_value
        if value is not None:
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

    def _set_eval_error(self, errors, attr_name, expression, exc=None):
        msg = ugettext_lazy('Invalid expression "%(expression)s".') % {
            'expression': expression,
        }
        msgs = errors.get(attr_name, None) or []
        if msg not in msgs:
            errors[attr_name] = msgs + [msg]
