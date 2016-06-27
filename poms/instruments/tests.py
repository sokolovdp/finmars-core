from __future__ import unicode_literals

from django.conf import settings
from rest_framework import status

from poms.common.tests import BaseApiWithPermissionTestCase, BaseApiWithAttributesTestCase, \
    BaseAttributeTypeApiTestCase, BaseApiWithTagsTestCase, BaseNamedModelTestCase
from poms.instruments.models import InstrumentType, InstrumentAttributeType, InstrumentClassifier, Instrument, \
    InstrumentClass
from poms.obj_perms.utils import get_perms_codename


def load_tests(loader, standard_tests, pattern):
    from poms.common.tests import load_tests as t
    return t(loader, standard_tests, pattern)


class InstrumentTypeApiTestCase(BaseNamedModelTestCase, BaseApiWithPermissionTestCase, BaseApiWithTagsTestCase):
    model = InstrumentType

    def setUp(self):
        super(InstrumentTypeApiTestCase, self).setUp()

        self._url_list = '/api/v1/instruments/instrument-type/'
        self._url_object = '/api/v1/instruments/instrument-type/%s/'
        self._change_permission = 'change_instrumenttype'

    def _create_obj(self, name='instrument_type'):
        return self.create_instrument_type(name, 'a')

    def _get_obj(self, name='instrument_type'):
        return self.get_instrument_type(name, 'a')

    def _make_new_data(self, **kwargs):
        kwargs['instrument_class'] = kwargs.get('instrument_class', InstrumentClass.GENERAL)
        data = super(InstrumentTypeApiTestCase, self)._make_new_data(**kwargs)
        return data


class InstrumentAttributeTypeApiTestCase(BaseAttributeTypeApiTestCase):
    model = InstrumentAttributeType
    classifier_model = InstrumentClassifier

    def setUp(self):
        super(InstrumentAttributeTypeApiTestCase, self).setUp()

        self._url_list = '/api/v1/instruments/instrument-attribute-type/'
        self._url_object = '/api/v1/instruments/instrument-attribute-type/%s/'
        self._change_permission = 'change_instrumentattributetype'


class InstrumentApiTestCase(BaseNamedModelTestCase, BaseApiWithPermissionTestCase, BaseApiWithTagsTestCase,
                            BaseApiWithAttributesTestCase):
    model = Instrument
    attribute_type_model = InstrumentAttributeType
    classifier_model = InstrumentClassifier

    def setUp(self):
        super(InstrumentApiTestCase, self).setUp()

        self._url_list = '/api/v1/instruments/instrument/'
        self._url_object = '/api/v1/instruments/instrument/%s/'
        self._change_permission = 'change_instrument'

        self.type_def = self.create_instrument_type('-', 'a')
        self.assign_perms(self.type_def, 'a', users=['a0', 'a1', 'a2'], groups=['g1', 'g2'],
                          perms=get_perms_codename(self.type_def, ['change', 'view']))

        self.type1 = self.create_instrument_type('type1', 'a')
        self.type2_a1 = self.create_instrument_type('type2_a1', 'a')
        self.assign_perms(self.type2_a1, 'a', users=['a1'], groups=[])
        self.type3_g2 = self.create_instrument_type('type3_g2', 'a')
        self.assign_perms(self.type3_g2, 'a', groups=['g2'])

    def _create_obj(self, name='instrument', instrument_type=None, pricing_currency=None, accrued_currency=None):
        instrument_type = instrument_type or self.type_def
        pricing_currency = pricing_currency or self.get_currency(settings.CURRENCY_CODE, 'a')
        accrued_currency = accrued_currency or self.get_currency(settings.CURRENCY_CODE, 'a')
        return self.create_instrument(name, 'a', instrument_type=instrument_type, pricing_currency=pricing_currency,
                                      accrued_currency=accrued_currency)

    def _get_obj(self, name='instrument'):
        return self.get_instrument(name, 'a')

    def _make_new_data(self, **kwargs):
        instrument_type = self.get_instrument_type(kwargs.get('instrument_type', '-'), 'a')
        kwargs['instrument_type'] = instrument_type.id
        pricing_currency = self.get_currency(kwargs.get('pricing_currency', settings.CURRENCY_CODE), 'a')
        kwargs['pricing_currency'] = pricing_currency.id
        accrued_currency = self.get_currency(kwargs.get('accrued_currency', settings.CURRENCY_CODE), 'a')
        kwargs['accrued_currency'] = accrued_currency.id
        data = super(InstrumentApiTestCase, self)._make_new_data(**kwargs)
        return data

    def test_add_by_user_with_type_without_perms(self):
        data = self._make_new_data(instrument_type='type1')
        response = self._add('a1', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_by_group_with_type_without_perms(self):
        data = self._make_new_data(instrument_type='type1')
        response = self._add('a2', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
