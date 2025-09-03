import logging
import time
import traceback
from datetime import timedelta

from django.db import connection

from poms.accounts.models import Account, AccountType
from poms.common.utils import (
    get_last_business_day,
    get_last_business_day_in_previous_quarter,
    get_last_business_day_of_previous_month,
    get_last_business_day_of_previous_year,
)
from poms.counterparties.models import Counterparty, Responsible
from poms.currencies.models import Currency
from poms.iam.utils import get_allowed_queryset
from poms.instruments.models import Country, Instrument, InstrumentType
from poms.portfolios.models import Portfolio
from poms.reports.common import Report
from poms.reports.models import TransactionReportCustomField
from poms.reports.sql_builders.helpers import (
    dictfetchall,
    get_transaction_report_date_filter_sql_string,
    get_transaction_report_filter_sql_string,
)
from poms.strategies.models import Strategy1, Strategy2, Strategy3
from poms.transactions.models import (
    ComplexTransaction,
    ComplexTransactionStatus,
    TransactionClass,
)
from poms.users.models import EcosystemDefault

_l = logging.getLogger("poms.reports")


class TransactionReportBuilderSql:
    def __init__(self, instance=None):
        _l.debug("ReportBuilderSql init")

        self.instance = instance

        self.ecosystem_defaults = EcosystemDefault.cache.get_cache(master_user_pk=self.instance.master_user.pk)

        _l.debug("self.instance master_user %s", self.instance.master_user)
        _l.debug("self.instance begin_date %s", self.instance.begin_date)
        _l.debug("self.instance end_date %s", self.instance.end_date)

        if self.instance.period_type:
            if self.instance.period_type == Report.PERIOD_TYPE_INCEPTION:
                # TODO wtf is first transaction when multi portfolios?
                # TODO ask oleg what to do with inception
                first_portfolio = self.instance.portfolios.first()
                self.instance.begin_date = get_last_business_day(
                    first_portfolio.first_transaction_date - timedelta(days=1),
                )
            elif self.instance.period_type == Report.PERIOD_TYPE_YTD:
                self.instance.begin_date = get_last_business_day_of_previous_year(self.instance.end_date)
            elif self.instance.period_type == Report.PERIOD_TYPE_QTD:
                self.instance.begin_date = get_last_business_day_in_previous_quarter(self.instance.end_date)
            elif self.instance.period_type == Report.PERIOD_TYPE_MTD:
                self.instance.begin_date = get_last_business_day_of_previous_month(self.instance.end_date)
            elif self.instance.period_type == Report.PERIOD_TYPE_DAILY:
                self.instance.begin_date = get_last_business_day(self.instance.end_date - timedelta(days=1))

        # TODO IAM_SECURITY_VERIFY need to check, if user somehow passes id of object
        #  he has no access to we should throw error'''

        if self.instance.bundle and self.instance.portfolios:
            raise Exception("Both portfolios and bundle provided. Only one of them should be provided.")

        if self.instance.bundle:
            self.instance.portfolios = []
            for register in self.instance.bundle.registers.all():
                self.instance.portfolios.append(register.portfolio)

        """Important security methods"""
        self.transform_to_allowed_portfolios()
        self.transform_to_allowed_accounts()

    def transform_to_allowed_portfolios(self):
        if not len(self.instance.portfolios):
            self.instance.portfolios = get_allowed_queryset(self.instance.member, Portfolio.objects.all())

    def transform_to_allowed_accounts(self):
        if not len(self.instance.accounts):
            self.instance.accounts = get_allowed_queryset(self.instance.member, Account.objects.all())

    def build_transaction(self):
        st = time.perf_counter()

        self.instance.items = []

        self.build_items()

        self.instance.execution_time = float(f"{time.perf_counter() - st:3.3f}")

        _l.debug("items total %s", len(self.instance.items))

        _l.debug("build_st done: %s", f"{time.perf_counter() - st:3.3f}")

        relation_prefetch_st = time.perf_counter()

        if self.instance.depth_level != "complex_transaction":
            self.add_data_items()
        else:
            # TODO Figure Out
            self.instance.item_instrument_types = []
            self.instance.item_account_types = []

        self.instance.relation_prefetch_time = float(f"{time.perf_counter() - relation_prefetch_st:3.3f}")

        return self.instance

    def add_user_filters(self):  # noqa: PLR0912, PLR0915
        if not self.instance.filters:
            return ""

        portfolios = list(Portfolio.objects.all().values("id", "user_code", "short_name", "name", "public_name"))
        instruments = list(Instrument.objects.all().values("id", "user_code", "short_name", "name", "public_name"))
        currencies = list(Currency.objects.all().values("id", "user_code", "short_name", "name", "public_name"))

        _l.debug(f"add_user_filters.instruments count {len(instruments)}")

        result = ""
        try:
            for filter in self.instance.filters:
                if filter["options"]["enabled"] and filter["options"]["filter_values"]:
                    if filter["key"] in [
                        "portfolio.user_code",
                        "portfolio.name",
                        "portfolio.short_name",
                        "portfolio.public_name",
                    ]:
                        field_key = filter["key"].split(".")[1]

                        portfolio_ids = []

                        for portfolio in portfolios:
                            portfolio_ids.extend(
                                str(portfolio["id"])
                                for value in filter["options"]["filter_values"]
                                if value == portfolio[field_key]
                            )
                        _l.debug(f"portfolio_ids {portfolio_ids}")

                        if portfolio_ids:
                            res = "'" + "','".join(portfolio_ids)
                            res = f"{res}'"

                            result = f"{result}and t.portfolio_id IN ({res})"

                    if filter["key"] in {
                        "instrument.user_code",
                        "instrument.name",
                        "instrument.short_name",
                        "instrument.public_name",
                    }:
                        field_key = filter["key"].split(".")[1]

                        instrument_ids = []

                        for instrument in instruments:
                            instrument_ids.extend(
                                str(instrument["id"])
                                for value in filter["options"]["filter_values"]
                                if value == instrument[field_key]
                            )

                        if instrument_ids:
                            res = "'" + "','".join(instrument_ids)
                            res = f"{res}'"
                            result = f"{result}and t.instrument_id IN ({res})"

                    if filter["key"] in ["entry_item_user_code"]:
                        instrument_ids = []

                        for instrument in instruments:
                            instrument_ids.extend(
                                str(instrument["id"])
                                for value in filter["options"]["filter_values"]
                                if value == instrument["user_code"]
                            )
                        _l.debug(f"instrument_ids {instrument_ids}")

                        instrument_expression = ""

                        if instrument_ids:
                            res = "'" + "','".join(instrument_ids)
                            res = f"{res}'"

                            instrument_expression = f"t.instrument_id IN ({res})"

                        currencies_ids = []

                        for currency in currencies:
                            currencies_ids.extend(
                                str(currency["id"])
                                for value in filter["options"]["filter_values"]
                                if value == currency["user_code"]
                            )
                        _l.debug(f"currencies_ids {currencies_ids}")

                        settlement_currency_expression = ""
                        transaction_currency_expression = ""

                        if currencies_ids:
                            res = "'" + "','".join(currencies_ids)
                            res = f"{res}'"

                            settlement_currency_expression = f"t.settlement_currency_id IN ({res})"
                            res = "'" + "','".join(currencies_ids)
                            res = f"{res}'"

                            transaction_currency_expression = f"t.transaction_currency_id IN ({res})"
                        # _l.debug('result %s' % result)

                        if instrument_expression and (
                            settlement_currency_expression and transaction_currency_expression
                        ):
                            result = (
                                f"{result}and ({instrument_expression} or {settlement_currency_expression}"
                                f" or {transaction_currency_expression})"
                            )

                        elif instrument_expression:
                            result = f"{result}and {instrument_expression}"

                        elif settlement_currency_expression and transaction_currency_expression:
                            result = (
                                f"{result}and ({settlement_currency_expression} or {transaction_currency_expression})"
                            )

        except Exception as e:
            _l.error(f"User filters layout error {e}")
            _l.error(f"User filters layout traceback {traceback.format_exc()}")

        return result

    def build_complex_transaction_level_items(self):
        _l.debug("build_complex_transaction_level_items")

        with connection.cursor() as cursor:
            filter_sql_string = get_transaction_report_filter_sql_string(self.instance)
            date_filter_sql_string = get_transaction_report_date_filter_sql_string(self.instance)

            query = """
                    SELECT
                      -- transaction fields
                      -- t.*,-- exclude transaction fields, only complex transaction fields left
                      -- complex transaction fields
                      
                      (null) as transaction_item_name,
                      (null) as transaction_item_short_name,
                      (null) as transaction_item_user_code,
                      
                      tc.id as complex_transaction_id,
                      tc.status_id as complex_transaction_status,
                      tc.code as complex_transaction_code,
                      tc.text as complex_transaction_text,
                      tc.date as complex_transaction_date,
                      tc.transaction_unique_code as transaction_unique_code,
                      tc.is_locked as is_locked,
                      tc.is_canceled as is_canceled,
                      -- complex transaction user fields
                      tc.user_text_1 as complex_transaction_user_text_1,
                      tc.user_text_2 as complex_transaction_user_text_2,
                      tc.user_text_3 as complex_transaction_user_text_3,
                      tc.user_text_4 as complex_transaction_user_text_4,
                      tc.user_text_5 as complex_transaction_user_text_5,
                      tc.user_text_6 as complex_transaction_user_text_6,
                      tc.user_text_7 as complex_transaction_user_text_7,
                      tc.user_text_8 as complex_transaction_user_text_8,
                      tc.user_text_9 as complex_transaction_user_text_9,
                      tc.user_text_10 as complex_transaction_user_text_10,
                      tc.user_text_11 as complex_transaction_user_text_11,
                      tc.user_text_12 as complex_transaction_user_text_12,
                      tc.user_text_13 as complex_transaction_user_text_13,
                      tc.user_text_14 as complex_transaction_user_text_14,
                      tc.user_text_15 as complex_transaction_user_text_15,
                      tc.user_text_16 as complex_transaction_user_text_16,
                      tc.user_text_17 as complex_transaction_user_text_17,
                      tc.user_text_18 as complex_transaction_user_text_18,
                      tc.user_text_19 as complex_transaction_user_text_19,
                      tc.user_text_20 as complex_transaction_user_text_20,
                      
                      tc.user_number_1 as complex_transaction_user_number_1,
                      tc.user_number_2 as complex_transaction_user_number_2,
                      tc.user_number_3 as complex_transaction_user_number_3,
                      tc.user_number_4 as complex_transaction_user_number_4,
                      tc.user_number_5 as complex_transaction_user_number_5,
                      tc.user_number_6 as complex_transaction_user_number_6,
                      tc.user_number_7 as complex_transaction_user_number_7,
                      tc.user_number_8 as complex_transaction_user_number_8,
                      tc.user_number_9 as complex_transaction_user_number_9,
                      tc.user_number_10 as complex_transaction_user_number_10,
                      tc.user_number_11 as complex_transaction_user_number_11,
                      tc.user_number_12 as complex_transaction_user_number_12,
                      tc.user_number_13 as complex_transaction_user_number_13,
                      tc.user_number_14 as complex_transaction_user_number_14,
                      tc.user_number_15 as complex_transaction_user_number_15,
                      tc.user_number_16 as complex_transaction_user_number_16,
                      tc.user_number_17 as complex_transaction_user_number_17,
                      tc.user_number_18 as complex_transaction_user_number_18,
                      tc.user_number_19 as complex_transaction_user_number_19,
                      tc.user_number_20 as complex_transaction_user_number_20,
                      
                      tc.user_date_1 as complex_transaction_user_date_1,
                      tc.user_date_2 as complex_transaction_user_date_2,
                      tc.user_date_3 as complex_transaction_user_date_3,
                      tc.user_date_4 as complex_transaction_user_date_4,
                      tc.user_date_5 as complex_transaction_user_date_5,
                      
                      -- complex transaction transaction type fields
                      tt.id as transaction_type_id,
                      tt.user_code as transaction_type_user_code,
                      tt.name as transaction_type_name,
                      tt.short_name as transaction_type_short_name,
                      -- complex transaction transaction type group fields
                      --tt2.name as transaction_type_group_name,-- ?? 
                      
                      cts.name as complex_transaction_status_name
                      
                    FROM transactions_transaction as t
                    INNER JOIN transactions_complextransaction tc on t.complex_transaction_id = tc.id
                    INNER JOIN transactions_transactiontype tt on tc.transaction_type_id = tt.id
                    --INNER JOIN transactions_transactiontypegroup tt2 on tt.group_id = tt2.id--
                    INNER JOIN transactions_complextransactionstatus cts on tc.status_id = cts.id
                    WHERE {date_filter_sql_string} AND t.master_user_id = {master_user_id} AND NOT tc.is_deleted AND NOT tc.is_canceled AND tc.status_id IN {statuses} {filter_sql_string}
                    
                    
                """

            # statuses = ['1', '3']
            statuses = ["1"]  # FN-1327

            _l.debug("complex_transaction_statuses_filter %s", self.instance.complex_transaction_statuses_filter)

            if self.instance.complex_transaction_statuses_filter:
                pieces = self.instance.complex_transaction_statuses_filter.split(",")

                if len(pieces):
                    statuses = []
                    if "booked" in pieces:
                        statuses.append("1")
                    if "ignored" in pieces:
                        statuses.append("3")

            statuses_str = (",").join(statuses)
            statuses_str = "(" + statuses_str + ")"

            query = query.format(
                begin_date=self.instance.begin_date,
                end_date=self.instance.end_date,
                master_user_id=self.instance.master_user.id,
                default_instrument_id=self.ecosystem_defaults.instrument_id,
                statuses=statuses_str,
                filter_sql_string=filter_sql_string,
                date_filter_sql_string=date_filter_sql_string,
            )

            # cursor.execute(query, [self.instance.begin_date, self.instance.end_date, self.instance.master_user.id, statuses, filter_sql_string]) # noqa: E501
            cursor.execute(query)

            result = dictfetchall(cursor)

            for result_item in result:
                result_item["id"] = result_item["complex_transaction_id"]
                result_item["code"] = result_item["complex_transaction_code"]
                result_item["entry_account"] = None
                result_item["entry_strategy"] = None
                result_item["entry_item_name"] = None  # Should be filled later
                result_item["entry_item_short_name"] = None  # Should be filled later
                result_item["entry_item_user_code"] = None  # Should be filled later
                result_item["entry_item_public_name"] = None  # Should be filled later
                result_item["entry_currency"] = None
                result_item["entry_instrument"] = None
                result_item["entry_amount"] = None
                result_item["entry_item_type"] = None
                result_item["entry_item_type_name"] = None

            self.instance.items = result

    def build_base_transaction_level_items(self):
        _l.debug("build_base_transaction_level_items")

        with connection.cursor() as cursor:
            filter_sql_string = get_transaction_report_filter_sql_string(self.instance)
            date_filter_sql_string = get_transaction_report_date_filter_sql_string(self.instance)

            user_filters = self.add_user_filters()

            query = """
                    SELECT
                      -- transaction fields
                      t.*,
                      
                      case when (t.instrument_id = null OR t.instrument_id = {default_instrument_id})
                         then t.notes
                         else
                           i.name
                      end as transaction_item_name,
                      
                      case when (t.instrument_id = null OR t.instrument_id = {default_instrument_id})
                         then t.notes
                         else
                           i.user_code
                      end as transaction_item_user_code,
                      
                      case when (t.instrument_id = null OR t.instrument_id = {default_instrument_id})
                         then t.notes
                         else
                           i.short_name
                      end as transaction_item_short_name,
                      -- complex transaction fields
                      tc.status_id as complex_transaction_status,
                      tc.id as complex_transaction_id,
                      tc.code as complex_transaction_code,
                      tc.text as complex_transaction_text,
                      tc.date as complex_transaction_date,
                      tc.transaction_unique_code as transaction_unique_code,
                      tc.is_locked as is_locked,
                      tc.is_canceled as is_canceled,
                      -- complex transaction user fields
                      tc.user_text_1 as complex_transaction_user_text_1,
                      tc.user_text_2 as complex_transaction_user_text_2,
                      tc.user_text_3 as complex_transaction_user_text_3,
                      tc.user_text_4 as complex_transaction_user_text_4,
                      tc.user_text_5 as complex_transaction_user_text_5,
                      tc.user_text_6 as complex_transaction_user_text_6,
                      tc.user_text_7 as complex_transaction_user_text_7,
                      tc.user_text_8 as complex_transaction_user_text_8,
                      tc.user_text_9 as complex_transaction_user_text_9,
                      tc.user_text_10 as complex_transaction_user_text_10,
                      tc.user_text_11 as complex_transaction_user_text_11,
                      tc.user_text_12 as complex_transaction_user_text_12,
                      tc.user_text_13 as complex_transaction_user_text_13,
                      tc.user_text_14 as complex_transaction_user_text_14,
                      tc.user_text_15 as complex_transaction_user_text_15,
                      tc.user_text_16 as complex_transaction_user_text_16,
                      tc.user_text_17 as complex_transaction_user_text_17,
                      tc.user_text_18 as complex_transaction_user_text_18,
                      tc.user_text_19 as complex_transaction_user_text_19,
                      tc.user_text_20 as complex_transaction_user_text_20,
                      
                      tc.user_number_1 as complex_transaction_user_number_1,
                      tc.user_number_2 as complex_transaction_user_number_2,
                      tc.user_number_3 as complex_transaction_user_number_3,
                      tc.user_number_4 as complex_transaction_user_number_4,
                      tc.user_number_5 as complex_transaction_user_number_5,
                      tc.user_number_6 as complex_transaction_user_number_6,
                      tc.user_number_7 as complex_transaction_user_number_7,
                      tc.user_number_8 as complex_transaction_user_number_8,
                      tc.user_number_9 as complex_transaction_user_number_9,
                      tc.user_number_10 as complex_transaction_user_number_10,
                      tc.user_number_11 as complex_transaction_user_number_11,
                      tc.user_number_12 as complex_transaction_user_number_12,
                      tc.user_number_13 as complex_transaction_user_number_13,
                      tc.user_number_14 as complex_transaction_user_number_14,
                      tc.user_number_15 as complex_transaction_user_number_15,
                      tc.user_number_16 as complex_transaction_user_number_16,
                      tc.user_number_17 as complex_transaction_user_number_17,
                      tc.user_number_18 as complex_transaction_user_number_18,
                      tc.user_number_19 as complex_transaction_user_number_19,
                      tc.user_number_20 as complex_transaction_user_number_20,
                      
                      tc.user_date_1 as complex_transaction_user_date_1,
                      tc.user_date_2 as complex_transaction_user_date_2,
                      tc.user_date_3 as complex_transaction_user_date_3,
                      tc.user_date_4 as complex_transaction_user_date_4,
                      tc.user_date_5 as complex_transaction_user_date_5,
                      
                      -- complex transaction transaction type fields
                      tt.id as transaction_type_id,
                      tt.user_code as transaction_type_user_code,
                      tt.name as transaction_type_name,
                      tt.short_name as transaction_type_short_name,
                      -- complex transaction transaction type group fields
                      --tt2.name as transaction_type_group_name, --?
                      
                      cts.name as complex_transaction_status_name
                    FROM transactions_transaction as t
                    INNER JOIN transactions_complextransaction tc on t.complex_transaction_id = tc.id
                    INNER JOIN transactions_transactiontype tt on tc.transaction_type_id = tt.id
                    --INNER JOIN transactions_transactiontypegroup tt2 on tt.group_id = tt2.id--
                    INNER JOIN instruments_instrument i on t.instrument_id = i.id
                    INNER JOIN transactions_complextransactionstatus cts on tc.status_id = cts.id
                    WHERE {date_filter_sql_string} AND t.master_user_id = {master_user_id} AND NOT t.is_deleted AND NOT t.is_canceled AND tc.status_id IN {statuses} {filter_sql_string}
                    {user_filters}
                    
                """

            # statuses = ['1', '3']
            statuses = ["1"]  # FN-1327

            _l.debug("complex_transaction_statuses_filter %s", self.instance.complex_transaction_statuses_filter)

            if self.instance.complex_transaction_statuses_filter:
                pieces = self.instance.complex_transaction_statuses_filter.split(",")

                if len(pieces):
                    statuses = []
                    if "booked" in pieces:
                        statuses.append("1")
                    if "ignored" in pieces:
                        statuses.append("3")

            statuses_str = (",").join(statuses)
            statuses_str = "(" + statuses_str + ")"

            query = query.format(
                begin_date=self.instance.begin_date,
                end_date=self.instance.end_date,
                master_user_id=self.instance.master_user.id,
                default_instrument_id=self.ecosystem_defaults.instrument_id,
                statuses=statuses_str,
                filter_sql_string=filter_sql_string,
                date_filter_sql_string=date_filter_sql_string,
                user_filters=user_filters,
            )

            # cursor.execute(query, [self.instance.begin_date, self.instance.end_date, self.instance.master_user.id, statuses, filter_sql_string]) # noqa: E501
            cursor.execute(query)

            result = dictfetchall(cursor)

            for result_item in result:
                result_item["entry_account"] = None
                result_item["entry_strategy"] = None
                result_item["entry_item_name"] = None  # Should be filled later
                result_item["entry_item_short_name"] = None  # Should be filled later
                result_item["entry_item_user_code"] = None  # Should be filled later
                result_item["entry_item_public_name"] = None  # Should be filled later
                result_item["entry_currency"] = None
                result_item["entry_instrument"] = None
                result_item["entry_amount"] = None
                result_item["entry_item_type"] = None
                result_item["entry_item_type_name"] = None

            self.instance.items = result

    def build_entry_level_items(self):  # noqa: PLR0912, PLR0915
        _l.debug("build_entry_level_items")

        with connection.cursor() as cursor:
            filter_sql_string = get_transaction_report_filter_sql_string(self.instance)
            date_filter_sql_string = get_transaction_report_date_filter_sql_string(self.instance)
            user_filters = self.add_user_filters()

            query = """
                    SELECT
                        
                      
                    
                      -- transaction fields
                      t.*,
                      
                      case when (t.instrument_id = null OR t.instrument_id = {default_instrument_id})
                         then t.notes
                         else
                           i.name
                      end as transaction_item_name,
                      
                      case when (t.instrument_id = null OR t.instrument_id = {default_instrument_id})
                         then t.notes
                         else
                           i.user_code
                      end as transaction_item_user_code,
                      
                      case when (t.instrument_id = null OR t.instrument_id = {default_instrument_id})
                         then t.notes
                         else
                           i.short_name
                      end as transaction_item_short_name,
                      
                      -- complex transaction fields
                      tc.id as complex_transaction_id,
                      tc.status_id as complex_transaction_status,
                      tc.code as complex_transaction_code,
                      tc.text as complex_transaction_text,
                      tc.date as complex_transaction_date,
                      tc.transaction_unique_code as transaction_unique_code,
                      tc.is_locked as is_locked,
                      tc.is_canceled as is_canceled,
                      -- complex transaction user fields
                      tc.user_text_1 as complex_transaction_user_text_1,
                      tc.user_text_2 as complex_transaction_user_text_2,
                      tc.user_text_3 as complex_transaction_user_text_3,
                      tc.user_text_4 as complex_transaction_user_text_4,
                      tc.user_text_5 as complex_transaction_user_text_5,
                      tc.user_text_6 as complex_transaction_user_text_6,
                      tc.user_text_7 as complex_transaction_user_text_7,
                      tc.user_text_8 as complex_transaction_user_text_8,
                      tc.user_text_9 as complex_transaction_user_text_9,
                      tc.user_text_10 as complex_transaction_user_text_10,
                      tc.user_text_11 as complex_transaction_user_text_11,
                      tc.user_text_12 as complex_transaction_user_text_12,
                      tc.user_text_13 as complex_transaction_user_text_13,
                      tc.user_text_14 as complex_transaction_user_text_14,
                      tc.user_text_15 as complex_transaction_user_text_15,
                      tc.user_text_16 as complex_transaction_user_text_16,
                      tc.user_text_17 as complex_transaction_user_text_17,
                      tc.user_text_18 as complex_transaction_user_text_18,
                      tc.user_text_19 as complex_transaction_user_text_19,
                      tc.user_text_20 as complex_transaction_user_text_20,
                      
                      tc.user_number_1 as complex_transaction_user_number_1,
                      tc.user_number_2 as complex_transaction_user_number_2,
                      tc.user_number_3 as complex_transaction_user_number_3,
                      tc.user_number_4 as complex_transaction_user_number_4,
                      tc.user_number_5 as complex_transaction_user_number_5,
                      tc.user_number_6 as complex_transaction_user_number_6,
                      tc.user_number_7 as complex_transaction_user_number_7,
                      tc.user_number_8 as complex_transaction_user_number_8,
                      tc.user_number_9 as complex_transaction_user_number_9,
                      tc.user_number_10 as complex_transaction_user_number_10,
                      tc.user_number_11 as complex_transaction_user_number_11,
                      tc.user_number_12 as complex_transaction_user_number_12,
                      tc.user_number_13 as complex_transaction_user_number_13,
                      tc.user_number_14 as complex_transaction_user_number_14,
                      tc.user_number_15 as complex_transaction_user_number_15,
                      tc.user_number_16 as complex_transaction_user_number_16,
                      tc.user_number_17 as complex_transaction_user_number_17,
                      tc.user_number_18 as complex_transaction_user_number_18,
                      tc.user_number_19 as complex_transaction_user_number_19,
                      tc.user_number_20 as complex_transaction_user_number_20,
                      
                      tc.user_date_1 as complex_transaction_user_date_1,
                      tc.user_date_2 as complex_transaction_user_date_2,
                      tc.user_date_3 as complex_transaction_user_date_3,
                      tc.user_date_4 as complex_transaction_user_date_4,
                      tc.user_date_5 as complex_transaction_user_date_5,
                      
                      -- complex transaction transaction type fields
                      tt.id as transaction_type_id,
                      tt.user_code as transaction_type_user_code,
                      tt.name as transaction_type_name,
                      tt.short_name as transaction_type_short_name,
                      -- complex transaction transaction type group fields
                      --tt2.name as transaction_type_group_name, --?
                      
                      cts.name as complex_transaction_status_name
                    FROM transactions_transaction as t
                    INNER JOIN transactions_complextransaction tc on t.complex_transaction_id = tc.id
                    INNER JOIN transactions_transactiontype tt on tc.transaction_type_id = tt.id
                    INNER JOIN instruments_instrument i on t.instrument_id = i.id
                    --INNER JOIN transactions_transactiontypegroup tt2 on tt.group_id = tt2.id--
                    INNER JOIN transactions_complextransactionstatus cts on tc.status_id = cts.id
                    WHERE {date_filter_sql_string} AND t.master_user_id = {master_user_id} AND NOT t.is_deleted AND NOT t.is_canceled AND tc.status_id IN {statuses} {filter_sql_string}
                    {user_filters}
                    
                    
                """

            # statuses = ['1', '3']
            statuses = ["1"]  # FN-1327

            _l.debug("complex_transaction_statuses_filter %s", self.instance.complex_transaction_statuses_filter)

            if self.instance.complex_transaction_statuses_filter:
                pieces = self.instance.complex_transaction_statuses_filter.split(",")

                if len(pieces):
                    statuses = []
                    if "booked" in pieces:
                        statuses.append("1")
                    if "ignored" in pieces:
                        statuses.append("3")

            statuses_str = (",").join(statuses)
            statuses_str = "(" + statuses_str + ")"

            query = query.format(
                begin_date=self.instance.begin_date,
                end_date=self.instance.end_date,
                default_instrument_id=self.ecosystem_defaults.instrument_id,
                master_user_id=self.instance.master_user.id,
                statuses=statuses_str,
                filter_sql_string=filter_sql_string,
                date_filter_sql_string=date_filter_sql_string,
                user_filters=user_filters,
            )

            # cursor.execute(query, [self.instance.begin_date, self.instance.end_date, self.instance.master_user.id, statuses, filter_sql_string]) # noqa: E501
            cursor.execute(query)

            raw_results = dictfetchall(cursor)
            results = []

            ITEM_TYPE_INSTRUMENT = 1
            ITEM_TYPE_CURRENCY = 2
            ITEM_TYPE_FX_VARIATIONS = 3
            ITEM_TYPE_FX_TRADES = 4
            ITEM_TYPE_TRANSACTION_PL = 5
            ITEM_TYPE_MISMATCH = 6
            ITEM_TYPE_EXPOSURE_COPY = 7

            _l.debug("transaction_report.raw_results.count %s", len(raw_results))

            for raw_item in raw_results:
                result_item = raw_item.copy()

                result_item["entry_account"] = None
                result_item["entry_strategy"] = None
                result_item["entry_item_name"] = None  # Should be filled later
                result_item["entry_item_short_name"] = None  # Should be filled later
                result_item["entry_item_user_code"] = None  # Should be filled later
                result_item["entry_item_public_name"] = None  # Should be filled later
                result_item["entry_currency"] = None
                result_item["entry_instrument"] = None
                result_item["entry_amount"] = None
                result_item["entry_item_type"] = None
                result_item["entry_item_type_name"] = None

                if (
                    result_item["transaction_class_id"] == TransactionClass.CASH_INFLOW
                    or result_item["transaction_class_id"] == TransactionClass.CASH_OUTFLOW
                    or result_item["transaction_class_id"] == TransactionClass.DISTRIBUTION
                    or result_item["transaction_class_id"] == TransactionClass.INJECTION
                ):
                    if (
                        self.instance.end_date < result_item["accounting_date"]
                        and self.instance.end_date < result_item["cash_date"]
                    ) or (
                        self.instance.end_date > result_item["accounting_date"]
                        and self.instance.end_date > result_item["cash_date"]
                    ):
                        result_item["entry_account"] = result_item["account_cash_id"]
                        result_item["entry_strategy"] = result_item["strategy1_cash_id"]
                        result_item["entry_currency"] = result_item["settlement_currency_id"]
                        result_item["entry_amount"] = result_item["cash_consideration"]
                        result_item["entry_item_type"] = ITEM_TYPE_CURRENCY
                        result_item["entry_item_type_name"] = "Currency"

                        results.append(result_item)

                    elif result_item["accounting_date"] < result_item["cash_date"]:
                        result_item["entry_account"] = result_item["account_interim_id"]
                        result_item["entry_strategy"] = result_item["strategy1_cash_id"]
                        result_item["entry_currency"] = result_item["settlement_currency_id"]
                        result_item["entry_amount"] = result_item["cash_consideration"]
                        result_item["entry_item_type"] = ITEM_TYPE_CURRENCY
                        result_item["entry_item_type_name"] = "Currency"

                        results.append(result_item)

                    else:
                        result_item["entry_account"] = result_item["account_cash_id"]
                        result_item["entry_strategy"] = result_item["strategy1_cash_id"]
                        result_item["entry_currency"] = result_item["settlement_currency_id"]
                        result_item["entry_amount"] = result_item["cash_consideration"]
                        result_item["entry_item_type"] = ITEM_TYPE_CURRENCY
                        result_item["entry_item_type_name"] = "Currency"

                        results.append(result_item)

                # szhitenev: PLAT-172 / REQ-283
                # probably we need cash date instead of accounting_date?
                elif (
                    result_item["transaction_class_id"] == TransactionClass.INITIAL_POSITION
                    and self.instance.end_date == result_item["accounting_date"]
                ):
                    if result_item["account_position_id"]:
                        entry1["id"] = str(result_item["id"]) + "_1"

                        entry1["entry_account"] = result_item["account_position_id"]
                        entry1["entry_strategy"] = result_item["strategy1_position_id"]
                        entry1["entry_instrument"] = result_item["instrument_id"]
                        entry1["entry_amount"] = result_item["position_size_with_sign"]
                        entry1["entry_item_type"] = ITEM_TYPE_INSTRUMENT
                        entry1["entry_item_type_name"] = "Instrument"

                        results.append(entry1)

                    if result_item["account_cash_id"]:
                        entry2["id"] = str(result_item["id"]) + "_2"

                        entry2["entry_account"] = result_item["account_cash_id"]
                        entry2["entry_strategy"] = result_item["strategy1_cash_id"]
                        entry2["entry_currency"] = result_item["settlement_currency_id"]
                        entry2["entry_amount"] = result_item["cash_consideration"]
                        entry2["entry_item_type"] = ITEM_TYPE_CURRENCY
                        entry2["entry_item_type_name"] = "Currency"

                        results.append(entry2)

                # szhitenev: PLAT-172 / REQ-283
                # probably we need cash date instead of accounting_date?
                elif (
                    (
                        result_item["transaction_class_id"] == TransactionClass.INITIAL_CASH
                        and self.instance.end_date == result_item["accounting_date"]
                    )
                    or result_item["transaction_class_id"] == TransactionClass.INSTRUMENT_PL
                    or result_item["transaction_class_id"] == TransactionClass.TRANSACTION_PL
                ):
                    result_item["entry_account"] = result_item["account_cash_id"]
                    result_item["entry_strategy"] = result_item["strategy1_cash_id"]
                    result_item["entry_currency"] = result_item["settlement_currency_id"]
                    result_item["entry_amount"] = result_item["cash_consideration"]
                    result_item["entry_item_type"] = ITEM_TYPE_CURRENCY
                    result_item["entry_item_type_name"] = "Currency"

                    results.append(result_item)

                elif (
                    result_item["transaction_class_id"] == TransactionClass.BUY
                    or result_item["transaction_class_id"] == TransactionClass.SELL
                ):
                    entry1 = result_item.copy()
                    entry2 = result_item.copy()

                    if (
                        self.instance.end_date < result_item["accounting_date"]
                        and self.instance.end_date < result_item["cash_date"]
                    ) or (
                        self.instance.end_date > result_item["accounting_date"]
                        and self.instance.end_date > result_item["cash_date"]
                    ):
                        if result_item["account_position_id"]:
                            entry1["id"] = str(result_item["id"]) + "_1"

                            entry1["entry_account"] = result_item["account_position_id"]
                            entry1["entry_strategy"] = result_item["strategy1_position_id"]
                            entry1["entry_instrument"] = result_item["instrument_id"]
                            entry1["entry_amount"] = result_item["position_size_with_sign"]
                            entry1["entry_item_type"] = ITEM_TYPE_INSTRUMENT
                            entry1["entry_item_type_name"] = "Instrument"

                            results.append(entry1)

                        if result_item["account_cash_id"]:
                            entry2["id"] = str(result_item["id"]) + "_2"

                            entry2["entry_account"] = result_item["account_cash_id"]
                            entry2["entry_strategy"] = result_item["strategy1_cash_id"]
                            entry2["entry_currency"] = result_item["settlement_currency_id"]
                            entry2["entry_amount"] = result_item["cash_consideration"]
                            entry2["entry_item_type"] = ITEM_TYPE_CURRENCY
                            entry2["entry_item_type_name"] = "Currency"

                            results.append(entry2)

                    elif result_item["accounting_date"] < result_item["cash_date"]:
                        if result_item["account_position_id"]:
                            entry1["id"] = str(result_item["id"]) + "_1"

                            entry1["entry_account"] = result_item["account_position_id"]
                            entry1["entry_strategy"] = result_item["strategy1_position_id"]
                            entry1["entry_instrument"] = result_item["instrument_id"]
                            entry1["entry_amount"] = result_item["position_size_with_sign"]
                            entry1["entry_item_type"] = ITEM_TYPE_INSTRUMENT
                            entry1["entry_item_type_name"] = "Instrument"

                            results.append(entry1)

                        if result_item["account_cash_id"]:
                            entry2["id"] = str(result_item["id"]) + "_2"

                            entry2["entry_account"] = result_item["account_interim_id"]  # IMPORTANT
                            entry2["entry_strategy"] = result_item["strategy1_cash_id"]
                            entry2["entry_currency"] = result_item["settlement_currency_id"]
                            entry2["entry_amount"] = result_item["cash_consideration"]
                            entry2["entry_item_type"] = ITEM_TYPE_CURRENCY
                            entry2["entry_item_type_name"] = "Currency"

                            results.append(entry2)

                    else:
                        if result_item["account_position_id"]:
                            entry1["id"] = str(result_item["id"]) + "_1"

                            entry1["entry_account"] = result_item["account_interim_id"]
                            entry1["entry_strategy"] = result_item["strategy1_position_id"]
                            entry1["entry_instrument"] = result_item["instrument_id"]
                            entry1["entry_amount"] = result_item["cash_consideration"] * -1  # IMPORTANT
                            entry1["entry_item_type"] = ITEM_TYPE_INSTRUMENT
                            entry1["entry_item_type_name"] = "Instrument"

                            results.append(entry1)

                        if result_item["account_cash_id"]:
                            entry2["id"] = str(result_item["id"]) + "_2"

                            entry2["entry_account"] = result_item["account_cash_id"]
                            entry2["entry_strategy"] = result_item["strategy1_cash_id"]
                            entry2["entry_currency"] = result_item["settlement_currency_id"]
                            entry2["entry_amount"] = result_item["cash_consideration"]
                            entry2["entry_item_type"] = ITEM_TYPE_CURRENCY
                            entry2["entry_item_type_name"] = "Currency"

                            results.append(entry2)

                elif result_item["transaction_class_id"] == TransactionClass.FX_TRADE:
                    entry1 = result_item.copy()
                    entry2 = result_item.copy()

                    if (
                        self.instance.end_date < result_item["accounting_date"]
                        and self.instance.end_date < result_item["cash_date"]
                    ) or (
                        self.instance.end_date > result_item["accounting_date"]
                        and self.instance.end_date > result_item["cash_date"]
                    ):
                        if result_item["account_position_id"]:
                            entry1["id"] = str(result_item["id"]) + "_1"

                            entry1["entry_account"] = result_item["account_position_id"]
                            entry1["entry_strategy"] = result_item["strategy1_cash_id"]
                            entry1["entry_currency"] = result_item["transaction_currency_id"]
                            entry1["entry_amount"] = result_item["position_size_with_sign"]
                            entry1["entry_item_type"] = ITEM_TYPE_CURRENCY
                            entry1["entry_item_type_name"] = "Currency"

                            results.append(entry1)

                        if result_item["account_cash_id"]:
                            entry2["id"] = str(result_item["id"]) + "_2"

                            entry2["entry_account"] = result_item["account_cash_id"]
                            entry2["entry_strategy"] = result_item["strategy1_cash_id"]
                            entry2["entry_currency"] = result_item["settlement_currency_id"]
                            entry2["entry_amount"] = result_item["cash_consideration"]
                            entry2["entry_item_type"] = ITEM_TYPE_CURRENCY
                            entry2["entry_item_type_name"] = "Currency"

                            results.append(entry2)

                    elif result_item["accounting_date"] < result_item["cash_date"]:
                        if result_item["account_position_id"]:
                            entry1["id"] = str(result_item["id"]) + "_1"

                            entry1["entry_account"] = result_item["account_position_id"]
                            entry1["entry_strategy"] = result_item["strategy1_cash_id"]
                            entry1["entry_currency"] = result_item["transaction_currency_id"]
                            entry1["entry_amount"] = result_item["position_size_with_sign"]
                            entry1["entry_item_type"] = ITEM_TYPE_CURRENCY
                            entry1["entry_item_type_name"] = "Currency"

                            results.append(entry1)

                        if result_item["account_cash_id"]:
                            entry2["id"] = str(result_item["id"]) + "_2"

                            entry2["entry_account"] = result_item["account_interim_id"]  # IMPORTANT
                            entry2["entry_strategy"] = result_item["strategy1_cash_id"]
                            entry2["entry_currency"] = result_item["settlement_currency_id"]
                            entry2["entry_amount"] = result_item["cash_consideration"]
                            entry2["entry_item_type"] = ITEM_TYPE_CURRENCY
                            entry2["entry_item_type_name"] = "Currency"

                            results.append(entry2)

                    else:
                        if result_item["account_position_id"]:
                            entry1["id"] = str(result_item["id"]) + "_1"

                            entry1["entry_account"] = result_item["account_interim_id"]
                            entry1["entry_strategy"] = result_item["strategy1_cash_id"]
                            entry1["entry_currency"] = result_item["transaction_currency_id"]
                            entry1["entry_amount"] = result_item["cash_consideration"] * -1  # IMPORTANT
                            entry1["entry_item_type"] = ITEM_TYPE_CURRENCY
                            entry1["entry_item_type_name"] = "Currency"

                            results.append(entry1)

                        if result_item["account_cash_id"]:
                            entry2["id"] = str(result_item["id"]) + "_2"

                            entry2["entry_account"] = result_item["account_cash_id"]
                            entry2["entry_strategy"] = result_item["strategy1_cash_id"]
                            entry2["entry_currency"] = result_item["settlement_currency_id"]
                            entry2["entry_amount"] = result_item["cash_consideration"]
                            entry2["entry_item_type"] = ITEM_TYPE_CURRENCY
                            entry2["entry_item_type_name"] = "Currency"

                            results.append(entry2)

                elif result_item["transaction_class_id"] == TransactionClass.FX_TRANSFER:
                    entry1 = result_item.copy()
                    entry2 = result_item.copy()

                    if (
                        self.instance.end_date < result_item["accounting_date"]
                        and self.instance.end_date < result_item["cash_date"]
                    ) or (
                        self.instance.end_date > result_item["accounting_date"]
                        and self.instance.end_date > result_item["cash_date"]
                    ):
                        if result_item["account_position_id"]:  # from
                            entry1["id"] = str(result_item["id"]) + "_1"

                            entry1["entry_account"] = result_item["account_position_id"]
                            entry1["entry_strategy"] = result_item["strategy1_cash_id"]
                            entry1["entry_currency"] = result_item["settlement_currency_id"]
                            entry1["entry_amount"] = result_item["cash_consideration"] * -1  # Important see FN-1077
                            entry1["entry_item_type"] = ITEM_TYPE_CURRENCY
                            entry1["entry_item_type_name"] = "Currency"

                            results.append(entry1)

                        if result_item["account_cash_id"]:  # to
                            entry2["id"] = str(result_item["id"]) + "_2"

                            entry2["entry_account"] = result_item["account_cash_id"]
                            entry2["entry_strategy"] = result_item["strategy1_position_id"]
                            entry2["entry_currency"] = result_item["settlement_currency_id"]
                            entry2["entry_amount"] = result_item["cash_consideration"]
                            entry2["entry_item_type"] = ITEM_TYPE_CURRENCY
                            entry2["entry_item_type_name"] = "Currency"

                            results.append(entry2)

                    elif result_item["accounting_date"] < result_item["cash_date"]:
                        if result_item["account_position_id"]:  # from
                            entry1["id"] = str(result_item["id"]) + "_1"

                            entry1["entry_account"] = result_item["account_position_id"]
                            entry1["entry_strategy"] = result_item["strategy1_cash_id"]
                            entry1["entry_currency"] = result_item["settlement_currency_id"]
                            entry1["entry_amount"] = result_item["cash_consideration"] * -1  # Important see FN-1077
                            entry1["entry_item_type"] = ITEM_TYPE_CURRENCY
                            entry1["entry_item_type_name"] = "Currency"

                            results.append(entry1)

                        if result_item["account_cash_id"]:  # to
                            entry2["id"] = str(result_item["id"]) + "_2"

                            entry2["entry_account"] = result_item["account_interim_id"]  # IMPORTANT
                            entry2["entry_strategy"] = result_item["strategy1_position_id"]
                            entry2["entry_currency"] = result_item["settlement_currency_id"]
                            entry2["entry_amount"] = result_item["cash_consideration"]
                            entry2["entry_item_type"] = ITEM_TYPE_CURRENCY
                            entry2["entry_item_type_name"] = "Currency"

                            results.append(entry2)

                    else:
                        if result_item["account_position_id"]:  # from
                            entry1["id"] = str(result_item["id"]) + "_1"

                            entry1["entry_account"] = result_item["account_interim_id"]
                            entry1["entry_strategy"] = result_item["strategy1_cash_id"]
                            entry1["entry_currency"] = result_item["settlement_currency_id"]
                            entry1["entry_amount"] = result_item["cash_consideration"] * -1  # Important see FN-1077
                            entry1["entry_item_type"] = ITEM_TYPE_CURRENCY
                            entry1["entry_item_type_name"] = "Currency"

                            results.append(entry1)

                        if result_item["account_cash_id"]:  # to
                            entry2["id"] = str(result_item["id"]) + "_2"

                            entry2["entry_account"] = result_item["account_cash_id"]
                            entry2["entry_strategy"] = result_item["strategy1_position_id"]
                            entry2["entry_currency"] = result_item["settlement_currency_id"]
                            entry2["entry_amount"] = result_item["cash_consideration"]
                            entry2["entry_item_type"] = ITEM_TYPE_CURRENCY
                            entry2["entry_item_type_name"] = "Currency"

                            results.append(entry2)

                elif result_item["transaction_class_id"] == TransactionClass.TRANSFER:
                    entry1 = result_item.copy()
                    entry2 = result_item.copy()

                    if (
                        self.instance.end_date < result_item["accounting_date"]
                        and self.instance.end_date < result_item["cash_date"]
                    ) or (
                        self.instance.end_date > result_item["accounting_date"]
                        and self.instance.end_date > result_item["cash_date"]
                    ):
                        if result_item["account_position_id"]:  # to
                            entry2["id"] = str(result_item["id"]) + "_2"

                            entry2["entry_account"] = result_item["account_position_id"]
                            entry2["entry_strategy"] = result_item["strategy1_cash_id"]
                            entry2["entry_currency"] = result_item["settlement_currency_id"]
                            entry2["entry_amount"] = result_item["position_size_with_sign"]
                            entry2["entry_item_type"] = ITEM_TYPE_INSTRUMENT
                            entry2["entry_item_type_name"] = "Instrument"

                            results.append(entry2)

                        if result_item["account_cash_id"]:  # from
                            entry1["id"] = str(result_item["id"]) + "_1"

                            entry1["entry_account"] = result_item["account_position_id"]
                            entry1["entry_strategy"] = result_item["strategy1_position_id"]
                            entry1["entry_instrument"] = result_item["instrument_id"]
                            entry1["entry_amount"] = (
                                result_item["position_size_with_sign"] * -1
                            )  # Important see FN-1077
                            entry1["entry_item_type"] = ITEM_TYPE_INSTRUMENT
                            entry1["entry_item_type_name"] = "Instrument"

                            results.append(entry1)

                    elif result_item["accounting_date"] < result_item["cash_date"]:
                        if result_item["account_position_id"]:  # to
                            entry2["id"] = str(result_item["id"]) + "_2"

                            entry2["entry_account"] = result_item["account_position_id"]  # Important
                            entry2["entry_strategy"] = result_item["strategy1_cash_id"]
                            entry2["entry_currency"] = result_item["settlement_currency_id"]
                            entry2["entry_amount"] = result_item["position_size_with_sign"]
                            entry2["entry_item_type"] = ITEM_TYPE_INSTRUMENT
                            entry2["entry_item_type_name"] = "Instrument"

                            results.append(entry2)

                        if result_item["account_cash_id"]:  # from
                            entry1["id"] = str(result_item["id"]) + "_2"

                            entry1["entry_account"] = result_item["account_interim_id"]
                            entry1["entry_strategy"] = result_item["strategy1_position_id"]
                            entry1["entry_instrument"] = result_item["instrument_id"]
                            entry1["entry_amount"] = (
                                result_item["position_size_with_sign"] * -1
                            )  # Important see FN-1077
                            entry1["entry_item_type"] = ITEM_TYPE_INSTRUMENT
                            entry1["entry_item_type_name"] = "Instrument"

                            results.append(entry1)

                    else:
                        if result_item["account_position_id"]:  # to
                            entry2["id"] = str(result_item["id"]) + "_2"

                            entry2["entry_account"] = result_item["account_interim_id"]
                            entry2["entry_strategy"] = result_item["strategy1_cash_id"]
                            entry2["entry_currency"] = result_item["settlement_currency_id"]
                            entry2["entry_amount"] = result_item["cash_consideration"] * -1
                            entry2["entry_item_type"] = ITEM_TYPE_INSTRUMENT
                            entry2["entry_item_type_name"] = "Instrument"

                            results.append(entry2)

                        if result_item["account_cash_id"]:  # from
                            entry1["id"] = str(result_item["id"]) + "_1"

                            entry1["entry_account"] = result_item["account_position_id"]
                            entry1["entry_strategy"] = result_item["strategy1_position_id"]
                            entry1["entry_instrument"] = result_item["instrument_id"]
                            entry1["entry_amount"] = (
                                result_item["position_size_with_sign"] * -1
                            )  # Important see FN-1077
                            entry1["entry_item_type"] = ITEM_TYPE_INSTRUMENT
                            entry1["entry_item_type_name"] = "Instrument"

                            results.append(entry1)

                else:
                    results.append(result_item)

            # test_results = []
            #
            # for i in range(1, 100):
            #
            #     test_results = test_results + results

            # self.instance.items = test_results # only test purpose
            self.instance.items = results

    def build_items(self):
        _l.debug("TransactionReportBuilderSql.build_items: depth_level %s", self.instance.depth_level)

        if self.instance.depth_level == "complex_transaction":
            self.build_complex_transaction_level_items()

        if self.instance.depth_level == "base_transaction":
            self.build_base_transaction_level_items()

        if self.instance.depth_level == "entry":
            self.build_entry_level_items()

    def add_data_items_instruments(self, ids):
        self.instance.item_instruments = (
            Instrument.objects.select_related(
                "instrument_type",
                "instrument_type__instrument_class",
                "pricing_currency",
                "accrued_currency",
                "payment_size_detail",
                "daily_pricing_model",
                "country",
                "owner",
                # 'price_download_scheme',
                # 'price_download_scheme__provider',
            )
            .prefetch_related(
                "attributes",
                "attributes__attribute_type",
                "attributes__classifier",
            )
            .filter(master_user=self.instance.master_user)
            .filter(id__in=ids)
        )

    def add_data_items_instrument_types(self, instruments):
        ids = []

        for instrument in instruments:
            ids.append(instrument.instrument_type_id)

        self.instance.item_instrument_types = (
            InstrumentType.objects.select_related("owner")
            .prefetch_related(
                "attributes",
                "attributes__attribute_type",
                "attributes__classifier",
            )
            .filter(master_user=self.instance.master_user)
            .filter(id__in=ids)
        )

    def add_data_items_countries(self, instruments):
        ids = []

        for instrument in instruments:
            ids.append(instrument.country_id)

        self.instance.item_countries = Country.objects.all()

    def add_data_items_account_types(self, accounts):
        ids = []

        for account in accounts:
            ids.append(account.type_id)

        self.instance.item_account_types = (
            AccountType.objects.select_related("owner")
            .prefetch_related(
                "attributes",
                "attributes__attribute_type",
                "attributes__classifier",
            )
            .filter(master_user=self.instance.master_user)
            .filter(id__in=ids)
        )

    def add_data_items_portfolios(self, ids):
        self.instance.item_portfolios = (
            Portfolio.objects.select_related("owner")
            .prefetch_related(
                "attributes",
                "attributes__attribute_type",
                "attributes__classifier",
            )
            .defer("responsibles", "counterparties", "transaction_types", "accounts")
            .filter(master_user=self.instance.master_user)
            .filter(id__in=ids)
        )

    def add_data_items_accounts(self, ids):
        self.instance.item_accounts = (
            Account.objects.select_related("type", "owner")
            .prefetch_related(
                "attributes",
                "attributes__attribute_type",
                "attributes__classifier",
            )
            .filter(master_user=self.instance.master_user)
            .filter(id__in=ids)
        )

    def add_data_items_currencies(self, ids):
        self.instance.item_currencies = (
            Currency.objects.select_related("country", "owner")
            .prefetch_related(
                "attributes",
                "attributes__attribute_type",
                "attributes__classifier",
            )
            .filter(master_user=self.instance.master_user)
            .filter(id__in=ids)
        )

    def add_data_items_counterparties(self, ids):
        self.instance.item_counterparties = (
            Counterparty.objects.select_related("owner")
            .prefetch_related(
                "attributes",
                "attributes__attribute_type",
                "attributes__classifier",
            )
            .filter(master_user=self.instance.master_user)
            .filter(id__in=ids)
        )

    def add_data_items_responsibles(self, ids):
        self.instance.item_responsibles = (
            Responsible.objects.select_related("owner")
            .prefetch_related(
                "attributes",
                "attributes__attribute_type",
                "attributes__classifier",
            )
            .filter(master_user=self.instance.master_user)
            .filter(id__in=ids)
        )

    def add_data_items_strategies1(self, ids):
        self.instance.item_strategies1 = (
            Strategy1.objects.select_related("owner")
            .prefetch_related(
                "attributes",
                "attributes__attribute_type",
                "attributes__classifier",
            )
            .filter(master_user=self.instance.master_user)
            .filter(id__in=ids)
        )

    def add_data_items_strategies2(self, ids):
        self.instance.item_strategies2 = (
            Strategy2.objects.select_related("owner")
            .prefetch_related(
                "attributes",
                "attributes__attribute_type",
                "attributes__classifier",
            )
            .filter(master_user=self.instance.master_user)
            .filter(id__in=ids)
        )

    def add_data_items_strategies3(self, ids):
        self.instance.item_strategies3 = (
            Strategy3.objects.select_related("owner")
            .prefetch_related(
                "attributes",
                "attributes__attribute_type",
                "attributes__classifier",
            )
            .filter(master_user=self.instance.master_user)
            .filter(id__in=ids)
        )

    def add_data_items_complex_transactions(self, ids):
        self.instance.item_complex_transactions = (
            ComplexTransaction.objects.select_related("owner")
            .prefetch_related(
                "transaction_type",
                # 'transaction_type__group',
                "attributes",
                "attributes__attribute_type",
                "attributes__classifier",
            )
            .filter(master_user=self.instance.master_user)
            .filter(id__in=ids)
        )

    def add_data_items_transaction_classes(self):
        self.instance.item_transaction_classes = TransactionClass.objects.all()

    def add_data_items_complex_transaction_status(self):
        self.instance.item_complex_transaction_status = ComplexTransactionStatus.objects.all()

    def add_data_items(self):  # noqa: PLR0912, PLR0915
        instance_relations_st = time.perf_counter()

        _l.debug(
            "_refresh_with_perms_optimized instance relations done: %s",
            f"{time.perf_counter() - instance_relations_st:3.3f}",
        )

        permissions_st = time.perf_counter()

        _l.debug(
            "_refresh_with_perms_optimized permissions done: %s",
            f"{time.perf_counter() - permissions_st:3.3f}",
        )

        item_relations_st = time.perf_counter()

        instrument_ids = []
        portfolio_ids = []
        account_ids = []
        currencies_ids = []
        counterparty_ids = []
        responsibles_ids = []
        strategies1_ids = []
        strategies2_ids = []
        strategies3_ids = []

        complex_transactions_ids = []

        for item in self.instance.items:
            portfolio_ids.append(item["portfolio_id"])

            instrument_ids.append(item["instrument_id"])
            instrument_ids.append(item["allocation_balance_id"])
            instrument_ids.append(item["allocation_pl_id"])
            instrument_ids.append(item["linked_instrument_id"])

            account_ids.append(item["account_position_id"])
            account_ids.append(item["account_cash_id"])

            currencies_ids.append(item["settlement_currency_id"])
            currencies_ids.append(item["transaction_currency_id"])
            counterparty_ids.append(item["counterparty_id"])
            responsibles_ids.append(item["responsible_id"])

            if "entry_strategy" in item:
                strategies1_ids.append(item["entry_strategy"])

            if "strategy1_position_id" in item:
                strategies1_ids.append(item["strategy1_position_id"])

            if "strategy2_position_id" in item:
                strategies2_ids.append(item["strategy2_position_id"])

            if "strategy3_position_id" in item:
                strategies3_ids.append(item["strategy3_position_id"])

            if "strategy1_cash_id" in item:
                strategies1_ids.append(item["strategy1_cash_id"])

            if "strategy2_cash_id" in item:
                strategies2_ids.append(item["strategy2_cash_id"])

            if "strategy3_cash_id" in item:
                strategies3_ids.append(item["strategy3_cash_id"])

            # if item['complex_transaction_id'] not in complex_transactions_ids:
            #     complex_transactions_ids.append(item['complex_transaction_id'])

        self.add_data_items_instruments(instrument_ids)
        self.add_data_items_portfolios(portfolio_ids)
        self.add_data_items_accounts(account_ids)
        self.add_data_items_currencies(currencies_ids)
        self.add_data_items_counterparties(counterparty_ids)
        self.add_data_items_responsibles(responsibles_ids)
        self.add_data_items_strategies1(strategies1_ids)
        self.add_data_items_strategies2(strategies2_ids)
        self.add_data_items_strategies3(strategies3_ids)
        self.add_data_items_transaction_classes()
        self.add_data_items_complex_transaction_status()
        # self.add_data_items_complex_transactions(complex_transactions_ids)  # too slow

        self.instance.item_instrument_types = []
        self.instance.item_account_types = []

        self.add_data_items_instrument_types(self.instance.item_instruments)
        self.add_data_items_countries(self.instance.item_instruments)
        self.add_data_items_account_types(self.instance.item_accounts)

        if self.instance.depth_level == "entry":
            for item in self.instance.items:
                if item["entry_currency"]:
                    for currency in self.instance.item_currencies:
                        if item["entry_currency"] == currency.id:
                            item["entry_item_short_name"] = currency.short_name
                            item["entry_item_user_code"] = currency.user_code
                            item["entry_item_name"] = currency.name
                            item["entry_item_public_name"] = currency.public_name

                if item["entry_instrument"]:
                    for instrument in self.instance.item_instruments:
                        if item["entry_instrument"] == instrument.id:
                            item["entry_item_short_name"] = instrument.short_name
                            item["entry_item_user_code"] = instrument.user_code
                            item["entry_item_name"] = instrument.name
                            item["entry_item_public_name"] = instrument.public_name

        self.instance.custom_fields = TransactionReportCustomField.objects.filter(
            master_user=self.instance.master_user
        )

        _l.debug(
            "_refresh_with_perms_optimized item relations done: %s",
            f"{time.perf_counter() - item_relations_st:3.3f}",
        )
