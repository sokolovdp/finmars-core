from __future__ import unicode_literals

from django.conf import settings
from django.conf.urls import url, include
from rest_framework import routers

import poms.accounts.views as accounts
import poms.audit.views as audit
import poms.chats.views as chats
import poms.counterparties.views as counterparties
import poms.currencies.views as currencies
import poms.http_sessions.views as sessions
import poms.instruments.views as instruments
import poms.integrations.views as integrations
import poms.notifications.views as notifications
import poms.portfolios.views as portfolios
import poms.reports.views as reports
import poms.strategies.views as strategies
import poms.tags.views as tags
import poms.transactions.views as transactions
import poms.ui.views as ui
import poms.users.views as users

router = routers.DefaultRouter()
router.register(r'users/login', users.LoginViewSet, 'login')
router.register(r'users/logout', users.LogoutViewSet, 'logout')
router.register(r'users/ping', users.PingViewSet, "ping")
router.register(r'users/protected-ping', users.ProtectedPingViewSet, "protectedping")

router.register(r'users/user', users.UserViewSet)
router.register(r'users/master-user', users.MasterUserViewSet)
router.register(r'users/member', users.MemberViewSet)
router.register(r'users/group', users.GroupViewSet)

# router.register(r'accounts/account-classifier/node', accounts.AccountClassifierNodeViewSet, 'accountclassifiernode')
# router.register(r'accounts/account-classifier', accounts.AccountClassifierViewSet)
router.register(r'accounts/account-type', accounts.AccountTypeViewSet)
router.register(r'accounts/account-attribute-type', accounts.AccountAttributeTypeViewSet)
router.register(r'accounts/account', accounts.AccountViewSet)

# router.register(r'counterparties/counterparty-classifier/node', counterparties.CounterpartyClassifierNodeViewSet,
#                 'counterpartyclassifiernode')
# router.register(r'counterparties/counterparty-classifier', counterparties.CounterpartyClassifierViewSet)
router.register(r'counterparties/counterparty-attribute-type', counterparties.CounterpartyAttributeTypeViewSet)
router.register(r'counterparties/counterparty', counterparties.CounterpartyViewSet)

# router.register(r'counterparties/responsible-classifier/node', counterparties.ResponsibleClassifierNodeViewSet,
#                 'responsibleclassifiernode')
# router.register(r'counterparties/responsible-classifier', counterparties.ResponsibleClassifierViewSet)
router.register(r'counterparties/responsible-attribute-type', counterparties.ResponsibleAttributeTypeViewSet)
router.register(r'counterparties/responsible', counterparties.ResponsibleViewSet)

router.register(r'currencies/currency', currencies.CurrencyViewSet)
router.register(r'currencies/currency-history', currencies.CurrencyHistoryViewSet)

router.register(r'instruments/instrument-class', instruments.InstrumentClassViewSet)
router.register(r'instruments/daily-pricing-model', instruments.DailyPricingModelViewSet)
router.register(r'instruments/accrual-calculation-model', instruments.AccrualCalculationModelClassViewSet)
router.register(r'instruments/payment-size-detail', instruments.PaymentSizeDetailViewSet)
router.register(r'instruments/periodicity-period', instruments.PeriodicityPeriodViewSet)
router.register(r'instruments/cost-method', instruments.CostMethodViewSet)
router.register(r'instruments/pricing-policy', instruments.PricingPolicyViewSet)
router.register(r'instruments/price-download-mode', instruments.PriceDownloadModeViewSet)
# router.register(r'instruments/instrument-classifier/node', instruments.InstrumentClassifierNodeViewSet,
#                 'instrumentclassifiernode')
# router.register(r'instruments/instrument-classifier', instruments.InstrumentClassifierViewSet)
router.register(r'instruments/instrument-type', instruments.InstrumentTypeViewSet)
router.register(r'instruments/instrument-attribute-type', instruments.InstrumentAttributeTypeViewSet)
router.register(r'instruments/instrument', instruments.InstrumentViewSet)
router.register(r'instruments/price-history', instruments.PriceHistoryViewSet)
# router.register(r'instruments/manual-pricing-formula', instruments.ManualPricingFormulaViewSet)
# router.register(r'instruments/accrual-calculation-schedule', instruments.AccrualCalculationScheduleViewSet)
# router.register(r'instruments/instrument-factor-schedule', instruments.InstrumentFactorScheduleViewSet)
# router.register(r'instruments/event-schedule', instruments.EventScheduleViewSet)

