from poms.reports.backends.balance import BalanceReportBuilder
from poms.reports.models import PLReportInstrument
from poms.transactions.models import TransactionClass


class PLReportBuilder(BalanceReportBuilder):
    def build(self):
        super(PLReportBuilder, self).build()

        summary = self.instance.summary
        items_index = {}
        items = []

        for i in self.instance.items:
            if i.instrument:
                pli = PLReportInstrument(i.instrument)
                items.append(pli)
                items_index['%s' % pli.pk] = pli

                summary.principal_with_sign_system_ccy += i.principal_value_instrument_system_ccy
                summary.carry_with_sign_system_ccy += i.accrued_value_instrument_system_ccy

                pli.principal_with_sign_system_ccy += i.principal_value_instrument_system_ccy
                pli.carry_with_sign_system_ccy += i.accrued_value_instrument_system_ccy
        self.instance.items = items

        self.annotate_fx_rates_and_prices()

        for t in self.transactions:
            t.transaction_class_code = t.transaction_class.code
            # if t.transaction_currency:
            #     t.transaction_currency_name = t.transaction_currency.name
            # if t.instrument:
            #     t.instrument_name = t.instrument.name
            # if t.settlement_currency:
            #     t.settlement_currency_name = t.settlement_currency.name

            if t.transaction_class.code == TransactionClass.CASH_INFLOW:
                t.principal_with_sign_system_ccy = t.principal_with_sign * t.transaction_currency_fx_rate
                t.carry_with_sign_system_ccy = t.carry_with_sign * t.transaction_currency_fx_rate
                t.overheads_with_sign_system_ccy = t.overheads_with_sign * t.transaction_currency_fx_rate
            elif t.transaction_class.code in [TransactionClass.BUY, TransactionClass.SELL]:
                t.principal_with_sign_system_ccy = t.principal_with_sign * t.settlement_currency_fx_rate
                t.carry_with_sign_system_ccy = t.carry_with_sign * t.settlement_currency_fx_rate
                t.overheads_with_sign_system_ccy = t.overheads_with_sign * t.settlement_currency_fx_rate
            elif t.transaction_class.code == TransactionClass.INSTRUMENT_PL:
                t.principal_with_sign_system_ccy = t.principal_with_sign * t.settlement_currency_fx_rate
                t.carry_with_sign_system_ccy = t.carry_with_sign * t.settlement_currency_fx_rate
                t.overheads_with_sign_system_ccy = t.overheads_with_sign * t.settlement_currency_fx_rate

            summary.principal_with_sign_system_ccy += getattr(t, 'principal_with_sign_system_ccy', 0.)
            summary.carry_with_sign_system_ccy += getattr(t, 'carry_with_sign_system_ccy', 0.)
            summary.overheads_with_sign_system_ccy += getattr(t, 'overheads_with_sign_system_ccy', 0.)

        # for t in self.transactions:
        #     plt = PLReportTransaction(t)
        #     transactions.append(plt)
        #
        #     is_update_report_instrument = False
        #     is_update_summary = False
        #
        #     if t.transaction_class.code == TransactionClass.CASH_INFLOW:
        #         plt.currency = t.transaction_currency
        #         plt.currency_history = self.find_currency_history(t.transaction_currency, self.instance.end_date)
        #     elif t.transaction_class.code in [TransactionClass.BUY, TransactionClass.SELL]:
        #         plt.currency = t.settlement_currency
        #         plt.currency_history = self.find_currency_history(t.settlement_currency, self.instance.end_date)
        #
        #         is_update_report_instrument = True
        #         is_update_summary = True
        #     elif t.transaction_class.code == TransactionClass.INSTRUMENT_PL:
        #         plt.currency = t.settlement_currency
        #         plt.currency_history = self.find_currency_history(t.settlement_currency, self.instance.end_date)
        #
        #         is_update_report_instrument = True
        #         is_update_summary = True
        #
        #     if is_update_report_instrument:
        #         pli = items_index['%s' % t.instrument.id]
        #         pli.principal_with_sign_system_ccy += plt.principal_with_sign_system_ccy
        #         pli.carry_with_sign_system_ccy += plt.carry_with_sign_system_ccy
        #         pli.overheads_with_sign_system_ccy += plt.overheads_with_sign_system_ccy
        #
        #     if is_update_summary:
        #         summary.principal_with_sign_system_ccy += plt.principal_with_sign_system_ccy
        #         summary.carry_with_sign_system_ccy += plt.carry_with_sign_system_ccy
        #         summary.overheads_with_sign_system_ccy += plt.overheads_with_sign_system_ccy

        self.instance.transactions = self.transactions

        return self.instance
