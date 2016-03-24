from __future__ import unicode_literals

from django.conf import settings
from django.conf.urls import patterns, url, include
from rest_framework import routers

import poms.accounts.views as accounts
import poms.api.views as views
import poms.audit.views as audit
import poms.counterparties.views as counterparties
import poms.currencies.views as currencies
import poms.http_sessions.views as sessions
import poms.instruments.views as instruments
import poms.portfolios.views as portfolios
import poms.transactions.views as transactions
import poms.strategies.views as strategies
import poms.users.views as users
import poms.reports.views as reports
import poms.notifications.views as notifications

router = routers.DefaultRouter()
router.register(r'users/login', users.LoginViewSet, 'LoginViewSet')
router.register(r'users/logout', users.LogoutViewSet, 'LogoutViewSet')
router.register(r'users/ping', views.PingViewSet, "ping")
router.register(r'users/protected-ping', views.ProtectedPingViewSet, "protectedping")

router.register(r'users/user', users.UserViewSet)
router.register(r'users/master-user', users.MasterUserViewSet)
router.register(r'users/member', users.MemberViewSet)
router.register(r'users/group', users.GroupViewSet)

router.register(r'notifications/notification', notifications.NotificationViewSet)

router.register(r'security/http-session', sessions.SessionViewSet)

router.register(r'audit/auth-log', audit.AuthLogEntryViewSet)

router.register(r'accounts/account-type', accounts.AccountTypeViewSet)
router.register(r'accounts/account-classifier', accounts.AccountClassifierViewSet)
router.register(r'accounts/account', accounts.AccountViewSet)

router.register(r'counterparties/counterparty-classifier', counterparties.CounterpartyClassifierViewSet)
router.register(r'counterparties/counterparty', counterparties.CounterpartyViewSet)
router.register(r'counterparties/responsible', counterparties.ResponsibleViewSet)

router.register(r'currencies/currency', currencies.CurrencyViewSet)
router.register(r'currencies/currency-history', currencies.CurrencyHistoryViewSet)

router.register(r'instruments/instrument-classifier', instruments.InstrumentClassifierViewSet)
router.register(r'instruments/instrument', instruments.InstrumentViewSet)
router.register(r'instruments/price-history', instruments.PriceHistoryViewSet)

router.register(r'portfolios/portfolio-classifier', portfolios.PortfolioClassifierViewSet)
router.register(r'portfolios/portfolio', portfolios.PortfolioViewSet)

router.register(r'transactions/transaction-class', transactions.TransactionClassViewSet)
router.register(r'transactions/transaction', transactions.TransactionViewSet)

router.register(r'strategies/strategy', strategies.StrategyViewSet)

router.register(r'reports/balance', reports.BalanceReportViewSet, "balancereport")
router.register(r'reports/pl', reports.PLReportViewSet, "plreport")
router.register(r'reports/cost', reports.CostReportViewSet, "costreport")
router.register(r'reports/ytm', reports.YTMReportViewSet, "ytmreport")
router.register(r'reports/simple-multipliers', reports.SimpleMultipliersReportViewSet, "simplemultipliersreport")

router.register(r'reports/v2/balance', reports.BalanceReport2ViewSet, "balancereport2")
router.register(r'reports/v2/pl', reports.PLReport2ViewSet, "plreport2")
router.register(r'reports/v2/cost', reports.CostReport2ViewSet, "costreport2")
router.register(r'reports/v2/ytm', reports.YTMReport2ViewSet, "ytmreport2")
router.register(r'reports/v2/simple-multipliers', reports.SimpleMultipliersReport2ViewSet, "simplemultipliersreport2")

# p = routers.DefaultRouter()
# p.register(r'users/login', users.LoginViewSet, 'LoginViewSet')
# p.register(r'users/logout', users.LogoutViewSet, 'LogoutViewSet')
# p.register(r'users/ping', views.PingViewSet, "ping")
# p.register(r'users/protected-ping', views.ProtectedPingViewSet, "protectedping")
# p.register(r'users/group', users.GroupViewSet)
# p.register(r'users/user', users.UserViewSet)
# p.register(r'users/master-user', users.MasterUserViewSet)
# p.register(r'users/member', users.MemberViewSet)
# p.register(r'security/http-session', sessions.SessionViewSet)
# p.register(r'audit/authlog', audit.AuthLogViewSet)
#
# mu = routers.DefaultRouter()
# mu.register(r'accounts/account-type', accounts.AccountTypeViewSet)
# mu.register(r'accounts/account-classifier', accounts.AccountClassifierViewSet)
# mu.register(r'accounts/account', accounts.AccountViewSet)
# mu.register(r'counterparties/counterparty-classifier', counterparties.CounterpartyClassifierViewSet)
# mu.register(r'counterparties/counterparty', counterparties.CounterpartyViewSet)
# mu.register(r'counterparties/responsible', counterparties.ResponsibleViewSet)
# mu.register(r'currencies/currency', currencies.CurrencyViewSet)
# mu.register(r'currencies/currency-history', currencies.CurrencyHistoryViewSet)
# mu.register(r'instruments/instrument-classifier', instruments.InstrumentClassifierViewSet)
# mu.register(r'instruments/instrument', instruments.InstrumentViewSet)
# mu.register(r'instruments/price-history', instruments.PriceHistoryViewSet)
# mu.register(r'portfolios/portfolio-classifier', portfolios.PortfolioClassifierViewSet)
# mu.register(r'portfolios/portfolio', portfolios.PortfolioViewSet)
# mu.register(r'transactions/transaction-class', transactions.TransactionClassViewSet)
# mu.register(r'transactions/transaction', transactions.TransactionViewSet)
# mu.register(r'strategies/strategy', strategies.StrategyViewSet)
# mu.register(r'reports/balance', reports.BalanceReportViewSet, "balancereport")
# mu.register(r'reports/pl', reports.PLReportViewSet, "plreport")
# mu.register(r'reports/cost', reports.CostReportViewSet, "costreport")
# mu.register(r'reports/ytm', reports.YTMReportViewSet, "ytmreport")
# mu.register(r'reports/simple-multipliers', reports.SimpleMultipliersReportViewSet, "simplemultipliersreport")
# mu.register(r'reports/v2/balance', reports.BalanceReport2ViewSet, "balancereport2")
# mu.register(r'reports/v2/pl', reports.PLReport2ViewSet, "plreport2")
# mu.register(r'reports/v2/cost', reports.CostReport2ViewSet, "costreport2")
# mu.register(r'reports/v2/ytm', reports.YTMReport2ViewSet, "ytmreport2")
# mu.register(r'reports/v2/simple-multipliers', reports.SimpleMultipliersReport2ViewSet, "simplemultipliersreport2")


urlpatterns = [
    url(r'^v1/', include(router.urls, namespace='v1')),


    # url(r'^v2/(?P<master_user>[0-9]+)/', include(mu.urls, namespace='v1')),
    # url(r'^v2/p/', include(p.urls, namespace='v1')),
]

if settings.DEV:
    urlpatterns += patterns('',
                            url(r'^dev/auth/', include('rest_framework.urls', namespace='rest_framework')),
                            )
