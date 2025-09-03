from poms.currencies.models import CurrencyHistory
from poms.reports.common import Report


def dictfetchall(cursor):
    "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row, strict=False)) for row in cursor.fetchall()]


def get_transaction_date_filter_for_initial_position_sql_string(date, has_where):
    result_string = ""

    if has_where:
        result_string = "and "
    else:
        result_string = "where "

    result_string = f"{result_string}((transaction_class_id IN (14,15) and min_date = '{date}') or (transaction_class_id NOT IN (14,15)))"

    return result_string


def get_transaction_filter_sql_string(instance):
    result_string = ""

    filter_sql_list = []

    portfolios_ids = []
    accounts_ids = []
    strategies1_ids = []
    strategies2_ids = []
    strategies3_ids = []

    if len(instance.portfolios):
        for portfolio in instance.portfolios:
            portfolios_ids.append(str(portfolio.id))

        filter_sql_list.append("portfolio_id in (" + ", ".join(portfolios_ids) + ")")

    if len(instance.accounts):
        for account in instance.accounts:
            accounts_ids.append(str(account.id))

        filter_sql_list.append("account_position_id in (" + ", ".join(accounts_ids) + ")")

    if len(instance.strategies1):
        for strategy in instance.strategies1:
            strategies1_ids.append(str(strategy.id))

        filter_sql_list.append("strategy1_position_id in (" + ", ".join(strategies1_ids) + ")")

    if len(instance.strategies2):
        for strategy in instance.strategies2:
            strategies2_ids.append(str(strategy.id))

        filter_sql_list.append("strategy2_position_id in (" + ", ".join(strategies2_ids) + ")")

    if len(instance.strategies3):
        for strategy in instance.strategies3:
            strategies3_ids.append(str(strategy.id))

        filter_sql_list.append("strategy3_position_id in (" + ", ".join(strategies3_ids) + ")")

    if filter_sql_list:
        result_string = result_string + "where "
        result_string = result_string + " and ".join(filter_sql_list)

    return result_string


def get_report_fx_rate(instance, date):
    report_fx_rate = 1

    try:
        item = CurrencyHistory.objects.get(
            currency_id=instance.report_currency.id,
            date=date,
            pricing_policy_id=instance.pricing_policy.id,
        )
        report_fx_rate = item.fx_rate
    except CurrencyHistory.DoesNotExist:
        report_fx_rate = 1

    report_fx_rate = str(report_fx_rate)

    return report_fx_rate


def get_fx_trades_and_fx_variations_transaction_filter_sql_string(instance):
    result_string = ""

    filter_sql_list = []

    portfolios_ids = []
    accounts_ids = []
    strategies1_ids = []
    strategies2_ids = []
    strategies3_ids = []

    if len(instance.portfolios):
        for portfolio in instance.portfolios:
            portfolios_ids.append(str(portfolio.id))

        filter_sql_list.append("portfolio_id in (" + ", ".join(portfolios_ids) + ")")

    if len(instance.accounts):
        for account in instance.accounts:
            accounts_ids.append(str(account.id))

        filter_sql_list.append("account_position_id in (" + ", ".join(accounts_ids) + ")")

    if len(instance.strategies1):
        for strategy in instance.strategies1:
            strategies1_ids.append(str(strategy.id))

        filter_sql_list.append("strategy1_position_id in (" + ", ".join(strategies1_ids) + ")")

    if len(instance.strategies2):
        for strategy in instance.strategies2:
            strategies2_ids.append(str(strategy.id))

        filter_sql_list.append("strategy2_position_id in (" + ", ".join(strategies2_ids) + ")")

    if len(instance.strategies3):
        for strategy in instance.strategies3:
            strategies3_ids.append(str(strategy.id))

        filter_sql_list.append("strategy3_position_id in (" + ", ".join(strategies3_ids) + ")")

    if filter_sql_list:
        result_string = result_string + " and "
        result_string = result_string + " and ".join(filter_sql_list)

    return result_string


def get_where_expression_for_position_consolidation(instance, prefix, prefix_second, use_allocation=True):
    result = []

    if instance.portfolio_mode == Report.MODE_INDEPENDENT:
        result.append(prefix + "portfolio_id = " + prefix_second + "portfolio_id")

    if instance.account_mode == Report.MODE_INDEPENDENT:
        result.append(prefix + "account_position_id = " + prefix_second + "account_position_id")

    if instance.strategy1_mode == Report.MODE_INDEPENDENT:
        result.append(prefix + "strategy1_position_id = " + prefix_second + "strategy1_position_id")

    if instance.strategy2_mode == Report.MODE_INDEPENDENT:
        result.append(prefix + "strategy2_position_id = " + prefix_second + "strategy2_position_id")

    if instance.strategy3_mode == Report.MODE_INDEPENDENT:
        result.append(prefix + "strategy3_position_id = " + prefix_second + "strategy3_position_id")

    if instance.allocation_mode == Report.MODE_INDEPENDENT:
        result.append(prefix + "allocation_pl_id = " + prefix_second + "allocation_pl_id")

    resultString = ""

    if result:
        resultString = " and ".join(result) + " and "

    return resultString


def get_position_consolidation_for_select(instance, prefix=""):
    result = []

    if instance.portfolio_mode == Report.MODE_INDEPENDENT:
        result.append(prefix + "portfolio_id")

    if instance.account_mode == Report.MODE_INDEPENDENT:
        result.append(prefix + "account_position_id")

    if instance.strategy1_mode == Report.MODE_INDEPENDENT:
        result.append(prefix + "strategy1_position_id")

    if instance.strategy2_mode == Report.MODE_INDEPENDENT:
        result.append(prefix + "strategy2_position_id")

    if instance.strategy3_mode == Report.MODE_INDEPENDENT:
        result.append(prefix + "strategy3_position_id")

    if instance.allocation_mode == Report.MODE_INDEPENDENT:
        result.append(prefix + "allocation_pl_id")

    resultString = ""

    if result:
        resultString = ", ".join(result) + ", "

    return resultString


def get_pl_left_join_consolidation(instance):
    result = []

    if instance.portfolio_mode == Report.MODE_INDEPENDENT:
        result.append("balance_q.portfolio_id = pl_q.portfolio_id")

    if instance.account_mode == Report.MODE_INDEPENDENT:
        result.append("balance_q.account_position_id = pl_q.account_position_id")

    if instance.strategy1_mode == Report.MODE_INDEPENDENT:
        result.append("balance_q.strategy1_position_id = pl_q.strategy1_position_id")

    if instance.strategy2_mode == Report.MODE_INDEPENDENT:
        result.append("balance_q.strategy2_position_id = pl_q.strategy2_position_id")

    if instance.strategy3_mode == Report.MODE_INDEPENDENT:
        result.append("balance_q.strategy3_position_id = pl_q.strategy3_position_id")

    if instance.allocation_mode == Report.MODE_INDEPENDENT:
        result.append("balance_q.allocation_pl_id = pl_q.allocation_pl_id")

    resultString = ""

    if result:
        resultString = resultString + "and "
        resultString = resultString + " and ".join(result)

    return resultString


def get_cash_consolidation_for_select(instance):
    result = []

    if instance.portfolio_mode == Report.MODE_INDEPENDENT:
        result.append("portfolio_id")

    if instance.account_mode == Report.MODE_INDEPENDENT:
        result.append("account_cash_id")

    if instance.strategy1_mode == Report.MODE_INDEPENDENT:
        result.append("strategy1_cash_id")

    if instance.strategy2_mode == Report.MODE_INDEPENDENT:
        result.append("strategy2_cash_id")

    if instance.strategy3_mode == Report.MODE_INDEPENDENT:
        result.append("strategy3_cash_id")

    if instance.allocation_mode == Report.MODE_INDEPENDENT:
        result.append("allocation_pl_id")

    resultString = ""

    if result:
        resultString = ", ".join(result) + ", "

    return resultString


def get_cash_as_position_consolidation_for_select(instance):
    result = []

    if instance.portfolio_mode == Report.MODE_INDEPENDENT:
        result.append("portfolio_id as portfolio_id")

    if instance.account_mode == Report.MODE_INDEPENDENT:
        result.append("account_cash_id as account_position_id ")

    if instance.strategy1_mode == Report.MODE_INDEPENDENT:
        result.append("strategy1_cash_id as strategy1_position_id")

    if instance.strategy2_mode == Report.MODE_INDEPENDENT:
        result.append("strategy2_cash_id as strategy2_position_id")

    if instance.strategy3_mode == Report.MODE_INDEPENDENT:
        result.append("strategy3_cash_id as strategy3_position_id")

    if instance.allocation_mode == Report.MODE_INDEPENDENT:
        result.append("allocation_pl_id as allocation_pl_id")

    resultString = ""

    if result:
        resultString = ", ".join(result) + ", "

    return resultString


def get_transaction_report_filter_sql_string(instance):
    result_string = ""

    filter_sql_list = []

    portfolios_ids = []
    accounts_ids = []
    strategies1_ids = []
    strategies2_ids = []
    strategies3_ids = []

    if len(instance.portfolios):
        for portfolio in instance.portfolios:
            portfolios_ids.append(str(portfolio.id))

        filter_sql_list.append("t.portfolio_id in (" + ", ".join(portfolios_ids) + ")")

    if len(instance.accounts):
        for account in instance.accounts:
            accounts_ids.append(str(account.id))

        filter_sql_list.append("t.account_position_id in (" + ", ".join(accounts_ids) + ")")

    if len(instance.strategies1):
        for strategy in instance.strategies1:
            strategies1_ids.append(str(strategy.id))

        filter_sql_list.append("t.strategy1_position_id in (" + ", ".join(strategies1_ids) + ")")

    if len(instance.strategies2):
        for strategy in instance.strategies2:
            strategies2_ids.append(str(strategy.id))

        filter_sql_list.append("t.strategy2_position_id in (" + ", ".join(strategies2_ids) + ")")

    if len(instance.strategies3):
        for strategy in instance.strategies3:
            strategies3_ids.append(str(strategy.id))

        filter_sql_list.append("t.strategy3_position_id in (" + ", ".join(strategies3_ids) + ")")

    if filter_sql_list:
        result_string = result_string + "and "
        result_string = result_string + " and ".join(filter_sql_list)

    return result_string


def get_transaction_report_date_filter_sql_string(instance):
    result_string = ""

    if (
        "user_" in instance.date_field or instance.date_field == "date"
    ):  # for complex transaction.user_date_N fields (note tc.)
        result_string = (
            "((t.transaction_class_id IN (14,15) AND tc."
            + instance.date_field
            + " = '"
            + str(instance.end_date)
            + "') OR (t.transaction_class_id NOT IN (14,15) AND tc."
            + instance.date_field
            + " >= '"
            + str(instance.begin_date)
            + "' AND tc."
            + instance.date_field
            + "<= '"
            + str(instance.end_date)
            + "'))"
        )

    else:  # for base transaction fields (note t.)
        result_string = (
            "((t.transaction_class_id IN (14,15) AND t."
            + instance.date_field
            + " = '"
            + str(instance.end_date)
            + "') OR (t.transaction_class_id NOT IN (14,15) AND t."
            + instance.date_field
            + " >= '"
            + str(instance.begin_date)
            + "' AND t."
            + instance.date_field
            + " <= '"
            + str(instance.end_date)
            + "'))"
        )

    return result_string


