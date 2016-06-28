from __future__ import unicode_literals

from poms.common.tests import BaseApiWithPermissionTestCase, BaseApiWithTagsTestCase, BaseNamedModelTestCase, \
    ABSTRACT_TESTS
from poms.strategies.models import Strategy1, Strategy2, Strategy3


def load_tests(loader, standard_tests, pattern):
    from poms.common.tests import load_tests as t
    return t(loader, standard_tests, pattern)


class BaseStrategyApiTestCase(BaseNamedModelTestCase, BaseApiWithPermissionTestCase, BaseApiWithTagsTestCase):
    model = None
    strategy_code = None

    def setUp(self):
        super(BaseStrategyApiTestCase, self).setUp()

        self._url_list = '/api/v1/strategies/strategy%s/' % self.strategy_code
        self._url_object = '/api/v1/strategies/strategy%s/%%s/' % self.strategy_code
        self._change_permission = 'change_strategy%s' % self.strategy_code

    def _create_obj(self, name='strategy'):
        return self.create_strategy(self.model, name, 'a')

    def _get_obj(self, name='strategy'):
        return self.get_strategy(self.model, name, 'a')


ABSTRACT_TESTS.append(BaseStrategyApiTestCase)


class Strategy1ApiTestCase(BaseStrategyApiTestCase):
    model = Strategy1
    strategy_code = 1


class Strategy2ApiTestCase(BaseStrategyApiTestCase):
    model = Strategy2
    strategy_code = 2


class Strategy3ApiTestCase(BaseStrategyApiTestCase):
    model = Strategy3
    strategy_code = 3
