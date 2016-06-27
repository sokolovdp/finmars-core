from __future__ import unicode_literals

from poms.common.tests import BaseApiWithPermissionTestCase, BaseApiWithAttributesTestCase, \
    BaseAttributeTypeApiTestCase, BaseApiWithTagsTestCase, BaseNamedModelTestCase
from poms.counterparties.models import CounterpartyAttributeType, CounterpartyClassifier, Counterparty, \
    ResponsibleAttributeType, ResponsibleClassifier, Responsible


def load_tests(loader, standard_tests, pattern):
    from poms.common.tests import load_tests as t
    return t(loader, standard_tests, pattern)


class CounterpartyAttributeTypeApiTestCase(BaseAttributeTypeApiTestCase):
    model = CounterpartyAttributeType
    classifier_model = CounterpartyClassifier

    def setUp(self):
        super(CounterpartyAttributeTypeApiTestCase, self).setUp()

        self._url_list = '/api/v1/counterparties/counterparty-attribute-type/'
        self._url_object = '/api/v1/counterparties/counterparty-attribute-type/%s/'
        self._change_permission = 'change_counterpartyattributetype'


class CounterpartyApiTestCase(BaseNamedModelTestCase, BaseApiWithPermissionTestCase, BaseApiWithTagsTestCase,
                              BaseApiWithAttributesTestCase):
    model = Counterparty
    attribute_type_model = CounterpartyAttributeType
    classifier_model = CounterpartyClassifier

    def setUp(self):
        super(CounterpartyApiTestCase, self).setUp()

        self._url_list = '/api/v1/counterparties/counterparty/'
        self._url_object = '/api/v1/counterparties/counterparty/%s/'
        self._change_permission = 'change_counterparty'

    def _create_obj(self, name='counterparty'):
        return self.create_counterparty(name, 'a')

    def _get_obj(self, name='counterparty'):
        return self.get_counterparty(name, 'a')


class ResponsibleAttributeTypeApiTestCase(BaseAttributeTypeApiTestCase):
    model = ResponsibleAttributeType
    classifier_model = ResponsibleClassifier

    def setUp(self):
        super(ResponsibleAttributeTypeApiTestCase, self).setUp()

        self._url_list = '/api/v1/counterparties/responsible-attribute-type/'
        self._url_object = '/api/v1/counterparties/responsible-attribute-type/%s/'
        self._change_permission = 'change_responsibleattributetype'


class ResponsibleApiTestCase(BaseNamedModelTestCase, BaseApiWithPermissionTestCase, BaseApiWithTagsTestCase,
                             BaseApiWithAttributesTestCase):
    model = Responsible
    attribute_type_model = ResponsibleAttributeType
    classifier_model = ResponsibleClassifier

    def setUp(self):
        super(ResponsibleApiTestCase, self).setUp()

        self._url_list = '/api/v1/counterparties/responsible/'
        self._url_object = '/api/v1/counterparties/responsible/%s/'
        self._change_permission = 'change_responsible'

    def _create_obj(self, name='responsible'):
        return self.create_counterparty(name, 'a')

    def _get_obj(self, name='responsible'):
        return self.get_counterparty(name, 'a')