def get_balance_query_with_pl():
    # language=PostgreSQL
    query = """
                    
                    with unioned_transactions_for_balance as (
                        
                        select 
                            id,
                            master_user_id,
                        
                            instrument_id,
                            portfolio_id,
                            transaction_class_id,
                            
                            transaction_date,
                            accounting_date,
                            cash_date,
                            
                            account_cash_id,
                            account_position_id,
                            account_interim_id,
                            
                            transaction_currency_id,
                            settlement_currency_id,
                            
                            position_size_with_sign,
                            cash_consideration,
                            
                            strategy1_cash_id,
                            strategy2_cash_id,
                            strategy3_cash_id,
                            
                            strategy1_position_id,
                            strategy2_position_id,
                            strategy3_position_id,
                            
                            allocation_balance_id,
                            allocation_pl_id
                            
                        from pl_transactions_with_ttype
                        
                        union all
                        
                        select 
                            id,
                            master_user_id,
                            
                            instrument_id,
                            portfolio_id,
                            transaction_class_id,
                            
                            transaction_date,
                            accounting_date,
                            cash_date,
                            
                            account_cash_id,
                            account_position_id,
                            account_interim_id,
                            
                            transaction_currency_id,
                            settlement_currency_id,
                            
                            (0) as position_size_with_sign,
                            cash_consideration,
                            
                            strategy1_cash_id,
                            strategy2_cash_id,
                            strategy3_cash_id,
                            
                            strategy1_position_id,
                            strategy2_position_id,
                            strategy3_position_id,
                            allocation_balance_id,
                            allocation_pl_id
                            
                        from pl_cash_fx_trades_transactions_with_ttype
                        
                        union all
                        
                        select 
                            id,
                            master_user_id,
                            
                            instrument_id,
                            portfolio_id,
                            transaction_class_id,
                            
                            transaction_date,
                            accounting_date,
                            cash_date,
                            
                            account_cash_id,
                            account_position_id,
                            account_interim_id,
                            
                            transaction_currency_id,
                            settlement_currency_id,
                            
                            position_size_with_sign,
                            cash_consideration,
                            
                            strategy1_cash_id,
                            strategy2_cash_id,
                            strategy3_cash_id,
                            
                            strategy1_position_id,
                            strategy2_position_id,
                            strategy3_position_id,
                            allocation_balance_id,
                            allocation_pl_id
                            
                            
                        from pl_cash_fx_variations_transactions_with_ttype
                        
                        union all
                        
                        select 
                            id,
                            master_user_id,
                            
                            instrument_id,
                            portfolio_id,
                            transaction_class_id,
                            
                            transaction_date,
                            accounting_date,
                            cash_date,
                            
                            account_cash_id,
                            account_position_id,
                            account_interim_id,
                            
                            transaction_currency_id,
                            settlement_currency_id,
                            
                            position_size_with_sign,
                            cash_consideration,
                            
                            strategy1_cash_id,
                            strategy2_cash_id,
                            strategy3_cash_id,
                            
                            strategy1_position_id,
                            strategy2_position_id,
                            strategy3_position_id,
                            
                            allocation_balance_id,
                            allocation_pl_id
                            
                        from pl_cash_transaction_pl_transactions_with_ttype
                      
                    ),
                    
                    unioned_interim_account_transactions as (
                        
                        select 
                               id,
                               master_user_id,
                               
                               instrument_id,
                               portfolio_id,
                               
                               transaction_class_id,
                  
                               strategy1_cash_id,
                               strategy2_cash_id,
                               strategy3_cash_id,
                               
                               
                               strategy1_position_id,
                               strategy2_position_id,
                               strategy3_position_id,
                               
                               position_size_with_sign,
                               /* не нужны для БАЛАНСА
                               principal_with_sign,
                               carry_with_sign,
                               overheads,
                                */
                               cash_consideration,
                               settlement_currency_id,
                               accounting_date,
                               cash_date,
                               account_position_id,
                               -- modification
                               account_interim_id as account_cash_id,
                               account_interim_id,
                               
                               case 
                                    when cash_date < accounting_date
                                    then cash_date
                                    else accounting_date
                               end
                               as min_date,
                               
                               allocation_balance_id,
                               allocation_pl_id
                               
                        -- добавить остальные поля
                        from unioned_transactions_for_balance -- USE TOTAL VIEW HERE
                        where accounting_date <= '{report_date}' /* REPORTING DATE */
                          and '{report_date}' < cash_date
                        
                        -- case 2
                        union all
                        select 
                                id,
                                master_user_id,
                        
                               instrument_id,
                               portfolio_id,
                               
                               transaction_class_id,
                               
                               strategy1_cash_id,
                               strategy2_cash_id,
                               strategy3_cash_id,
                               
                               strategy1_position_id,
                               strategy2_position_id,
                               strategy3_position_id,
                               
                               
                               -- modification
                               0 as position_size_with_sign,
                               (-cash_consideration) as cash_consideration,
                               settlement_currency_id,
                               accounting_date,
                               cash_date,
                               account_position_id,
                               -- modification
                               account_interim_id as account_cash_id,
                               account_interim_id,
                               
                               case 
                                    when cash_date < accounting_date
                                    then cash_date
                                    else accounting_date
                               end
                               as min_date,
                               allocation_balance_id,
                               allocation_pl_id
                               
                        from unioned_transactions_for_balance
                        where cash_date  <= '{report_date}'  /* REPORTING DATE */
                          and '{report_date}' < accounting_Date
                    
                        union all
                        
                        select 
                                id,
                                master_user_id,
                        
                               instrument_id,
                               portfolio_id,
                               
                               transaction_class_id,
                               
                               strategy1_cash_id,
                               strategy2_cash_id,
                               strategy3_cash_id,
                               
                               strategy1_position_id,
                               strategy2_position_id,
                               strategy3_position_id,
                        
                               position_size_with_sign,
                               cash_consideration,
                               settlement_currency_id,
                               accounting_date,
                               cash_date,
                        
                               account_position_id,
                               account_cash_id,
                               account_interim_id,
                               
                               case 
                                    when cash_date < accounting_date
                                    then cash_date
                                    else accounting_date
                               end
                               as min_date,
                               
                               allocation_balance_id,
                               allocation_pl_id
                               
                        from unioned_transactions_for_balance
                        --where not (accounting_date <= '{report_date}' /* REPORTING DATE */
                        --  and '{report_date}' < cash_date)
                        where not ( (accounting_date <= '{report_date}' 
                          and '{report_date}' < cash_date) 
                          or (cash_date  <= '{report_date}' and '{report_date}' < accounting_date)) 
                            
                    ),
                    
                    filtered_transactions as (
                        
                        select * from unioned_interim_account_transactions
                        {transaction_filter_sql_string}
                        {transaction_date_filter_for_initial_position_sql_string}
                    
                    )
                    
                    -- main query  
                    
                    -- Cash 
                    select 
                    
                        instrument_id,
                        {consolidated_position_columns}
                    
                        name,
                        short_name,
                        user_code,
                        
                        pricing_currency_id,
                        instrument_pricing_currency_fx_rate,
                        instrument_accrued_currency_fx_rate,
                        
                        instrument_principal_price,
                        instrument_accrued_price,
                        instrument_factor,
                        instrument_ytm,
                        daily_price_change,
                        
                        currency_id,
                        
                        item_type,
                        item_type_name,
                        
                        fx_rate,
                        
                        position_size,
                        nominal_position_size,
                        
                        co_directional_exposure_currency_id,
                        counter_directional_exposure_currency_id,
                        
                        exposure_calculation_model_id,
                        long_underlying_exposure_id,
                        short_underlying_exposure_id,
                    
                        has_second_exposure_currency,
                        
                        market_value,
                        market_value_loc,
                        
                        exposure,
                        exposure_loc,
                        
                        exposure_delta_adjusted,
                        exposure_long_underlying_zero,
                        exposure_long_underlying_price,
                        exposure_long_underlying_price_delta,
                        exposure_long_underlying_fx_rate,
                        exposure_long_underlying_fx_rate_delta,
                        
                        exposure_short_underlying_zero,
                        exposure_short_underlying_price,
                        exposure_short_underlying_price_delta,
                        exposure_short_underlying_fx_rate,
                        exposure_short_underlying_fx_rate_delta,
                        
                        exposure_2,
                        exposure_2_loc,
                        
                        net_cost_price,
                        net_cost_price_loc,
                        
                        gross_cost_price,
                        gross_cost_price_loc,
                        
                        principal_invested,
                        principal_invested_loc,
                        
                        amount_invested,
                        amount_invested_loc,
                        
                        principal_invested_fixed,
                        principal_invested_fixed_loc,
                        
                        amount_invested_fixed,
                        amount_invested_fixed_loc,
                        
                        position_return,
                        position_return_loc,
                        net_position_return,
                        net_position_return_loc,
                        
                        position_return_fixed,
                        position_return_fixed_loc,
                        net_position_return_fixed,
                        net_position_return_fixed_loc,
                        
                        time_invested,
                        
                        ytm,
                        modified_duration,
                        ytm_at_cost,
                        return_annually,
                        return_annually_fixed,
            
                        principal_opened,
                        carry_opened,
                        overheads_opened,
                        total_opened,
                        
                        principal_closed,
                        carry_closed,
                        overheads_closed,
                        total_closed,
                        
                        principal_fx_opened,
                        carry_fx_opened,
                        overheads_fx_opened,
                        total_fx_opened,
                        
                        principal_fx_closed,
                        carry_fx_closed,
                        overheads_fx_closed,
                        total_fx_closed,
                        
                        principal_fixed_opened,
                        carry_fixed_opened,
                        overheads_fixed_opened,
                        total_fixed_opened,
                        
                        principal_fixed_closed,
                        carry_fixed_closed,
                        overheads_fixed_closed,
                        total_fixed_closed,
                        
                        -- loc
                        
                        principal_opened_loc,
                        carry_opened_loc,
                        overheads_opened_loc,
                        total_opened_loc,
                        
                        principal_closed_loc,
                        carry_closed_loc,
                        overheads_closed_loc,
                        total_closed_loc,
                        
                        principal_fx_opened_loc,
                        carry_fx_opened_loc,
                        overheads_fx_opened_loc,
                        total_fx_opened_loc,
                        
                        principal_fx_closed_loc,
                        carry_fx_closed_loc,
                        overheads_fx_closed_loc,
                        total_fx_closed_loc,
                        
                        principal_fixed_opened_loc,
                        carry_fixed_opened_loc,
                        overheads_fixed_opened_loc,
                        total_fixed_opened_loc,
                        
                        principal_fixed_closed_loc,
                        carry_fixed_closed_loc,
                        overheads_fixed_closed_loc,
                        total_fixed_closed_loc
                    
                    from (   
                    
                        select 
                         
                             (-1) as instrument_id,
                            {consolidated_cash_as_position_columns}
                            
                            (settlement_currency_id) as currency_id,
                                
                            (2) as item_type,
                            ('Currency') as item_type_name,
                            
                            (1) as price,
                            case when settlement_currency_id = {default_currency_id}
                                then 1
                                else
                                    (select
                                fx_rate
                             from currencies_currencyhistory
                             where
                                currency_id = settlement_currency_id and
                                date = '{report_date}' and
                                pricing_policy_id = {pricing_policy_id}
                            )
                            end as fx_rate,
                            
                                
                            position_size,
                            (position_size) as nominal_position_size,
                                      
                            c.name,
                            c.short_name,
                            c.user_code,
                            
                            (settlement_currency_id) as pricing_currency_id,
                            (0) as instrument_pricing_currency_fx_rate, -- WTF?
                            (0) as instrument_accrued_currency_fx_rate,
                            (1) as instrument_principal_price,
                            (0) as instrument_accrued_price,
                            (1) as instrument_factor,
                            (0) as instrument_ytm,
                            (0) as daily_price_change,
                            
                            (c.id) as co_directional_exposure_currency_id,
                            (-1) as counter_directional_exposure_currency_id,
                            
                            (-1) as exposure_calculation_model_id,
                            (-1) as long_underlying_exposure_id,
                            (-1) as short_underlying_exposure_id,
                        
                            (false) as has_second_exposure_currency,
                                
                            market_value,
                            market_value_loc,
                            
                            exposure,
                            exposure_loc,
                            
                            (0) as exposure_delta_adjusted,
                            (0) as exposure_long_underlying_zero,
                            (0) as exposure_long_underlying_price,
                            (0) as exposure_long_underlying_price_delta,
                            (0) as exposure_long_underlying_fx_rate,
                            (0) as exposure_long_underlying_fx_rate_delta,
                            
                            (0) as exposure_short_underlying_zero,
                            (0) as exposure_short_underlying_price,
                            (0) as exposure_short_underlying_price_delta,
                            (0) as exposure_short_underlying_fx_rate,
                            (0) as exposure_short_underlying_fx_rate_delta,
                            
                            (0) as exposure_2,
                            (0) as exposure_2_loc,
                            
                            (0) as net_cost_price,
                            (0) as net_cost_price_loc,
                            
                            (0) as gross_cost_price,
                            (0) as gross_cost_price_loc,
                            
                            (0) as principal_invested,
                            (0) as principal_invested_loc,
                            
                            (0) as amount_invested,
                            (0) as amount_invested_loc,
                            
                            (0) as principal_invested_fixed,
                            (0) as principal_invested_fixed_loc,
                            
                            (0) as amount_invested_fixed,
                            (0) as amount_invested_fixed_loc,
                                
                            (0) as position_return,
                            (0) as position_return_loc,
                            (0) as net_position_return,
                            (0) as net_position_return_loc,
                            
                            (0) as position_return_fixed,
                            (0) as position_return_fixed_loc,
                            (0) as net_position_return_fixed,
                            (0) as net_position_return_fixed_loc,
                            
                            (0) as time_invested,
                            
                            (0) as ytm,
                            (0) as modified_duration,
                            (0) as ytm_at_cost,
                            (0) as return_annually,
                            (0) as return_annually_fixed,
                            
                            (0) as principal_opened,
                            (0) as carry_opened,
                            (0) as overheads_opened,
                            (0) as total_opened,
                            
                            (0) as principal_closed,
                            (0) as carry_closed,
                            (0) as overheads_closed,
                            (0) as total_closed,
                            
                            (0) as principal_fx_opened,
                            (0) as carry_fx_opened,
                            (0) as overheads_fx_opened,
                            (0) as total_fx_opened,
                            
                            (0) as principal_fx_closed,
                            (0) as carry_fx_closed,
                            (0) as overheads_fx_closed,
                            (0) as total_fx_closed,
                            
                            (0) as principal_fixed_opened,
                            (0) as carry_fixed_opened,
                            (0) as overheads_fixed_opened,
                            (0) as total_fixed_opened,
                            
                            (0) as principal_fixed_closed,
                            (0) as carry_fixed_closed,
                            (0) as overheads_fixed_closed,
                            (0) as total_fixed_closed,
                            
                            -- loc
                            
                            (0) as principal_opened_loc,
                            (0) as carry_opened_loc,
                            (0) as overheads_opened_loc,
                            (0) as total_opened_loc,
                            
                            (0) as principal_closed_loc,
                            (0) as carry_closed_loc,
                            (0) as overheads_closed_loc,
                            (0) as total_closed_loc,
                            
                            (0) as principal_fx_opened_loc,
                            (0) as carry_fx_opened_loc,
                            (0) as overheads_fx_opened_loc,
                            (0) as total_fx_opened_loc,
                            
                            (0) as principal_fx_closed_loc,
                            (0) as carry_fx_closed_loc,
                            (0) as overheads_fx_closed_loc,
                            (0) as total_fx_closed_loc,
                            
                            (0) as principal_fixed_opened_loc,
                            (0) as carry_fixed_opened_loc,
                            (0) as overheads_fixed_opened_loc,
                            (0) as total_fixed_opened_loc,
                            
                            (0) as principal_fixed_closed_loc,
                            (0) as carry_fixed_closed_loc,
                            (0) as overheads_fixed_closed_loc,
                            (0) as total_fixed_closed_loc
                        
                         from (
                       
                            select 
                            
                                {consolidated_cash_columns}
                                settlement_currency_id,
                                
                                SUM(position_size) as position_size,
                                SUM(market_value) as market_value,
                                SUM(market_value_loc) as market_value_loc,
                                
                                SUM(exposure) as exposure,
                                SUM(exposure_loc) as exposure_loc
                                
                            from (
                             -- Cash 
                                select 
                                
                                    instrument_id,
                                    {consolidated_cash_columns}
                                    settlement_currency_id,
        
                                    position_size,
          
                                    (t_with_report_fx_rate.position_size * stl_fx_rate / report_fx_rate) as market_value,
                                    (t_with_report_fx_rate.position_size * stl_fx_rate) as market_value_loc,
                                    
                                    (t_with_report_fx_rate.position_size * stl_fx_rate / report_fx_rate) as exposure,
                                    (t_with_report_fx_rate.position_size * stl_fx_rate) as exposure_loc
                                     
                                from 
                                    (select 
                                        *,
                                        case when {report_currency_id} = {default_currency_id}
                                            then 1
                                            else
                                                (select
                                            fx_rate
                                         from currencies_currencyhistory
                                         where
                                            currency_id = {report_currency_id} and
                                            date = '{report_date}' and
                                            pricing_policy_id = {pricing_policy_id}
                                        )
                                            end as report_fx_rate,
                
                                        case when settlement_currency_id = {default_currency_id}
                                            then 1
                                            else
                                                (select
                                            fx_rate
                                         from currencies_currencyhistory
                                         where
                                            currency_id = settlement_currency_id and
                                            date = '{report_date}' and
                                            pricing_policy_id = {pricing_policy_id}
                                        )
                                            end as stl_fx_rate
                                    from (
                                        select
                                          {consolidated_cash_columns}
                                          settlement_currency_id,
                                           (-1) as instrument_id,
                                          SUM(cash_consideration) as position_size
                                        from filtered_transactions
                                        where min_date <= '{report_date}' and master_user_id = {master_user_id}
                                        group by
                                          {consolidated_cash_columns}
                                          settlement_currency_id, instrument_id
                                        ) as t
                                    ) as t_with_report_fx_rate
                                
                            ) as unioned_transaction_pl_with_cash 
                            
                            group by
                                      {consolidated_cash_columns}
                                      settlement_currency_id
                            
                        ) as grouped_cash
                        
                        left join currencies_currency as c
                        ON grouped_cash.settlement_currency_id = c.id
                        where position_size != 0
                        
                    ) as pre_final_union_cash_calculations_level_0
                    
                    union all
                    
                    -- Positions
                    select 
                        
                        instrument_id,
                        {consolidated_position_columns}
                    
                        name,
                        short_name,
                        user_code,
                        
                        pricing_currency_id,
                        instrument_pricing_currency_fx_rate,
                        instrument_accrued_currency_fx_rate,
                        
                        instrument_principal_price,
                        instrument_accrued_price,
                        instrument_factor,
                        instrument_ytm,
                        daily_price_change,
                        
                        currency_id,
                        
                        item_type,
                        item_type_name,
                        
                        fx_rate,
                        
                        position_size,
                        nominal_position_size,
                        
                        co_directional_exposure_currency_id,
                        counter_directional_exposure_currency_id,
                        
                        exposure_calculation_model_id,
                        long_underlying_exposure_id,
                        short_underlying_exposure_id,
                    
                        has_second_exposure_currency,
                        
                        market_value,
                        market_value_loc,
                        
                        exposure,
                        exposure_loc,
                        
                        exposure_delta_adjusted,
                        exposure_long_underlying_zero,
                        exposure_long_underlying_price,
                        exposure_long_underlying_price_delta,
                        exposure_long_underlying_fx_rate,
                        exposure_long_underlying_fx_rate_delta,
                        
                        exposure_short_underlying_zero,
                        exposure_short_underlying_price,
                        exposure_short_underlying_price_delta,
                        exposure_short_underlying_fx_rate,
                        exposure_short_underlying_fx_rate_delta,
                        
                        exposure_2,
                        exposure_2_loc,
                        
                        net_cost_price,
                        net_cost_price_loc,
                        
                        gross_cost_price,
                        gross_cost_price_loc,
                        
                        principal_invested,
                        principal_invested_loc,
                        
                        amount_invested,
                        amount_invested_loc,
                        
                        principal_invested_fixed,
                        principal_invested_fixed_loc,
                        
                        amount_invested_fixed,
                        amount_invested_fixed_loc,
                        
                        position_return,
                        position_return_loc,
                        net_position_return,
                        net_position_return_loc,
                        
                        position_return_fixed,
                        position_return_fixed_loc,
                        net_position_return_fixed,
                        net_position_return_fixed_loc,
                        
                        time_invested,
                        
                        ytm,
                        modified_duration,
                        ytm_at_cost,
                        return_annually,
                        return_annually_fixed,
            
                        principal_opened,
                        carry_opened,
                        overheads_opened,
                        total_opened,
                        
                        principal_closed,
                        carry_closed,
                        overheads_closed,
                        total_closed,
                        
                        principal_fx_opened,
                        carry_fx_opened,
                        overheads_fx_opened,
                        total_fx_opened,
                        
                        principal_fx_closed,
                        carry_fx_closed,
                        overheads_fx_closed,
                        total_fx_closed,
                        
                        principal_fixed_opened,
                        carry_fixed_opened,
                        overheads_fixed_opened,
                        total_fixed_opened,
                        
                        principal_fixed_closed,
                        carry_fixed_closed,
                        overheads_fixed_closed,
                        total_fixed_closed,
                        
                        -- loc
                        
                        principal_opened_loc,
                        carry_opened_loc,
                        overheads_opened_loc,
                        total_opened_loc,
                        
                        principal_closed_loc,
                        carry_closed_loc,
                        overheads_closed_loc,
                        total_closed_loc,
                        
                        principal_fx_opened_loc,
                        carry_fx_opened_loc,
                        overheads_fx_opened_loc,
                        total_fx_opened_loc,
                        
                        principal_fx_closed_loc,
                        carry_fx_closed_loc,
                        overheads_fx_closed_loc,
                        total_fx_closed_loc,
                        
                        principal_fixed_opened_loc,
                        carry_fixed_opened_loc,
                        overheads_fixed_opened_loc,
                        total_fixed_opened_loc,
                        
                        principal_fixed_closed_loc,
                        carry_fixed_closed_loc,
                        overheads_fixed_closed_loc,
                        total_fixed_closed_loc
                        
                    from (
                        select 
                            balance_q.instrument_id,
                            {balance_q_consolidated_select_columns}
                        
                            name,
                            short_name,
                            user_code,
                            
                            pricing_currency_id,
                            instrument_pricing_currency_fx_rate,
                            instrument_accrued_currency_fx_rate,
                            
                            instrument_principal_price,
                            instrument_accrued_price,
                            instrument_factor,
                            instrument_ytm,
                            daily_price_change,
                            
                            (-1) as currency_id,
                            
                            item_type,
                            item_type_name,
                            
                            price,
                            fx_rate,
                            
                            position_size,
                            nominal_position_size,
                            
                            exposure_calculation_model_id,
                            co_directional_exposure_currency_id,
                            counter_directional_exposure_currency_id,
                            
                            long_underlying_exposure_id,
                            short_underlying_exposure_id,
                
                            has_second_exposure_currency,
                            
                            case
                                 when instrument_class_id = 5
                                     then (position_size * (instrument_principal_price - pl_q.principal_cost_price_loc) * price_multiplier * pch_fx_rate) / rep_cur_fx
                                 else market_value / rep_cur_fx
                             end as market_value,
                
                            case
                                 when instrument_class_id = 5
                                     then (position_size * (instrument_principal_price - pl_q.principal_cost_price_loc) * price_multiplier)
                                 else market_value / pch_fx_rate
                            end as market_value_loc,
                
                            (exposure / rep_cur_fx) as exposure,
                            (exposure_2 / rep_cur_fx) as exposure_2,
                            (exposure_delta_adjusted / rep_cur_fx) as exposure_delta_adjusted,
                            
                            exposure_long_underlying_zero,
                            exposure_long_underlying_price,
                            exposure_long_underlying_price_delta,
                            exposure_long_underlying_fx_rate,
                            exposure_long_underlying_fx_rate_delta,
                            
                            exposure_short_underlying_zero,
                            exposure_short_underlying_price,
                            exposure_short_underlying_price_delta,
                            exposure_short_underlying_fx_rate,
                            exposure_short_underlying_fx_rate_delta,
                            
                            (exposure / ec1_fx_rate) as exposure_loc,
                            (exposure_2 / ec2_fx_rate) as exposure_2_loc,
                            
                            /* instrument_long_delta */
                            /* instrument_short_delta */
                            
                            net_cost_price,
                            net_cost_price_loc,
                            
                            gross_cost_price,
                            gross_cost_price_loc,
                            
                            principal_invested,
                            principal_invested_loc,
                            
                            amount_invested,
                            amount_invested_loc,
                            
                            principal_invested_fixed,
                            principal_invested_fixed_loc,
                            
                            amount_invested_fixed,
                            amount_invested_fixed_loc,
                            
                            position_return,
                            position_return_loc,
                            net_position_return,
                            net_position_return_loc,
                            
                            position_return_fixed,
                            position_return_fixed_loc,
                            net_position_return_fixed,
                            net_position_return_fixed_loc,
                            
                            time_invested,
                            
                            ytm,
                            modified_duration,
                            ytm_at_cost,
                            return_annually,
                            return_annually_fixed,
                
                            principal_opened,
                            carry_opened,
                            overheads_opened,
                            total_opened,
                            
                            principal_closed,
                            carry_closed,
                            overheads_closed,
                            total_closed,
                            
                            principal_fx_opened,
                            carry_fx_opened,
                            overheads_fx_opened,
                            total_fx_opened,
                            
                            principal_fx_closed,
                            carry_fx_closed,
                            overheads_fx_closed,
                            total_fx_closed,
                            
                            principal_fixed_opened,
                            carry_fixed_opened,
                            overheads_fixed_opened,
                            total_fixed_opened,
                            
                            principal_fixed_closed,
                            carry_fixed_closed,
                            overheads_fixed_closed,
                            total_fixed_closed,
                            
                            -- loc
                            
                            principal_opened_loc,
                            carry_opened_loc,
                            overheads_opened_loc,
                            total_opened_loc,
                            
                            principal_closed_loc,
                            carry_closed_loc,
                            overheads_closed_loc,
                            total_closed_loc,
                            
                            principal_fx_opened_loc,
                            carry_fx_opened_loc,
                            overheads_fx_opened_loc,
                            total_fx_opened_loc,
                            
                            principal_fx_closed_loc,
                            carry_fx_closed_loc,
                            overheads_fx_closed_loc,
                            total_fx_closed_loc,
                            
                            principal_fixed_opened_loc,
                            carry_fixed_opened_loc,
                            overheads_fixed_opened_loc,
                            total_fixed_opened_loc,
                            
                            principal_fixed_closed_loc,
                            carry_fixed_closed_loc,
                            overheads_fixed_closed_loc,
                            total_fixed_closed_loc
                            
                        from (
                            select 
                        
                            instrument_id,
                            {consolidated_position_columns}
                            
                            position_size,
                            case when coalesce(factor,1) = 0
                                    then position_size
                                    else
                                        position_size / coalesce(factor,1)
                            end as nominal_position_size,
    
                            (1) as item_type,
                            ('Instrument') as item_type_name,
                            
                            (principal_price) as price,
                            (pch_fx_rate) as fx_rate,
        
                            name,
                            short_name,
                            user_code,
        
                            pricing_currency_id,
                            (pch_fx_rate) as instrument_pricing_currency_fx_rate,
                            (ach_fx_rate) as instrument_accrued_currency_fx_rate,
                            
                            instrument_class_id,
                            co_directional_exposure_currency_id,
                            counter_directional_exposure_currency_id,
                            
                            exposure_calculation_model_id,
                            long_underlying_exposure_id,
                            short_underlying_exposure_id,
    
                            has_second_exposure_currency,
        
                            case when pricing_currency_id = {report_currency_id}
                                   then 1
                               else
                                   (rep_cur_fx/pch_fx_rate)
                            end as cross_loc_prc_fx,
        
                            (principal_price) as instrument_principal_price,
                            (accrued_price) as instrument_accrued_price,
                            (factor) as instrument_factor,
                            (ytm) as instrument_ytm,
                            
                            case when coalesce(yesterday_principal_price,0) = 0
                                    then 0
                                    else
                                        (principal_price - yesterday_principal_price) / yesterday_principal_price
                            end as daily_price_change,
                        
                            
                            (long_delta) as instrument_long_delta,
                            (short_delta) as instrument_short_delta,
        
                            (position_size * principal_price * price_multiplier * pch_fx_rate + (position_size * accrued_price * ach_fx_rate * 1 * accrued_multiplier)) as market_value,
                            (position_size * principal_price * price_multiplier * pch_fx_rate + (position_size * accrued_price * ach_fx_rate * 1 * accrued_multiplier)) as exposure,
    
                            -(position_size * principal_price * price_multiplier * pch_fx_rate + (position_size * accrued_price * ach_fx_rate * 1 * accrued_multiplier)) as exposure_2,
                            
                            /* Position * (Price * Multiplier * Long Delta * Pricing to Exposure FX Rate + Accrued * Multiplier * Accrued to Exposure FX Rate) */
                            (position_size * principal_price * price_multiplier * pch_fx_rate * long_delta + (position_size * accrued_price * ach_fx_rate * 1 * accrued_multiplier)) as exposure_delta_adjusted,
                            
                            (0) as exposure_long_underlying_zero,
                            (underlying_long_multiplier * lui_principal_price * lui_price_multiplier + underlying_long_multiplier * lui_accrued_price * lui_accrued_multiplier) as exposure_long_underlying_price,
                            (underlying_long_multiplier * long_delta * lui_principal_price * lui_price_multiplier + underlying_long_multiplier * lui_accrued_price * lui_accrued_multiplier) as exposure_long_underlying_price_delta,
                            (underlying_long_multiplier * ec1_fx_rate) as exposure_long_underlying_fx_rate,
                            (underlying_long_multiplier * long_delta * ec1_fx_rate) as exposure_long_underlying_fx_rate_delta,
                            
                            /*Market Value Long Underlying Exposure
                            1) "Zero":
                            =0
                            
                            2) "Long Underlying Instrument Price Exposure":
                             Long Underlying Multiplier* [Long Underlying Instrument].[Price] * [Long Underlying Instrument].[Price Multiplier] + Long Underlying Multiplier * [Long Underlying Instrument].[Accrued] * [Long Underlying Instrument].[Accrued Multiplier]
    
                            
                            3) "Long Underlying Instrument Price Delta-adjusted Exposure":
                            Long Underlying Multiplier * Long Delta * [Long Underlying Instrument].[Price] * [Long Underlying Instrument].[Price Multiplier] + Long Underlying Multiplier * [Long Underlying Instrument].[Accrued] * [Long Underlying Instrument].[Accrued Multiplier]
    
                            4) "Long Underlying Currency FX Rate Exposure": 
                             Long Underlying Multiplier * [Long Underlying Currency].[FX Rate]
                            
                            5) "Long Underlying Currency FX Rate Delta-adjusted Exposure": 
                            Long Underlying Multiplier * Long Delta * [Long Underlying Currency].[FX Rate]
                            
                            */
                            
                            (0) as exposure_short_underlying_zero,
                            (underlying_short_multiplier * sui_principal_price * sui_price_multiplier + underlying_short_multiplier * sui_accrued_price * sui_accrued_multiplier) as exposure_short_underlying_price,
                            (underlying_short_multiplier * short_delta * sui_principal_price * sui_price_multiplier + underlying_short_multiplier * sui_accrued_price * sui_accrued_multiplier) as exposure_short_underlying_price_delta,
                            (underlying_short_multiplier * ec1_fx_rate) as exposure_short_underlying_fx_rate,
                            (underlying_short_multiplier * short_delta * ec1_fx_rate) as exposure_short_underlying_fx_rate_delta,
                            
                            price_multiplier,
                            pch_fx_rate,
                            rep_cur_fx,
                            ec1_fx_rate,
                            ec2_fx_rate
                            
                        from (
                            select
                                instrument_id,
                                {consolidated_position_columns}
                                
                                position_size,
                                
                                i.name,
                                i.short_name,
                                i.user_code,
                                i.pricing_currency_id,
                                i.price_multiplier,
                                i.accrued_multiplier,
                                
                                i.exposure_calculation_model_id,
                                i.underlying_long_multiplier,
                                i.underlying_short_multiplier,
                                
                                i.co_directional_exposure_currency_id,
                                i.counter_directional_exposure_currency_id,
                                
                                i.long_underlying_exposure_id,
                                i.short_underlying_exposure_id,
                                
                                it.instrument_class_id,
    
                                it.has_second_exposure_currency,
                                
                                
                                (lui.price_multiplier) as lui_price_multiplier,
                                (lui.accrued_multiplier) as lui_accrued_multiplier,
                                
                                (sui.price_multiplier) as sui_price_multiplier,
                                (sui.accrued_multiplier) as sui_accrued_multiplier,
                                
                                (select 
                                    principal_price
                                from instruments_pricehistory
                                where 
                                    instrument_id=lui.id and 
                                    date = '{report_date}' and
                                    pricing_policy_id = {pricing_policy_id})
                                as lui_principal_price,
                                
                                (select 
                                    accrued_price
                                from instruments_pricehistory
                                where 
                                    instrument_id=lui.id and 
                                    date = '{report_date}' and
                                    pricing_policy_id = {pricing_policy_id})
                                as lui_accrued_price,
                                
                                (select 
                                    principal_price
                                from instruments_pricehistory
                                where 
                                    instrument_id=sui.id and 
                                    date = '{report_date}' and
                                    pricing_policy_id = {pricing_policy_id})
                                as sui_principal_price,
                                
                                (select 
                                    accrued_price
                                from instruments_pricehistory
                                where 
                                    instrument_id=sui.id and 
                                    date = '{report_date}' and
                                    pricing_policy_id = {pricing_policy_id})
                                as sui_accrued_price,
                                
                                case when i.co_directional_exposure_currency_id = {report_currency_id}
                                            then 1
                                        else
                                            (select
                                                 fx_rate
                                             from currencies_currencyhistory
                                             where
                                                     currency_id = i.co_directional_exposure_currency_id and
                                                     date = '{report_date}' and
                                                     pricing_policy_id = {pricing_policy_id}
                                            )
                                       end as ec1_fx_rate,
    
                                   case when i.counter_directional_exposure_currency_id = {report_currency_id}
                                            then 1
                                        else
                                            (select
                                                 fx_rate
                                             from currencies_currencyhistory
                                             where
                                                     currency_id = i.counter_directional_exposure_currency_id and
                                                     date = '{report_date}' and
                                                     pricing_policy_id = {pricing_policy_id}
                                            )
                                    end as ec2_fx_rate,
                                
                                case
                                       when {report_currency_id} = {default_currency_id}
                                           then 1
                                       else
                                           (select fx_rate
                                            from currencies_currencyhistory c_ch
                                            where date = '{report_date}'
                                              and c_ch.currency_id = {report_currency_id}
                                              and c_ch.pricing_policy_id = {pricing_policy_id}
                                            limit 1)
                                end as rep_cur_fx,
                                
                                case when i.pricing_currency_id = {default_currency_id}
                                    then 1
                                    else
                                        (select
                                    fx_rate
                                 from currencies_currencyhistory
                                 where
                                    currency_id = i.pricing_currency_id and
                                    date = '{report_date}' and
                                    pricing_policy_id = {pricing_policy_id}
                                )
                                end as pch_fx_rate,
                                
                                case when i.accrued_currency_id = {default_currency_id}
                                    then 1
                                    else
                                        (select
                                    fx_rate
                                 from currencies_currencyhistory
                                 where
                                    currency_id = i.accrued_currency_id and
                                    date = '{report_date}' and
                                    pricing_policy_id = {pricing_policy_id}
                                )
                                end as ach_fx_rate,
                                    
                                (select 
                                    principal_price
                                from instruments_pricehistory
                                where 
                                    instrument_id=i.id and 
                                    date = '{report_date}' and
                                    pricing_policy_id = {pricing_policy_id})
                                as principal_price,
                                
                                (select 
                                    principal_price
                                from instruments_pricehistory
                                where 
                                    instrument_id=i.id and 
                                    date = '{bday_yesterday_of_report_date}' and
                                    pricing_policy_id = {pricing_policy_id})
                                as yesterday_principal_price,
                                
                                (select 
                                    factor
                                from instruments_pricehistory
                                where 
                                    instrument_id=i.id and 
                                    date = '{report_date}' and
                                    pricing_policy_id = {pricing_policy_id})
                                as factor,
                                
                                (select 
                                    ytm
                                from instruments_pricehistory
                                where 
                                    instrument_id=i.id and 
                                    date = '{report_date}' and
                                    pricing_policy_id = {pricing_policy_id})
                                as ytm,
                                
                                (select 
                                    accrued_price
                                from instruments_pricehistory
                                where 
                                    instrument_id=i.id and 
                                    date = '{report_date}' and
                                    pricing_policy_id = {pricing_policy_id} )
                                as accrued_price,
                                
                                (select 
                                    long_delta
                                from instruments_pricehistory
                                where 
                                    instrument_id=i.id and 
                                    date = '{report_date}' and
                                    pricing_policy_id = {pricing_policy_id})
                                as long_delta,
                                
                                (select 
                                    short_delta
                                from instruments_pricehistory
                                where 
                                    instrument_id=i.id and 
                                    date = '{report_date}' and
                                    pricing_policy_id = {pricing_policy_id})
                                as short_delta
                                
                            from
                                (select
                                  {consolidated_position_columns}
                                  instrument_id,
                                  SUM(position_size_with_sign) as position_size
                                from filtered_transactions 
                                where min_date <= '{report_date}' 
                                and master_user_id = {master_user_id}
                                and transaction_class_id in (1,2,14)
                                group by
                                  {consolidated_position_columns}
                                  instrument_id) as t
                            left join instruments_instrument as i
                            ON instrument_id = i.id
                            left join instruments_instrument as lui
                            ON i.long_underlying_instrument_id = lui.id
                            left join instruments_instrument as sui
                            ON i.short_underlying_instrument_id = sui.id
                            left join instruments_instrumenttype as it
                            ON i.instrument_type_id = it.id
                            ) as grouped
                        where position_size != 0
                        ) as balance_q
                        left join 
                            (select 
                                    instrument_id, 
                                    {consolidated_position_columns}
                                    
                                    net_cost_price,
                                    net_cost_price_loc,
                                    principal_cost_price_loc,
                                    gross_cost_price,
                                    gross_cost_price_loc,
                                    
                                    principal_invested,
                                    principal_invested_loc,  
                                    
                                    amount_invested,
                                    amount_invested_loc,
                                    
                                    principal_invested_fixed,
                                    principal_invested_fixed_loc,
                                    
                                    amount_invested_fixed,
                                    amount_invested_fixed_loc,
                                    
                                    position_return,
                                    position_return_loc,
                                    net_position_return,
                                    net_position_return_loc,
                                    
                                    position_return_fixed,
                                    position_return_fixed_loc,
                                    net_position_return_fixed,
                                    net_position_return_fixed_loc,
                                    
                                    time_invested,
                                    
                                    ytm,
                                    modified_duration,
                                    ytm_at_cost,
                                    return_annually,
                                    return_annually_fixed,
                        
                                    principal_opened,
                                    carry_opened,
                                    overheads_opened,
                                    total_opened,
                                    
                                    principal_closed,
                                    carry_closed,
                                    overheads_closed,
                                    total_closed,
                                    
                                    principal_fx_opened,
                                    carry_fx_opened,
                                    overheads_fx_opened,
                                    total_fx_opened,
                                    
                                    principal_fx_closed,
                                    carry_fx_closed,
                                    overheads_fx_closed,
                                    total_fx_closed,
                                    
                                    principal_fixed_opened,
                                    carry_fixed_opened,
                                    overheads_fixed_opened,
                                    total_fixed_opened,
                                    
                                    principal_fixed_closed,
                                    carry_fixed_closed,
                                    overheads_fixed_closed,
                                    total_fixed_closed,
                                    
                                    -- loc
                                    
                                    principal_opened_loc,
                                    carry_opened_loc,
                                    overheads_opened_loc,
                                    total_opened_loc,
                                    
                                    principal_closed_loc,
                                    carry_closed_loc,
                                    overheads_closed_loc,
                                    total_closed_loc,
                                    
                                    principal_fx_opened_loc,
                                    carry_fx_opened_loc,
                                    overheads_fx_opened_loc,
                                    total_fx_opened_loc,
                                    
                                    principal_fx_closed_loc,
                                    carry_fx_closed_loc,
                                    overheads_fx_closed_loc,
                                    total_fx_closed_loc,
                                    
                                    principal_fixed_opened_loc,
                                    carry_fixed_opened_loc,
                                    overheads_fixed_opened_loc,
                                    total_fixed_opened_loc,
                                    
                                    principal_fixed_closed_loc,
                                    carry_fixed_closed_loc,
                                    overheads_fixed_closed_loc,
                                    total_fixed_closed_loc
                                    
                                  from ({pl_query}) as pl where pl.item_type != 6
                        ) as pl_q
                        on balance_q.instrument_id = pl_q.instrument_id {pl_left_join_consolidation}
                    
                    ) as joined_positions
                """

    return query


