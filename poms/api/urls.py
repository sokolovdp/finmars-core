from __future__ import unicode_literals

from django.conf import settings
from django.conf.urls import patterns, url, include
from rest_framework import routers

import poms.audit.views as audit
import poms.http_sessions.views as sessions
import poms.accounts.views as accounts
import poms.currencies.views as currencies
import poms.instruments.views as instruments
import poms.users.views as users
import poms.reports.views as reports

router = routers.DefaultRouter()
router.register(r'users/login', users.LoginViewSet, 'LoginViewSet')
router.register(r'users/logout', users.LogoutViewSet, 'LogoutViewSet')
# router.register(r'auth/obtain-token', auth.ObtainAuthTokenViewSet, 'ObtainAuthTokenViewSet')

router.register(r'security/http-session', sessions.SessionViewSet)

router.register(r'audit/authlog', audit.AuthLogViewSet)

router.register(r'accounts/account', accounts.AccountViewSet)

router.register(r'instruments/instrument-classifier', instruments.InstrumentClassifierViewSet)

router.register(r'currencies/currency', currencies.CurrencyViewSet)
router.register(r'currencies/currency-history', currencies.CurrencyHistoryViewSet)

router.register(r'reports/balance', reports.BalanceReportViewSet, "balancereport")

urlpatterns = router.urls

if settings.DEV:
    urlpatterns += patterns('',
                            url(r'^dev/auth/', include('rest_framework.urls', namespace='rest_framework')),
                            )
