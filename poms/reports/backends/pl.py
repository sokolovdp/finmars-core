from poms.reports.backends.balance import BalanceReportBuilder
from poms.reports.models import PLReportTransaction, PLReportInstrument
from poms.transactions.models import TransactionClass


class PLReportBuilder(BalanceReportBuilder):
    def build(self):
        super(PLReportBuilder, self).build()

        summary = self.instance.summary
        transactions = []

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

        for t in self.transactions:
            plt = PLReportTransaction(t)
            transactions.append(plt)

            if t.transaction_class.code == TransactionClass.CASH_INFLOW:
                plt.currency = t.transaction_currency
                plt.currency_history = self.find_currency_history(t.transaction_currency, self.instance.end_date)
            elif t.transaction_class.code in [TransactionClass.BUY, TransactionClass.SELL]:
                plt.currency = t.settlement_currency
                plt.currency_history = self.find_currency_history(t.settlement_currency, self.instance.end_date)

                pli = items_index['%s' % t.instrument.id]
                pli.principal_with_sign_system_ccy += plt.principal_with_sign_system_ccy
                pli.carry_with_sign_system_ccy += plt.carry_with_sign_system_ccy
                pli.overheads_with_sign_system_ccy += plt.overheads_with_sign_system_ccy
            elif t.transaction_class.code == TransactionClass.INSTRUMENT_PL:
                plt.currency = t.settlement_currency
                plt.currency_history = self.find_currency_history(t.settlement_currency, self.instance.end_date)

                pli = items_index['%s' % t.instrument.id]
                pli.principal_with_sign_system_ccy += plt.principal_with_sign_system_ccy
                pli.carry_with_sign_system_ccy += plt.carry_with_sign_system_ccy
                pli.overheads_with_sign_system_ccy += plt.overheads_with_sign_system_ccy

            summary.principal_with_sign_system_ccy += plt.principal_with_sign_system_ccy
            summary.carry_with_sign_system_ccy += plt.carry_with_sign_system_ccy
            summary.overheads_with_sign_system_ccy += plt.overheads_with_sign_system_ccy

        self.instance.transactions = transactions

        return self.instance