# router.register(r'portfolios/portfolio-classifier/node', portfolios.PortfolioClassifierNodeViewSet,
#                 'portfolioclassifiernode')
# router.register(r'portfolios/portfolio-classifier', portfolios.PortfolioClassifierViewSet)
router.register(r'portfolios/portfolio-attribute-type', portfolios.PortfolioAttributeTypeViewSet)
router.register(r'portfolios/portfolio', portfolios.PortfolioViewSet)

# router.register(r'strategies/strategy/node', strategies.StrategyNodeViewSet, 'strategynode')
# router.register(r'strategies/strategy', strategies.StrategyViewSet)
router.register(r'strategies/strategy1/node', strategies.Strategy1NodeViewSet, 'strategy1node')
router.register(r'strategies/strategy1', strategies.Strategy1ViewSet)
router.register(r'strategies/strategy2/node', strategies.Strategy2NodeViewSet, 'strategy2node')
router.register(r'strategies/strategy2', strategies.Strategy2ViewSet)
router.register(r'strategies/strategy3/node', strategies.Strategy3NodeViewSet, 'strategy3node')
router.register(r'strategies/strategy3', strategies.Strategy3ViewSet)

router.register(r'tags/tag', tags.TagViewSet)

router.register(r'transactions/transaction-class', transactions.TransactionClassViewSet)
router.register(r'transactions/transaction-type-group', transactions.TransactionTypeGroupViewSet)
router.register(r'transactions/transaction-type', transactions.TransactionTypeViewSet)
router.register(r'transactions/transaction-attribute-type', transactions.TransactionAttributeTypeViewSet)
router.register(r'transactions/transaction', transactions.TransactionViewSet)
router.register(r'transactions/complex-transaction', transactions.ComplexTransactionViewSet)

router.register(r'ui/list-layout', ui.ListLayoutViewSet)
router.register(r'ui/edit-layout', ui.EditLayoutViewSet)
router.register(r'ui/template-list-layout', ui.TemplateListLayoutViewSet)
router.register(r'ui/template-edit-layout', ui.TemplateEditLayoutViewSet)

router.register(r'reports/balance', reports.BalanceReport2ViewSet, "balancereport2")
router.register(r'reports/pl', reports.PLReport2ViewSet, "plreport2")
router.register(r'reports/cost', reports.CostReport2ViewSet, "costreport2")
router.register(r'reports/ytm', reports.YTMReport2ViewSet, "ytmreport2")
router.register(r'reports/simple-multipliers', reports.SimpleMultipliersReport2ViewSet, "simplemultipliersreport2")

router.register(r'notifications/notification', notifications.NotificationViewSet)
# router.register(r'notifications/message', notifications.MessageViewSet, 'django-message')

# router.register(r'chats/thread-status', chats.ThreadStatusViewSet, 'chatthreadstatus')
router.register(r'chats/thread-group', chats.ThreadGroupViewSet, 'chatthreadgroup')
router.register(r'chats/thread', chats.ThreadViewSet, 'chatthread')
router.register(r'chats/message', chats.MessageViewSet, 'chatmessage')
router.register(r'chats/direct-message', chats.DirectMessageViewSet, 'chatdirectmessage')

router.register(r'security/http-session', sessions.SessionViewSet)
router.register(r'audit/auth-log', audit.AuthLogViewSet)
router.register(r'audit/history', audit.ObjectHistoryViewSet)

router.register(r'bloomberg/config', integrations.BloombergConfigViewSet)

router.register(r'import/instrument/mapping', integrations.InstrumentMappingViewSet)
router.register(r'import/instrument/file', integrations.InstrumentFileImportViewSet,
                'InstrumentFileImportViewSet')
router.register(r'import/instrument/bloomberg', integrations.InstrumentBloombergImportViewSet,
                'InstrumentBloombergImportViewSet')

urlpatterns = [
    url(r'^v1/', include(router.urls, namespace='v1')),
]

if settings.DEV:
    urlpatterns += [
        url(r'^dev/auth/', include('rest_framework.urls', namespace='rest_framework')),
    ]
