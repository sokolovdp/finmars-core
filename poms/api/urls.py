from __future__ import unicode_literals

from django.conf import settings
from django.conf.urls import url, include
from rest_framework import routers

import poms.accounts.views as accounts
import poms.api.views as api
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

router.register(r'users/user-register', users.UserRegisterViewSet, 'userregister')
router.register(r'users/user', users.UserViewSet)
router.register(r'users/master-user', users.MasterUserViewSet)
router.register(r'users/member', users.MemberViewSet)
router.register(r'users/group', users.GroupViewSet)
router.register(r'users/language', api.LanguageViewSet, 'language')
router.register(r'users/timezone', api.TimezoneViewSet, 'timezone')

router.register(r'accounts/account-type', accounts.AccountTypeViewSet)
router.register(r'accounts/account-attribute-type', accounts.AccountAttributeTypeViewSet)
router.register(r'accounts/account-attribute-type2', accounts.AccountAttributeType2ViewSet, 'accountattributetype2')
router.register(r'accounts/account-classifier', accounts.AccountClassifierViewSet)
router.register(r'accounts/account', accounts.AccountViewSet)

router.register(r'counterparties/counterparty-attribute-type', counterparties.CounterpartyAttributeTypeViewSet)
router.register(r'counterparties/counterparty-attribute-type2', counterparties.CounterpartyAttributeType2ViewSet, 'counterpartyattributetype2')
router.register(r'counterparties/counterparty-classifier', counterparties.CounterpartyClassifierViewSet)
router.register(r'counterparties/counterparty-group', counterparties.CounterpartyGroupViewSet)
router.register(r'counterparties/counterparty', counterparties.CounterpartyViewSet)

router.register(r'counterparties/responsible-attribute-type', counterparties.ResponsibleAttributeTypeViewSet)
router.register(r'counterparties/responsible-attribute-type2', counterparties.ResponsibleAttributeType2ViewSet, 'responsibleattributetype2')
router.register(r'counterparties/responsible-classifier', counterparties.ResponsibleClassifierViewSet)
router.register(r'counterparties/responsible-group', counterparties.ResponsibleGroupViewSet)
router.register(r'counterparties/responsible', counterparties.ResponsibleViewSet)

router.register(r'currencies/currency', currencies.CurrencyViewSet)
router.register(r'currencies/currency-history', currencies.CurrencyHistoryViewSet)

router.register(r'instruments/instrument-class', instruments.InstrumentClassViewSet)
router.register(r'instruments/daily-pricing-model', instruments.DailyPricingModelViewSet)
router.register(r'instruments/accrual-calculation-model', instruments.AccrualCalculationModelClassViewSet)
router.register(r'instruments/payment-size-detail', instruments.PaymentSizeDetailViewSet)
router.register(r'instruments/periodicity', instruments.PeriodicityViewSet)
router.register(r'instruments/cost-method', instruments.CostMethodViewSet)
router.register(r'instruments/pricing-policy', instruments.PricingPolicyViewSet)

router.register(r'instruments/event-schedule-config', instruments.EventScheduleConfigViewSet)

router.register(r'instruments/instrument-type', instruments.InstrumentTypeViewSet)
router.register(r'instruments/instrument-attribute-type', instruments.InstrumentAttributeTypeViewSet)
router.register(r'instruments/instrument-classifier', instruments.InstrumentClassifierViewSet)
router.register(r'instruments/instrument', instruments.InstrumentViewSet)
router.register(r'instruments/price-history', instruments.PriceHistoryViewSet)

router.register(r'portfolios/portfolio-attribute-type', portfolios.PortfolioAttributeTypeViewSet)
router.register(r'portfolios/portfolio-classifier', portfolios.PortfolioClassifierViewSet)
router.register(r'portfolios/portfolio', portfolios.PortfolioViewSet)

router.register(r'strategies/1/group', strategies.Strategy1GroupViewSet)
router.register(r'strategies/1/subgroup', strategies.Strategy1SubgroupViewSet)
router.register(r'strategies/1/strategy', strategies.Strategy1ViewSet)

router.register(r'strategies/2/group', strategies.Strategy2GroupViewSet)
router.register(r'strategies/2/subgroup', strategies.Strategy2SubgroupViewSet)
router.register(r'strategies/2/strategy', strategies.Strategy2ViewSet)

router.register(r'strategies/3/group', strategies.Strategy3GroupViewSet)
router.register(r'strategies/3/subgroup', strategies.Strategy3SubgroupViewSet)
router.register(r'strategies/3/strategy', strategies.Strategy3ViewSet)

router.register(r'tags/tag', tags.TagViewSet)

router.register(r'transactions/event-class', transactions.EventClassViewSet)
router.register(r'transactions/notification-class', transactions.NotificationClassViewSet)
router.register(r'transactions/transaction-class', transactions.TransactionClassViewSet)

router.register(r'transactions/transaction-type-group', transactions.TransactionTypeGroupViewSet)
router.register(r'transactions/transaction-type', transactions.TransactionTypeViewSet)
router.register(r'transactions/transaction-attribute-type', transactions.TransactionAttributeTypeViewSet)
router.register(r'transactions/transaction-classifier', transactions.TransactionClassifierViewSet)
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
router.register(r'chats/thread-group', chats.ThreadGroupViewSet)
router.register(r'chats/thread', chats.ThreadViewSet)
router.register(r'chats/message', chats.MessageViewSet)
router.register(r'chats/direct-message', chats.DirectMessageViewSet)

router.register(r'security/http-session', sessions.SessionViewSet)
router.register(r'audit/auth-log', audit.AuthLogViewSet)
router.register(r'audit/history', audit.ObjectHistory4ViewSet)

router.register(r'import/config', integrations.ImportConfigViewSet)

router.register(r'import/provider', integrations.ProviderClassViewSet)
router.register(r'import/factor-schedule-download-method', integrations.FactorScheduleDownloadMethodViewSet)
router.register(r'import/accrual-schedule-download-method', integrations.AccrualScheduleDownloadMethodViewSet)

router.register(r'import/instrument-scheme', integrations.InstrumentDownloadSchemeViewSet)
router.register(r'import/price-download-scheme', integrations.PriceDownloadSchemeViewSet)

router.register(r'import/currency-mapping', integrations.CurrencyMappingViewSet)
router.register(r'import/instrument-type-mapping', integrations.InstrumentTypeMappingViewSet)
router.register(r'import/instrument-attribute-value-mapping', integrations.InstrumentAttributeValueMappingViewSet)
router.register(r'import/accrual-calculation-model-mapping', integrations.AccrualCalculationModelMappingViewSet)
router.register(r'import/periodicity-mapping', integrations.PeriodicityMappingViewSet)

router.register(r'import/file/instrument', integrations.ImportFileInstrumentViewSet, 'importfileinstrument')

router.register(r'import/instrument', integrations.ImportInstrumentViewSet, 'importinstrument')
router.register(r'import/pricing', integrations.ImportPricingViewSet, 'importpricing')
router.register(r'import/pricing-automated-schedule', integrations.PricingAutomatedScheduleViewSet)

router.register(r'import/task', integrations.TaskViewSet)

router.register(r'utils/expression', api.ExpressionViewSet, 'expression')

urlpatterns = [
    url(r'^v1/', include(router.urls, namespace='v1')),
]

if settings.DEV:
    urlpatterns += [
        url(r'^dev/auth/', include('rest_framework.urls', namespace='rest_framework')),
    ]

if 'rest_framework_swagger' in settings.INSTALLED_APPS:
    urlpatterns += [
        url(r'^schema/', api.SchemaViewSet.as_view()),
    ]