def get_balance_query():
    # language=PostgreSQL
    query = """
                    
                    with unioned_transactions_for_balance as (
                        
                        select 
                            id,
                            master_user_id,
                        
                            instrument_id,
                            portfolio_id,
                            transaction_class_id,
                            
                            transaction_date,
                            accounting_date,
                            cash_date,
                            
                            account_cash_id,
                            account_position_id,
                            account_interim_id,
                            
                            transaction_currency_id,
                            settlement_currency_id,
                            
                            position_size_with_sign,
                            cash_consideration,
                            
                            strategy1_cash_id,
                            strategy2_cash_id,
                            strategy3_cash_id,
                            
                            strategy1_position_id,
                            strategy2_position_id,
                            strategy3_position_id,
                            
                            allocation_balance_id,
                            allocation_pl_id
                            
                        from pl_transactions_with_ttype
                        
                        union all
                        
                        select 
                            id,
                            master_user_id,
                            
                            instrument_id,
                            portfolio_id,
                            transaction_class_id,
                            
                            transaction_date,
                            accounting_date,
                            cash_date,
                            
                            account_cash_id,
                            account_position_id,
                            account_interim_id,
                            
                            transaction_currency_id,
                            settlement_currency_id,
                            
                            (0) as position_size_with_sign,
                            cash_consideration,
                            
                            strategy1_cash_id,
                            strategy2_cash_id,
                            strategy3_cash_id,
                            
                            strategy1_position_id,
                            strategy2_position_id,
                            strategy3_position_id,
                            allocation_balance_id,
                            allocation_pl_id
                            
                        from pl_cash_fx_trades_transactions_with_ttype
                        
                        union all
                        
                        select 
                            id,
                            master_user_id,
                            
                            instrument_id,
                            portfolio_id,
                            transaction_class_id,
                            
                            transaction_date,
                            accounting_date,
                            cash_date,
                            
                            account_cash_id,
                            account_position_id,
                            account_interim_id,
                            
                            transaction_currency_id,
                            settlement_currency_id,
                            
                            position_size_with_sign,
                            cash_consideration,
                            
                            strategy1_cash_id,
                            strategy2_cash_id,
                            strategy3_cash_id,
                            
                            strategy1_position_id,
                            strategy2_position_id,
                            strategy3_position_id,
                            allocation_balance_id,
                            allocation_pl_id
                            
                            
                        from pl_cash_fx_variations_transactions_with_ttype
                        
                        union all
                        
                        select 
                            id,
                            master_user_id,
                            
                            instrument_id,
                            portfolio_id,
                            transaction_class_id,
                            
                            transaction_date,
                            accounting_date,
                            cash_date,
                            
                            account_cash_id,
                            account_position_id,
                            account_interim_id,
                            
                            transaction_currency_id,
                            settlement_currency_id,
                            
                            position_size_with_sign,
                            cash_consideration,
                            
                            strategy1_cash_id,
                            strategy2_cash_id,
                            strategy3_cash_id,
                            
                            strategy1_position_id,
                            strategy2_position_id,
                            strategy3_position_id,
                            
                            allocation_balance_id,
                            allocation_pl_id
                            
                        from pl_cash_transaction_pl_transactions_with_ttype
                      
                    ),
                    
                    unioned_interim_account_transactions as (
                        
                        select 
                               id,
                               master_user_id,
                               
                               instrument_id,
                               portfolio_id,
                               
                               transaction_class_id,
                  
                               strategy1_cash_id,
                               strategy2_cash_id,
                               strategy3_cash_id,
                               
                               
                               strategy1_position_id,
                               strategy2_position_id,
                               strategy3_position_id,
                               
                               position_size_with_sign,
                               /* не нужны для БАЛАНСА
                               principal_with_sign,
                               carry_with_sign,
                               overheads,
                                */
                               cash_consideration,
                               settlement_currency_id,
                               accounting_date,
                               cash_date,
                               account_position_id,
                               -- modification
                               account_interim_id as account_cash_id,
                               account_interim_id,
                               
                               case 
                                    when cash_date < accounting_date
                                    then cash_date
                                    else accounting_date
                               end
                               as min_date,
                               
                               allocation_balance_id,
                               allocation_pl_id
                               
                        -- добавить остальные поля
                        from unioned_transactions_for_balance -- USE TOTAL VIEW HERE
                        where accounting_date <= '{report_date}' /* REPORTING DATE */
                          and '{report_date}' < cash_date
                        
                        -- case 2
                        union all
                        select 
                                id,
                                master_user_id,
                        
                               instrument_id,
                               portfolio_id,
                               
                               transaction_class_id,
                               
                               strategy1_cash_id,
                               strategy2_cash_id,
                               strategy3_cash_id,
                               
                               strategy1_position_id,
                               strategy2_position_id,
                               strategy3_position_id,
                               
                               
                               -- modification
                               0 as position_size_with_sign,
                               (-cash_consideration) as cash_consideration,
                               settlement_currency_id,
                               accounting_date,
                               cash_date,
                               account_position_id,
                               -- modification
                               account_interim_id as account_cash_id,
                               account_interim_id,
                               
                               case 
                                    when cash_date < accounting_date
                                    then cash_date
                                    else accounting_date
                               end
                               as min_date,
                               allocation_balance_id,
                               allocation_pl_id
                               
                        from unioned_transactions_for_balance
                        where cash_date  <= '{report_date}'  /* REPORTING DATE */
                          and '{report_date}' < accounting_Date
                    
                        union all
                        
                        select 
                                id,
                                master_user_id,
                        
                               instrument_id,
                               portfolio_id,
                               
                               transaction_class_id,
                               
                               strategy1_cash_id,
                               strategy2_cash_id,
                               strategy3_cash_id,
                               
                               strategy1_position_id,
                               strategy2_position_id,
                               strategy3_position_id,
                        
                               position_size_with_sign,
                               cash_consideration,
                               settlement_currency_id,
                               accounting_date,
                               cash_date,
                        
                               account_position_id,
                               account_cash_id,
                               account_interim_id,
                               
                               case 
                                    when cash_date < accounting_date
                                    then cash_date
                                    else accounting_date
                               end
                               as min_date,
                               
                               allocation_balance_id,
                               allocation_pl_id
                               
                        from unioned_transactions_for_balance
                        --where not (accounting_date <= '{report_date}' /* REPORTING DATE */
                        --  and '{report_date}' < cash_date)
                        where not ( (accounting_date <= '{report_date}' 
                          and '{report_date}' < cash_date) 
                          or (cash_date  <= '{report_date}' and '{report_date}' < accounting_date)) 
                            
                    ),
                    
                    filtered_transactions as (
                        
                        select * from unioned_interim_account_transactions
                        {transaction_filter_sql_string}
                        {transaction_date_filter_for_initial_position_sql_string}
                    
                    )
                    
                    -- main query  
                    
                    -- Cash 
                    select 
                    
                        instrument_id,
                        {consolidated_position_columns}
                    
                        name,
                        short_name,
                        user_code,
                        
                        pricing_currency_id,
                        instrument_pricing_currency_fx_rate,
                        instrument_accrued_currency_fx_rate,
                        
                        instrument_principal_price,
                        instrument_accrued_price,
                        instrument_factor,
                        instrument_ytm,
                        daily_price_change,
                        
                        currency_id,
                        
                        item_type,
                        item_type_name,
                        
                        fx_rate,
                        
                        position_size,
                        nominal_position_size,
                        
                        co_directional_exposure_currency_id,
                        counter_directional_exposure_currency_id,
                        
                        exposure_calculation_model_id,
                        long_underlying_exposure_id,
                        short_underlying_exposure_id,
                    
                        has_second_exposure_currency,
                        
                        market_value,
                        market_value_loc,
                        
                        exposure,
                        exposure_loc,
                        
                        exposure_delta_adjusted,
                        exposure_long_underlying_zero,
                        exposure_long_underlying_price,
                        exposure_long_underlying_price_delta,
                        exposure_long_underlying_fx_rate,
                        exposure_long_underlying_fx_rate_delta,
                        
                        exposure_short_underlying_zero,
                        exposure_short_underlying_price,
                        exposure_short_underlying_price_delta,
                        exposure_short_underlying_fx_rate,
                        exposure_short_underlying_fx_rate_delta,
                        
                        exposure_2,
                        exposure_2_loc,
                        
                        net_cost_price,
                        net_cost_price_loc,
                        
                        gross_cost_price,
                        gross_cost_price_loc,
                        
                        principal_invested,
                        principal_invested_loc,
                        
                        amount_invested,
                        amount_invested_loc,
                        
                        principal_invested_fixed,
                        principal_invested_fixed_loc,
                        
                        amount_invested_fixed,
                        amount_invested_fixed_loc,
                        
                        position_return,
                        position_return_loc,
                        net_position_return,
                        net_position_return_loc,
                        
                        position_return_fixed,
                        position_return_fixed_loc,
                        net_position_return_fixed,
                        net_position_return_fixed_loc,
                        
                        time_invested,
                        
                        ytm,
                        modified_duration,
                        ytm_at_cost,
                        return_annually,
                        return_annually_fixed,
            
                        principal_opened,
                        carry_opened,
                        overheads_opened,
                        total_opened,
                        
                        principal_closed,
                        carry_closed,
                        overheads_closed,
                        total_closed,
                        
                        principal_fx_opened,
                        carry_fx_opened,
                        overheads_fx_opened,
                        total_fx_opened,
                        
                        principal_fx_closed,
                        carry_fx_closed,
                        overheads_fx_closed,
                        total_fx_closed,
                        
                        principal_fixed_opened,
                        carry_fixed_opened,
                        overheads_fixed_opened,
                        total_fixed_opened,
                        
                        principal_fixed_closed,
                        carry_fixed_closed,
                        overheads_fixed_closed,
                        total_fixed_closed,
                        
                        -- loc
                        
                        principal_opened_loc,
                        carry_opened_loc,
                        overheads_opened_loc,
                        total_opened_loc,
                        
                        principal_closed_loc,
                        carry_closed_loc,
                        overheads_closed_loc,
                        total_closed_loc,
                        
                        principal_fx_opened_loc,
                        carry_fx_opened_loc,
                        overheads_fx_opened_loc,
                        total_fx_opened_loc,
                        
                        principal_fx_closed_loc,
                        carry_fx_closed_loc,
                        overheads_fx_closed_loc,
                        total_fx_closed_loc,
                        
                        principal_fixed_opened_loc,
                        carry_fixed_opened_loc,
                        overheads_fixed_opened_loc,
                        total_fixed_opened_loc,
                        
                        principal_fixed_closed_loc,
                        carry_fixed_closed_loc,
                        overheads_fixed_closed_loc,
                        total_fixed_closed_loc
                    
                    from (   
                    
                        select 
                         
                             (-1) as instrument_id,
                            {consolidated_cash_as_position_columns}
                            
                            (settlement_currency_id) as currency_id,
                                
                            (2) as item_type,
                            ('Currency') as item_type_name,
                            
                            (1) as price,
                            case when settlement_currency_id = {default_currency_id}
                                then 1
                                else
                                    (select
                                fx_rate
                             from currencies_currencyhistory
                             where
                                currency_id = settlement_currency_id and
                                date = '{report_date}' and
                                pricing_policy_id = {pricing_policy_id}
                            )
                            end as fx_rate,
                            
                                
                            position_size,
                            (position_size) as nominal_position_size,
                                      
                            c.name,
                            c.short_name,
                            c.user_code,
                            
                            (settlement_currency_id) as pricing_currency_id,
                            (0) as instrument_pricing_currency_fx_rate, -- WTF?
                            (0) as instrument_accrued_currency_fx_rate,
                            (1) as instrument_principal_price,
                            (0) as instrument_accrued_price,
                            (1) as instrument_factor,
                            (0) as instrument_ytm,
                            (0) as daily_price_change,
                            
                            (c.id) as co_directional_exposure_currency_id,
                            (-1) as counter_directional_exposure_currency_id,
                            
                            (-1) as exposure_calculation_model_id,
                            (-1) as long_underlying_exposure_id,
                            (-1) as short_underlying_exposure_id,
                        
                            (false) as has_second_exposure_currency,
                                
                            market_value,
                            market_value_loc,
                            
                            exposure,
                            exposure_loc,
                            
                            (0) as exposure_delta_adjusted,
                            (0) as exposure_long_underlying_zero,
                            (0) as exposure_long_underlying_price,
                            (0) as exposure_long_underlying_price_delta,
                            (0) as exposure_long_underlying_fx_rate,
                            (0) as exposure_long_underlying_fx_rate_delta,
                            
                            (0) as exposure_short_underlying_zero,
                            (0) as exposure_short_underlying_price,
                            (0) as exposure_short_underlying_price_delta,
                            (0) as exposure_short_underlying_fx_rate,
                            (0) as exposure_short_underlying_fx_rate_delta,
                            
                            (0) as exposure_2,
                            (0) as exposure_2_loc,
                            
                            (0) as net_cost_price,
                            (0) as net_cost_price_loc,
                            
                            (0) as gross_cost_price,
                            (0) as gross_cost_price_loc,
                            
                            (0) as principal_invested,
                            (0) as principal_invested_loc,
                            
                            (0) as amount_invested,
                            (0) as amount_invested_loc,
                            
                            (0) as principal_invested_fixed,
                            (0) as principal_invested_fixed_loc,
                            
                            (0) as amount_invested_fixed,
                            (0) as amount_invested_fixed_loc,
                                
                            (0) as position_return,
                            (0) as position_return_loc,
                            (0) as net_position_return,
                            (0) as net_position_return_loc,
                            
                            (0) as position_return_fixed,
                            (0) as position_return_fixed_loc,
                            (0) as net_position_return_fixed,
                            (0) as net_position_return_fixed_loc,
                            
                            (0) as time_invested,
                            
                            (0) as ytm,
                            (0) as modified_duration,
                            (0) as ytm_at_cost,
                            (0) as return_annually,
                            (0) as return_annually_fixed,
                            
                            (0) as principal_opened,
                            (0) as carry_opened,
                            (0) as overheads_opened,
                            (0) as total_opened,
                            
                            (0) as principal_closed,
                            (0) as carry_closed,
                            (0) as overheads_closed,
                            (0) as total_closed,
                            
                            (0) as principal_fx_opened,
                            (0) as carry_fx_opened,
                            (0) as overheads_fx_opened,
                            (0) as total_fx_opened,
                            
                            (0) as principal_fx_closed,
                            (0) as carry_fx_closed,
                            (0) as overheads_fx_closed,
                            (0) as total_fx_closed,
                            
                            (0) as principal_fixed_opened,
                            (0) as carry_fixed_opened,
                            (0) as overheads_fixed_opened,
                            (0) as total_fixed_opened,
                            
                            (0) as principal_fixed_closed,
                            (0) as carry_fixed_closed,
                            (0) as overheads_fixed_closed,
                            (0) as total_fixed_closed,
                            
                            -- loc
                            
                            (0) as principal_opened_loc,
                            (0) as carry_opened_loc,
                            (0) as overheads_opened_loc,
                            (0) as total_opened_loc,
                            
                            (0) as principal_closed_loc,
                            (0) as carry_closed_loc,
                            (0) as overheads_closed_loc,
                            (0) as total_closed_loc,
                            
                            (0) as principal_fx_opened_loc,
                            (0) as carry_fx_opened_loc,
                            (0) as overheads_fx_opened_loc,
                            (0) as total_fx_opened_loc,
                            
                            (0) as principal_fx_closed_loc,
                            (0) as carry_fx_closed_loc,
                            (0) as overheads_fx_closed_loc,
                            (0) as total_fx_closed_loc,
                            
                            (0) as principal_fixed_opened_loc,
                            (0) as carry_fixed_opened_loc,
                            (0) as overheads_fixed_opened_loc,
                            (0) as total_fixed_opened_loc,
                            
                            (0) as principal_fixed_closed_loc,
                            (0) as carry_fixed_closed_loc,
                            (0) as overheads_fixed_closed_loc,
                            (0) as total_fixed_closed_loc
                        
                         from (
                       
                            select 
                            
                                {consolidated_cash_columns}
                                settlement_currency_id,
                                
                                SUM(position_size) as position_size,
                                SUM(market_value) as market_value,
                                SUM(market_value_loc) as market_value_loc,
                                
                                SUM(exposure) as exposure,
                                SUM(exposure_loc) as exposure_loc
                                
                            from (
                             -- Cash 
                                select 
                                
                                    instrument_id,
                                    {consolidated_cash_columns}
                                    settlement_currency_id,
        
                                    position_size,
          
                                    (t_with_report_fx_rate.position_size * stl_fx_rate / report_fx_rate) as market_value,
                                    (t_with_report_fx_rate.position_size * stl_fx_rate) as market_value_loc,
                                    
                                    (t_with_report_fx_rate.position_size * stl_fx_rate / report_fx_rate) as exposure,
                                    (t_with_report_fx_rate.position_size * stl_fx_rate) as exposure_loc
                                     
                                from 
                                    (select 
                                        *,
                                        case when {report_currency_id} = {default_currency_id}
                                            then 1
                                            else
                                                (select
                                            fx_rate
                                         from currencies_currencyhistory
                                         where
                                            currency_id = {report_currency_id} and
                                            date = '{report_date}' and
                                            pricing_policy_id = {pricing_policy_id}
                                        )
                                            end as report_fx_rate,
                
                                        case when settlement_currency_id = {default_currency_id}
                                            then 1
                                            else
                                                (select
                                            fx_rate
                                         from currencies_currencyhistory
                                         where
                                            currency_id = settlement_currency_id and
                                            date = '{report_date}' and
                                            pricing_policy_id = {pricing_policy_id}
                                        )
                                            end as stl_fx_rate
                                    from (
                                        select
                                          {consolidated_cash_columns}
                                          settlement_currency_id,
                                           (-1) as instrument_id,
                                          SUM(cash_consideration) as position_size
                                        from filtered_transactions
                                        where min_date <= '{report_date}' and master_user_id = {master_user_id}
                                        group by
                                          {consolidated_cash_columns}
                                          settlement_currency_id, instrument_id
                                        ) as t
                                    ) as t_with_report_fx_rate
                                
                            ) as unioned_transaction_pl_with_cash 
                            
                            group by
                                      {consolidated_cash_columns}
                                      settlement_currency_id
                            
                        ) as grouped_cash
                        
                        left join currencies_currency as c
                        ON grouped_cash.settlement_currency_id = c.id
                        where position_size != 0
                        
                    ) as pre_final_union_cash_calculations_level_0
                    
                    union all
                    
                    -- Positions
                    select 
                        
                        instrument_id,
                        {consolidated_position_columns}
                    
                        name,
                        short_name,
                        user_code,
                        
                        pricing_currency_id,
                        instrument_pricing_currency_fx_rate,
                        instrument_accrued_currency_fx_rate,
                        
                        instrument_principal_price,
                        instrument_accrued_price,
                        instrument_factor,
                        instrument_ytm,
                        daily_price_change,
                        
                        currency_id,
                        
                        item_type,
                        item_type_name,
                        
                        fx_rate,
                        
                        position_size,
                        nominal_position_size,
                        
                        co_directional_exposure_currency_id,
                        counter_directional_exposure_currency_id,
                        
                        exposure_calculation_model_id,
                        long_underlying_exposure_id,
                        short_underlying_exposure_id,
                    
                        has_second_exposure_currency,
                        
                        market_value,
                        market_value_loc,
                        
                        exposure,
                        exposure_loc,
                        
                        exposure_delta_adjusted,
                        exposure_long_underlying_zero,
                        exposure_long_underlying_price,
                        exposure_long_underlying_price_delta,
                        exposure_long_underlying_fx_rate,
                        exposure_long_underlying_fx_rate_delta,
                        
                        exposure_short_underlying_zero,
                        exposure_short_underlying_price,
                        exposure_short_underlying_price_delta,
                        exposure_short_underlying_fx_rate,
                        exposure_short_underlying_fx_rate_delta,
                        
                        exposure_2,
                        exposure_2_loc,
                        
                        net_cost_price,
                        net_cost_price_loc,
                        
                        gross_cost_price,
                        gross_cost_price_loc,
                        
                        principal_invested,
                        principal_invested_loc,
                        
                        amount_invested,
                        amount_invested_loc,
                        
                        principal_invested_fixed,
                        principal_invested_fixed_loc,
                        
                        amount_invested_fixed,
                        amount_invested_fixed_loc,
                        
                        position_return,
                        position_return_loc,
                        net_position_return,
                        net_position_return_loc,
                        
                        position_return_fixed,
                        position_return_fixed_loc,
                        net_position_return_fixed,
                        net_position_return_fixed_loc,
                        
                        time_invested,
                        
                        ytm,
                        modified_duration,
                        ytm_at_cost,
                        return_annually,
                        return_annually_fixed,
            
                        principal_opened,
                        carry_opened,
                        overheads_opened,
                        total_opened,
                        
                        principal_closed,
                        carry_closed,
                        overheads_closed,
                        total_closed,
                        
                        principal_fx_opened,
                        carry_fx_opened,
                        overheads_fx_opened,
                        total_fx_opened,
                        
                        principal_fx_closed,
                        carry_fx_closed,
                        overheads_fx_closed,
                        total_fx_closed,
                        
                        principal_fixed_opened,
                        carry_fixed_opened,
                        overheads_fixed_opened,
                        total_fixed_opened,
                        
                        principal_fixed_closed,
                        carry_fixed_closed,
                        overheads_fixed_closed,
                        total_fixed_closed,
                        
                        -- loc
                        
                        principal_opened_loc,
                        carry_opened_loc,
                        overheads_opened_loc,
                        total_opened_loc,
                        
                        principal_closed_loc,
                        carry_closed_loc,
                        overheads_closed_loc,
                        total_closed_loc,
                        
                        principal_fx_opened_loc,
                        carry_fx_opened_loc,
                        overheads_fx_opened_loc,
                        total_fx_opened_loc,
                        
                        principal_fx_closed_loc,
                        carry_fx_closed_loc,
                        overheads_fx_closed_loc,
                        total_fx_closed_loc,
                        
                        principal_fixed_opened_loc,
                        carry_fixed_opened_loc,
                        overheads_fixed_opened_loc,
                        total_fixed_opened_loc,
                        
                        principal_fixed_closed_loc,
                        carry_fixed_closed_loc,
                        overheads_fixed_closed_loc,
                        total_fixed_closed_loc
                        
                    from (
                        select 
                            balance_q.instrument_id,
                            {balance_q_consolidated_select_columns}
                        
                            name,
                            short_name,
                            user_code,
                            
                            pricing_currency_id,
                            instrument_pricing_currency_fx_rate,
                            instrument_accrued_currency_fx_rate,
                            
                            instrument_principal_price,
                            instrument_accrued_price,
                            instrument_factor,
                            instrument_ytm,
                            daily_price_change,
                            
                            (-1) as currency_id,
                            
                            item_type,
                            item_type_name,
                            
                            price,
                            fx_rate,
                            
                            position_size,
                            nominal_position_size,
                            
                            exposure_calculation_model_id,
                            co_directional_exposure_currency_id,
                            counter_directional_exposure_currency_id,
                            
                            long_underlying_exposure_id,
                            short_underlying_exposure_id,
                
                            has_second_exposure_currency,
                            
                            (market_value / rep_cur_fx) as market_value,
                
                            (market_value / pch_fx_rate) as market_value_loc,
                
                            (exposure / rep_cur_fx) as exposure,
                            (exposure_2 / rep_cur_fx) as exposure_2,
                            (exposure_delta_adjusted / rep_cur_fx) as exposure_delta_adjusted,
                            
                            exposure_long_underlying_zero,
                            exposure_long_underlying_price,
                            exposure_long_underlying_price_delta,
                            exposure_long_underlying_fx_rate,
                            exposure_long_underlying_fx_rate_delta,
                            
                            exposure_short_underlying_zero,
                            exposure_short_underlying_price,
                            exposure_short_underlying_price_delta,
                            exposure_short_underlying_fx_rate,
                            exposure_short_underlying_fx_rate_delta,
                            
                            (exposure / ec1_fx_rate) as exposure_loc,
                            (exposure_2 / ec2_fx_rate) as exposure_2_loc,
                            
                            /* instrument_long_delta */
                            /* instrument_short_delta */
                            
                            (0) as net_cost_price,
                            (0) as net_cost_price_loc,
                            
                            (0) as gross_cost_price,
                            (0) as gross_cost_price_loc,
                            
                            (0) as principal_invested,
                            (0) as principal_invested_loc,
                            
                            (0) as amount_invested,
                            (0) as amount_invested_loc,
                            
                            (0) as principal_invested_fixed,
                            (0) as principal_invested_fixed_loc,
                            
                            (0) as amount_invested_fixed,
                            (0) as amount_invested_fixed_loc,
                                
                            (0) as position_return,
                            (0) as position_return_loc,
                            (0) as net_position_return,
                            (0) as net_position_return_loc,
                            
                            (0) as position_return_fixed,
                            (0) as position_return_fixed_loc,
                            (0) as net_position_return_fixed,
                            (0) as net_position_return_fixed_loc,
                            
                            (0) as time_invested,
                            
                            (0) as ytm,
                            (0) as modified_duration,
                            (0) as ytm_at_cost,
                            (0) as return_annually,
                            (0) as return_annually_fixed,
                            
                            (0) as principal_opened,
                            (0) as carry_opened,
                            (0) as overheads_opened,
                            (0) as total_opened,
                            
                            (0) as principal_closed,
                            (0) as carry_closed,
                            (0) as overheads_closed,
                            (0) as total_closed,
                            
                            (0) as principal_fx_opened,
                            (0) as carry_fx_opened,
                            (0) as overheads_fx_opened,
                            (0) as total_fx_opened,
                            
                            (0) as principal_fx_closed,
                            (0) as carry_fx_closed,
                            (0) as overheads_fx_closed,
                            (0) as total_fx_closed,
                            
                            (0) as principal_fixed_opened,
                            (0) as carry_fixed_opened,
                            (0) as overheads_fixed_opened,
                            (0) as total_fixed_opened,
                            
                            (0) as principal_fixed_closed,
                            (0) as carry_fixed_closed,
                            (0) as overheads_fixed_closed,
                            (0) as total_fixed_closed,
                            
                            -- loc
                            
                            (0) as principal_opened_loc,
                            (0) as carry_opened_loc,
                            (0) as overheads_opened_loc,
                            (0) as total_opened_loc,
                            
                            (0) as principal_closed_loc,
                            (0) as carry_closed_loc,
                            (0) as overheads_closed_loc,
                            (0) as total_closed_loc,
                            
                            (0) as principal_fx_opened_loc,
                            (0) as carry_fx_opened_loc,
                            (0) as overheads_fx_opened_loc,
                            (0) as total_fx_opened_loc,
                            
                            (0) as principal_fx_closed_loc,
                            (0) as carry_fx_closed_loc,
                            (0) as overheads_fx_closed_loc,
                            (0) as total_fx_closed_loc,
                            
                            (0) as principal_fixed_opened_loc,
                            (0) as carry_fixed_opened_loc,
                            (0) as overheads_fixed_opened_loc,
                            (0) as total_fixed_opened_loc,
                            
                            (0) as principal_fixed_closed_loc,
                            (0) as carry_fixed_closed_loc,
                            (0) as overheads_fixed_closed_loc,
                            (0) as total_fixed_closed_loc
                            
                        from (
                            select 
                        
                            instrument_id,
                            {consolidated_position_columns}
                            
                            position_size,
                            case when coalesce(factor,1) = 0
                                    then position_size
                                    else
                                        position_size / coalesce(factor,1)
                            end as nominal_position_size,
    
                            (1) as item_type,
                            ('Instrument') as item_type_name,
                            
                            (principal_price) as price,
                            (pch_fx_rate) as fx_rate,
        
                            name,
                            short_name,
                            user_code,
        
                            pricing_currency_id,
                            (pch_fx_rate) as instrument_pricing_currency_fx_rate,
                            (ach_fx_rate) as instrument_accrued_currency_fx_rate,
                            
                            instrument_class_id,
                            co_directional_exposure_currency_id,
                            counter_directional_exposure_currency_id,
                            
                            exposure_calculation_model_id,
                            long_underlying_exposure_id,
                            short_underlying_exposure_id,
    
                            has_second_exposure_currency,
        
                            case when pricing_currency_id = {report_currency_id}
                                   then 1
                               else
                                   (rep_cur_fx/pch_fx_rate)
                            end as cross_loc_prc_fx,
        
                            (principal_price) as instrument_principal_price,
                            (accrued_price) as instrument_accrued_price,
                            (factor) as instrument_factor,
                            (ytm) as instrument_ytm,
                            
                            case when coalesce(yesterday_principal_price,0) = 0
                                    then 0
                                    else
                                        (principal_price - yesterday_principal_price) / yesterday_principal_price
                            end as daily_price_change,
                        
                            
                            (long_delta) as instrument_long_delta,
                            (short_delta) as instrument_short_delta,
        
                            (position_size * principal_price * price_multiplier * pch_fx_rate + (position_size * accrued_price * ach_fx_rate * 1 * accrued_multiplier)) as market_value,
                            (position_size * principal_price * price_multiplier * pch_fx_rate + (position_size * accrued_price * ach_fx_rate * 1 * accrued_multiplier)) as exposure,
    
                            -(position_size * principal_price * price_multiplier * pch_fx_rate + (position_size * accrued_price * ach_fx_rate * 1 * accrued_multiplier)) as exposure_2,
                            
                            /* Position * (Price * Multiplier * Long Delta * Pricing to Exposure FX Rate + Accrued * Multiplier * Accrued to Exposure FX Rate) */
                            (position_size * principal_price * price_multiplier * pch_fx_rate * long_delta + (position_size * accrued_price * ach_fx_rate * 1 * accrued_multiplier)) as exposure_delta_adjusted,
                            
                            (0) as exposure_long_underlying_zero,
                            (underlying_long_multiplier * lui_principal_price * lui_price_multiplier + underlying_long_multiplier * lui_accrued_price * lui_accrued_multiplier) as exposure_long_underlying_price,
                            (underlying_long_multiplier * long_delta * lui_principal_price * lui_price_multiplier + underlying_long_multiplier * lui_accrued_price * lui_accrued_multiplier) as exposure_long_underlying_price_delta,
                            (underlying_long_multiplier * ec1_fx_rate) as exposure_long_underlying_fx_rate,
                            (underlying_long_multiplier * long_delta * ec1_fx_rate) as exposure_long_underlying_fx_rate_delta,
                            
                            /*Market Value Long Underlying Exposure
                            1) "Zero":
                            =0
                            
                            2) "Long Underlying Instrument Price Exposure":
                             Long Underlying Multiplier* [Long Underlying Instrument].[Price] * [Long Underlying Instrument].[Price Multiplier] + Long Underlying Multiplier * [Long Underlying Instrument].[Accrued] * [Long Underlying Instrument].[Accrued Multiplier]
    
                            
                            3) "Long Underlying Instrument Price Delta-adjusted Exposure":
                            Long Underlying Multiplier * Long Delta * [Long Underlying Instrument].[Price] * [Long Underlying Instrument].[Price Multiplier] + Long Underlying Multiplier * [Long Underlying Instrument].[Accrued] * [Long Underlying Instrument].[Accrued Multiplier]
    
                            4) "Long Underlying Currency FX Rate Exposure": 
                             Long Underlying Multiplier * [Long Underlying Currency].[FX Rate]
                            
                            5) "Long Underlying Currency FX Rate Delta-adjusted Exposure": 
                            Long Underlying Multiplier * Long Delta * [Long Underlying Currency].[FX Rate]
                            
                            */
                            
                            (0) as exposure_short_underlying_zero,
                            (underlying_short_multiplier * sui_principal_price * sui_price_multiplier + underlying_short_multiplier * sui_accrued_price * sui_accrued_multiplier) as exposure_short_underlying_price,
                            (underlying_short_multiplier * short_delta * sui_principal_price * sui_price_multiplier + underlying_short_multiplier * sui_accrued_price * sui_accrued_multiplier) as exposure_short_underlying_price_delta,
                            (underlying_short_multiplier * ec1_fx_rate) as exposure_short_underlying_fx_rate,
                            (underlying_short_multiplier * short_delta * ec1_fx_rate) as exposure_short_underlying_fx_rate_delta,
                            
                            price_multiplier,
                            pch_fx_rate,
                            rep_cur_fx,
                            ec1_fx_rate,
                            ec2_fx_rate
                            
                        from (
                            select
                                instrument_id,
                                {consolidated_position_columns}
                                
                                position_size,
                                
                                i.name,
                                i.short_name,
                                i.user_code,
                                i.pricing_currency_id,
                                i.price_multiplier,
                                i.accrued_multiplier,
                                
                                i.exposure_calculation_model_id,
                                i.underlying_long_multiplier,
                                i.underlying_short_multiplier,
                                
                                i.co_directional_exposure_currency_id,
                                i.counter_directional_exposure_currency_id,
                                
                                i.long_underlying_exposure_id,
                                i.short_underlying_exposure_id,
                                
                                it.instrument_class_id,
    
                                it.has_second_exposure_currency,
                                
                                
                                (lui.price_multiplier) as lui_price_multiplier,
                                (lui.accrued_multiplier) as lui_accrued_multiplier,
                                
                                (sui.price_multiplier) as sui_price_multiplier,
                                (sui.accrued_multiplier) as sui_accrued_multiplier,
                                
                                (select 
                                    principal_price
                                from instruments_pricehistory
                                where 
                                    instrument_id=lui.id and 
                                    date = '{report_date}' and
                                    pricing_policy_id = {pricing_policy_id})
                                as lui_principal_price,
                                
                                (select 
                                    accrued_price
                                from instruments_pricehistory
                                where 
                                    instrument_id=lui.id and 
                                    date = '{report_date}' and
                                    pricing_policy_id = {pricing_policy_id})
                                as lui_accrued_price,
                                
                                (select 
                                    principal_price
                                from instruments_pricehistory
                                where 
                                    instrument_id=sui.id and 
                                    date = '{report_date}' and
                                    pricing_policy_id = {pricing_policy_id})
                                as sui_principal_price,
                                
                                (select 
                                    accrued_price
                                from instruments_pricehistory
                                where 
                                    instrument_id=sui.id and 
                                    date = '{report_date}' and
                                    pricing_policy_id = {pricing_policy_id})
                                as sui_accrued_price,
                                
                                case when i.co_directional_exposure_currency_id = {report_currency_id}
                                            then 1
                                        else
                                            (select
                                                 fx_rate
                                             from currencies_currencyhistory
                                             where
                                                     currency_id = i.co_directional_exposure_currency_id and
                                                     date = '{report_date}' and
                                                     pricing_policy_id = {pricing_policy_id}
                                            )
                                       end as ec1_fx_rate,
    
                                   case when i.counter_directional_exposure_currency_id = {report_currency_id}
                                            then 1
                                        else
                                            (select
                                                 fx_rate
                                             from currencies_currencyhistory
                                             where
                                                     currency_id = i.counter_directional_exposure_currency_id and
                                                     date = '{report_date}' and
                                                     pricing_policy_id = {pricing_policy_id}
                                            )
                                    end as ec2_fx_rate,
                                
                                case
                                       when {report_currency_id} = {default_currency_id}
                                           then 1
                                       else
                                           (select fx_rate
                                            from currencies_currencyhistory c_ch
                                            where date = '{report_date}'
                                              and c_ch.currency_id = {report_currency_id}
                                              and c_ch.pricing_policy_id = {pricing_policy_id}
                                            limit 1)
                                end as rep_cur_fx,
                                
                                case when i.pricing_currency_id = {default_currency_id}
                                    then 1
                                    else
                                        (select
                                    fx_rate
                                 from currencies_currencyhistory
                                 where
                                    currency_id = i.pricing_currency_id and
                                    date = '{report_date}' and
                                    pricing_policy_id = {pricing_policy_id}
                                )
                                end as pch_fx_rate,
                                
                                case when i.accrued_currency_id = {default_currency_id}
                                    then 1
                                    else
                                        (select
                                    fx_rate
                                 from currencies_currencyhistory
                                 where
                                    currency_id = i.accrued_currency_id and
                                    date = '{report_date}' and
                                    pricing_policy_id = {pricing_policy_id}
                                )
                                end as ach_fx_rate,
                                    
                                (select 
                                    principal_price
                                from instruments_pricehistory
                                where 
                                    instrument_id=i.id and 
                                    date = '{report_date}' and
                                    pricing_policy_id = {pricing_policy_id})
                                as principal_price,
                                
                                (select 
                                    principal_price
                                from instruments_pricehistory
                                where 
                                    instrument_id=i.id and 
                                    date = '{bday_yesterday_of_report_date}' and
                                    pricing_policy_id = {pricing_policy_id})
                                as yesterday_principal_price,
                                
                                (select 
                                    factor
                                from instruments_pricehistory
                                where 
                                    instrument_id=i.id and 
                                    date = '{report_date}' and
                                    pricing_policy_id = {pricing_policy_id})
                                as factor,
                                
                                (select 
                                    ytm
                                from instruments_pricehistory
                                where 
                                    instrument_id=i.id and 
                                    date = '{report_date}' and
                                    pricing_policy_id = {pricing_policy_id})
                                as ytm,
                                
                                (select 
                                    accrued_price
                                from instruments_pricehistory
                                where 
                                    instrument_id=i.id and 
                                    date = '{report_date}' and
                                    pricing_policy_id = {pricing_policy_id} )
                                as accrued_price,
                                
                                (select 
                                    long_delta
                                from instruments_pricehistory
                                where 
                                    instrument_id=i.id and 
                                    date = '{report_date}' and
                                    pricing_policy_id = {pricing_policy_id})
                                as long_delta,
                                
                                (select 
                                    short_delta
                                from instruments_pricehistory
                                where 
                                    instrument_id=i.id and 
                                    date = '{report_date}' and
                                    pricing_policy_id = {pricing_policy_id})
                                as short_delta
                                
                            from
                                (select
                                  {consolidated_position_columns}
                                  instrument_id,
                                  SUM(position_size_with_sign) as position_size
                                from filtered_transactions 
                                where min_date <= '{report_date}' 
                                and master_user_id = {master_user_id}
                                and transaction_class_id in (1,2,14)
                                group by
                                  {consolidated_position_columns}
                                  instrument_id) as t
                            left join instruments_instrument as i
                            ON instrument_id = i.id
                            left join instruments_instrument as lui
                            ON i.long_underlying_instrument_id = lui.id
                            left join instruments_instrument as sui
                            ON i.short_underlying_instrument_id = sui.id
                            left join instruments_instrumenttype as it
                            ON i.instrument_type_id = it.id
                            ) as grouped
                        where position_size != 0
                        ) as balance_q
                    
                    ) as joined_positions
                """

    return query
