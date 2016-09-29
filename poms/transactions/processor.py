from django.core.exceptions import ObjectDoesNotExist

from poms.common import formula
from poms.instruments.models import Instrument, DailyPricingModel
from poms.obj_perms.utils import assign_perms
from poms.transactions.models import Transaction, ComplexTransaction


class TransactionTypeProcessor(object):
    def __init__(self, transaction_type, input_values):
        self.transaction_type = transaction_type
        self.input_values = input_values
        self._save = False
        self._seq = 0

    def run(self, save=False):
        self._save = save
        return self._process()

    def _process(self):
        input_values = self.input_values

        master_user = self.transaction_type.master_user
        actions = self.transaction_type.actions.order_by('order').all()
        user_object_permissions = self.transaction_type.user_object_permissions.select_related('permission').all()
        group_object_permissions = self.transaction_type.group_object_permissions.select_related('permission').all()

        instruments = []
        transactions = []
        daily_pricing_model = DailyPricingModel.objects.get(pk=DailyPricingModel.SKIP)

        cmplx_trn = ComplexTransaction(transaction_type=self.transaction_type)
        if self._save:
            cmplx_trn.save()
        else:
            cmplx_trn.id = self._next_id()

        trn_order = 0
        instr_map = {}
        for order, action in enumerate(actions, start=1):
            try:
                action_instr = action.transactiontypeactioninstrument
            except ObjectDoesNotExist:
                action_instr = None
            try:
                action_trn = action.transactiontypeactiontransaction
            except ObjectDoesNotExist:
                action_trn = None

            if action_instr:
                user_code = formula.safe_eval(action_instr.user_code, names=input_values)
                if user_code:
                    try:
                        instr = Instrument.objects.get(master_user=master_user, user_code=user_code)
                        instruments.append(instr)
                        # results[action_instr.order] = instr
                        continue
                    except ObjectDoesNotExist:
                        pass

                instr = Instrument(master_user=master_user)
                instruments.append(instr)
                # results[action_instr.order] = instr
                instr.user_code = user_code
                self._set_simple(instr, 'name', action_instr, 'name', input_values)
                self._set_simple(instr, 'short_name', action_instr, 'short_name', input_values, '')
                self._set_simple(instr, 'public_name', action_instr, 'public_name', input_values, '')
                self._set_simple(instr, 'notes', action_instr, 'notes', input_values, '')
                self._set_relation(instr, 'instrument_type', action_instr, 'instrument_type', input_values, master_user.instrument_type)
                self._set_relation(instr, 'pricing_currency', action_instr, 'pricing_currency', input_values, master_user.currency)
                self._set_simple(instr, 'price_multiplier', action_instr, 'price_multiplier', input_values, 0.0)
                self._set_relation(instr, 'accrued_currency', action_instr, 'accrued_currency', input_values, master_user.currency)
                self._set_simple(instr, 'accrued_multiplier', action_instr, 'accrued_multiplier', input_values, 0.0)
                self._set_relation(instr, 'payment_size_detail', action_instr, 'payment_size_detail', input_values)
                self._set_simple(instr, 'default_price', action_instr, 'default_price', input_values)
                self._set_simple(instr, 'default_accrued', action_instr, 'default_accrued', input_values)
                self._set_simple(instr, 'user_text_1', action_instr, 'user_text_1', input_values, '')
                self._set_simple(instr, 'user_text_2', action_instr, 'user_text_2', input_values, '')
                self._set_simple(instr, 'user_text_3', action_instr, 'user_text_3', input_values, '')
                self._set_simple(instr, 'reference_for_pricing', action_instr, 'reference_for_pricing', input_values, '')
                self._set_relation(instr, 'price_download_scheme', action_instr, 'price_download_scheme', input_values)
                self._set_relation(instr, 'daily_pricing_model', action_instr, 'daily_pricing_model', input_values, daily_pricing_model)
                self._set_simple(instr, 'maturity_date', action_instr, 'maturity_date', input_values)

                if self._save:
                    instr.save()
                    self._instrument_assign_permission(instr, user_object_permissions, group_object_permissions)
                else:
                    instr.id = self._next_id()
                instr_map[action.id] = instr
            elif action_trn:
                trn = Transaction(master_user=master_user)
                transactions.append(trn)
                trn.complex_transaction = cmplx_trn
                trn.complex_transaction_order = trn_order
                trn.transaction_class = action_trn.transaction_class

                self._set_relation(trn, 'portfolio', action_trn, 'portfolio', input_values, master_user.portfolio)
                self._set_relation(trn, 'instrument', action_trn, 'instrument', input_values)
                if action_trn.instrument_phantom is not None:
                    trn.instrument = instr_map[action_trn.instrument_phantom_id]
                self._set_relation(trn, 'transaction_currency', action_trn, 'transaction_currency', input_values, master_user.currency)
                self._set_simple(trn, 'position_size_with_sign', action_trn, 'position_size_with_sign', input_values)
                self._set_relation(trn, 'settlement_currency', action_trn, 'settlement_currency', input_values, master_user.currency)
                self._set_simple(trn, 'cash_consideration', action_trn, 'cash_consideration', input_values, 0.0)
                self._set_simple(trn, 'principal_with_sign', action_trn, 'principal_with_sign', input_values, 0.0)
                self._set_simple(trn, 'carry_with_sign', action_trn, 'carry_with_sign', input_values, 0.0)
                self._set_simple(trn, 'overheads_with_sign', action_trn, 'overheads_with_sign', input_values, 0.0)
                self._set_relation(trn, 'account_position', action_trn, 'account_position', input_values, master_user.account)
                self._set_relation(trn, 'account_cash', action_trn, 'account_cash', input_values, master_user.account)
                self._set_relation(trn, 'account_interim', action_trn, 'account_interim', input_values, master_user.account)
                self._set_simple(trn, 'accounting_date', action_trn, 'accounting_date', input_values)
                self._set_simple(trn, 'cash_date', action_trn, 'cash_date', input_values)
                trn.transaction_date = min(trn.accounting_date, trn.cash_date)
                self._set_relation(trn, 'strategy1_position', action_trn, 'strategy1_position', input_values, master_user.strategy1)
                self._set_relation(trn, 'strategy1_cash', action_trn, 'strategy1_cash', input_values, master_user.strategy1)
                self._set_relation(trn, 'strategy2_position', action_trn, 'strategy2_position', input_values, master_user.strategy2)
                self._set_relation(trn, 'strategy2_cash', action_trn, 'strategy2_cash', input_values, master_user.strategy2)
                self._set_relation(trn, 'strategy3_position', action_trn, 'strategy3_position', input_values, master_user.strategy3)
                self._set_relation(trn, 'strategy3_cash', action_trn, 'strategy3_cash', input_values, master_user.strategy3)
                self._set_simple(trn, 'factor', action_trn, 'factor', input_values, 0.0)
                self._set_simple(trn, 'trade_price', action_trn, 'trade_price', input_values, 0.0)
                self._set_simple(trn, 'principal_amount', action_trn, 'principal_amount', input_values, 0.0)
                self._set_simple(trn, 'carry_amount', action_trn, 'carry_amount', input_values, 0.0)
                self._set_relation(trn, 'responsible', action_trn, 'responsible', input_values, master_user.responsible)
                self._set_relation(trn, 'counterparty', action_trn, 'counterparty', input_values, master_user.counterparty)

                if self._save:
                    trn.save()
                else:
                    trn.id = self._next_id()

                trn_order += 1

        return instruments, transactions

    def _next_id(self):
        self._seq -= 1
        return self._seq

    def _set_simple(self, target, target_attr_name, source, source_attr_name, input_values, default_value=None):
        value = getattr(source, source_attr_name)
        if value:
            value = formula.safe_eval(value, names=input_values)
        else:
            value = default_value
        setattr(target, target_attr_name, value)

    def _set_relation(self, target, target_attr_name, source, source_attr_name, input_values, default_value=None):
        value = getattr(source, source_attr_name, None)
        if value:
            pass
        else:
            from_input = getattr(source, '%s_input' % source_attr_name)
            if from_input:
                value = input_values[from_input.name]
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
