from django.core.exceptions import ObjectDoesNotExist

from poms.common import formula
from poms.instruments.models import Instrument
from poms.obj_perms.utils import assign_perms
from poms.transactions.models import Transaction, ComplexTransaction


class TransactionTypeProcessor(object):
    def __init__(self, transaction_type, input_values):
        self.transaction_type = transaction_type
        self.input_values = input_values
        self.check_mode = True

    def check(self):
        self.check_mode = True
        return self._process()

    def process(self):
        self.check_mode = False
        return self._process()

    def run(self,check_mode):
        if check_mode:
            return self.check()
        else:
            return self.process()

    def _process(self):
        input_values = self.input_values
        master_user = self.transaction_type.master_user
        actions = self.transaction_type.actions.order_by('order').all()
        user_object_permissions = self.transaction_type.user_object_permissions.select_related('permission').all()
        group_object_permissions = self.transaction_type.group_object_permissions.select_related('permission').all()

        instruments = []
        transactions = []
        results = {}
        if self.check_mode:
            ctrn = ComplexTransaction(id=-1, transaction_type=self.transaction_type)
        else:
            ctrn = ComplexTransaction.objects.create(transaction_type=self.transaction_type)
        ctrn_order = 0
        for order, action in enumerate(actions, start=1):
            try:
                ainstr = action.transactiontypeactioninstrument
            except ObjectDoesNotExist:
                ainstr = None
            try:
                atrn = action.transactiontypeactiontransaction
            except ObjectDoesNotExist:
                atrn = None
            if ainstr:
                user_code = formula.safe_eval(ainstr.user_code, names=input_values)
                if user_code:
                    try:
                        Instrument.objects.get(master_user=master_user, user_code=user_code)
                        instruments.append(instr)
                        results[ainstr.order] = instr
                        continue
                    except ObjectDoesNotExist:
                        pass

                instr = Instrument(master_user=master_user)
                instruments.append(instr)
                results[ainstr.order] = instr
                instr.user_code = user_code
                self._set_simple(instr, 'name', ainstr, 'name', input_values)
                self._set_simple(instr, 'public_name', ainstr, 'public_name', input_values)
                self._set_simple(instr, 'short_name', ainstr, 'short_name', input_values)
                self._set_simple(instr, 'notes', ainstr, 'notes', input_values)
                self._set_relation(instr, 'instrument_type', ainstr, 'instrument_type', input_values)
                self._set_relation(instr, 'pricing_currency', ainstr, 'pricing_currency', input_values)
                self._set_simple(instr, 'price_multiplier', ainstr, 'price_multiplier', input_values)
                self._set_relation(instr, 'accrued_currency', ainstr, 'accrued_currency', input_values)
                self._set_simple(instr, 'accrued_multiplier', ainstr, 'accrued_multiplier', input_values)
                self._set_relation(instr, 'daily_pricing_model', ainstr, 'daily_pricing_model', input_values)
                self._set_relation(instr, 'payment_size_detail', ainstr, 'payment_size_detail', input_values)
                self._set_simple(instr, 'default_price', ainstr, 'default_price', input_values)
                self._set_simple(instr, 'default_accrued', ainstr, 'default_accrued', input_values)
                self._set_simple(instr, 'user_text_1', ainstr, 'user_text_1', input_values)
                self._set_simple(instr, 'user_text_2', ainstr, 'user_text_2', input_values)
                self._set_simple(instr, 'user_text_3', ainstr, 'user_text_3', input_values)
                if self.check_mode:
                    instr.id = -order
                else:
                    instr.save()
                    perms_map = {
                        'add_transactiontype': 'add_instrument',
                        'view_transactiontype': 'view_instrument',
                        'change_transactiontype': 'change_instrument',
                        'delete_transactiontype': 'delete_instrument',
                    }
                    for uop in user_object_permissions:
                        if uop.permission.codename in perms_map:
                            perms = [perms_map[uop.permission.codename], ]
                            assign_perms(instr, members=[uop.member], groups=None, perms=perms)
                    for gop in group_object_permissions:
                        if gop.permission.codename in perms_map:
                            perms = [perms_map[gop.permission.codename], ]
                            assign_perms(instr, members=None, groups=[gop.group], perms=perms)
            elif atrn:
                ctrn_order += 1
                trn = Transaction(master_user=master_user)
                transactions.append(trn)
                results[order] = trn
                trn.complex_transaction = ctrn
                trn.complex_transaction_order = ctrn_order
                trn.transaction_class = atrn.transaction_class
                self._set_relation(trn, 'portfolio', atrn, 'portfolio', input_values)
                self._set_relation(trn, 'instrument', atrn, 'instrument', input_values)
                if trn.instrument is None and atrn.instrument_phantom is not None:
                    trn.instrument = results[atrn.instrument_phantom.order]
                self._set_relation(trn, 'transaction_currency', atrn, 'transaction_currency', input_values)
                self._set_simple(trn, 'position_size_with_sign', atrn, 'position_size_with_sign', input_values)
                self._set_relation(trn, 'settlement_currency', atrn, 'settlement_currency', input_values)
                self._set_simple(trn, 'cash_consideration', atrn, 'cash_consideration', input_values)
                self._set_simple(trn, 'principal_with_sign', atrn, 'principal_with_sign', input_values)
                self._set_simple(trn, 'carry_with_sign', atrn, 'carry_with_sign', input_values)
                self._set_simple(trn, 'overheads_with_sign', atrn, 'overheads_with_sign', input_values)
                self._set_relation(trn, 'account_position', atrn, 'account_position', input_values)
                self._set_relation(trn, 'account_cash', atrn, 'account_cash', input_values)
                self._set_relation(trn, 'account_interim', atrn, 'account_interim', input_values)
                self._set_simple(trn, 'accounting_date', atrn, 'accounting_date', input_values)
                self._set_simple(trn, 'cash_date', atrn, 'cash_date', input_values)
                trn.transaction_date = min(trn.accounting_date, trn.cash_date)
                self._set_relation(trn, 'strategy1_position', atrn, 'strategy1_position', input_values)
                self._set_relation(trn, 'strategy1_cash', atrn, 'strategy1_cash', input_values)
                self._set_relation(trn, 'strategy2_position', atrn, 'strategy2_position', input_values)
                self._set_relation(trn, 'strategy2_cash', atrn, 'strategy2_cash', input_values)
                self._set_relation(trn, 'strategy3_position', atrn, 'strategy3_position', input_values)
                self._set_relation(trn, 'strategy3_cash', atrn, 'strategy3_cash', input_values)
                self._set_simple(trn, 'factor', atrn, 'factor', input_values)
                self._set_simple(trn, 'trade_price', atrn, 'trade_price', input_values)
                self._set_simple(trn, 'principal_amount', atrn, 'principal_amount', input_values)
                self._set_simple(trn, 'carry_amount', atrn, 'carry_amount', input_values)
                self._set_relation(trn, 'responsible', atrn, 'responsible', input_values)
                self._set_relation(trn, 'counterparty', atrn, 'counterparty', input_values)
                if self.check_mode:
                    trn.id = -order
                else:
                    trn.save()
        return instruments, transactions

    def _set_simple(self, obj, name, tobj, tname, input_values):
        value = getattr(tobj, tname)
        if value:
            value = formula.safe_eval(value, names=input_values)
            setattr(obj, name, value)

    def _set_relation(self, obj, name, tobj, tname, input_values):
        value = getattr(tobj, tname, None)
        if value is None:
            inp = getattr(tobj, '%s_input' % tname)
            if inp:
                value = input_values[inp.name]
        setattr(obj, name, value)
