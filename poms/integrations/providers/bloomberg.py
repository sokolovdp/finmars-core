import base64
import logging
import os
import pprint
import uuid
from datetime import timedelta, date, datetime
from tempfile import NamedTemporaryFile
from time import sleep

import requests
import six
from OpenSSL import crypto
from dateutil import parser
from django.conf import settings
from django.db import IntegrityError
from suds.client import Client
from suds.transport import Reply
from suds.transport.http import HttpAuthenticated

from poms.common import formula
from poms.currencies.models import CurrencyHistory
from poms.instruments.models import PriceHistory
from poms.integrations.models import Task

__author__ = 'alyakhov'

_l = logging.getLogger('poms.integrations.providers.bloomberg')


# _l = getLogger(__name__)


class BloombergException(Exception):
    pass


class BloombergTransportException(BloombergException):
    pass


def get_certs_from_file(p12cert, password):
    """
    Convert pkcs#12 bloomberg certificate into pem format certificates, used by authorized DLWS access.
    @param p12cert: path to pkcs#12 file
    @type str
    @param password: password to extract certificates from pkcs#12 file
    @type str
    @return: (cert,key): pem certificate as string and private key as string
    @rtype: tuple
    """
    with open(p12cert, 'rb') as f:
        p12 = crypto.load_pkcs12(f.read(), password)
        key = crypto.dump_privatekey(crypto.FILETYPE_PEM, p12.get_privatekey())
        cert = crypto.dump_certificate(crypto.FILETYPE_PEM, p12.get_certificate())
    return cert, key


def get_certs(p12cert, password, is_base64=False):
    """
    Convert pkcs#12 bloomberg certificate into pem format certificates, used by authorized DLWS access.
    @param p12cert: binary or base64 data
    @type str
    @param password: password to extract certificates from pkcs#12 file
    @type str
    @param is_base64: p12cert is bynary or base64 encoded string
    @type bool
    @return: (cert,key): pem certificate as string and private key as string
    @rtype: tuple
    """
    if is_base64:
        p12cert = base64.b64decode(p12cert)
    p12 = crypto.load_pkcs12(p12cert, password)
    key = crypto.dump_privatekey(crypto.FILETYPE_PEM, p12.get_privatekey())
    cert = crypto.dump_certificate(crypto.FILETYPE_PEM, p12.get_certificate())
    return cert, key


class RequestsTransport(HttpAuthenticated):
    """
    Custom transport for SUDs library, required for SSL client certificate authorization. Rely on requests library.
    Should be initialized with cert and key (pem certificate file path and private key respectively).
    """

    def __init__(self, **kwargs):
        self.cert = kwargs.pop('cert', None)
        self.key = kwargs.pop('key', None)
        self.timeout = kwargs.pop('timeout', 10)
        if not self.cert:
            raise BloombergTransportException("cert param could not be None")
        if not self.key:
            raise BloombergTransportException("key param could not be None")
        super(RequestsTransport, self).__init__(**kwargs)

    def get_soap_action(self, message):
        """
        Custom quirk to setup SOAPAction header
        """
        s = message.decode()
        if "submitGetDataRequest" in s:
            return '"submitGetDataRequest"'
        elif "submitGetDataRequest" in s:
            return '"submitGetDataRequest"'
        elif "retrieveGetDataRequest" in s:
            return '"retrieveGetDataResponse"'
        elif "submitGetHistoryRequest" in s:
            return '"submitGetHistoryRequest"'
        elif "retrieveGetHistoryRequest" in s:
            return '"retrieveGetHistoryResponse"'
        elif "getFieldsRequest" in s:
            return '"getFields"'
        return "''"

    def send(self, request):
        """
        Transport to send request with SSL client cert. Use temporary files for certs, which get deleted right after
        request completed.
        request param contain message attr with SOAP generated content.
        """
        self.addcredentials(request)

        with NamedTemporaryFile() as key, NamedTemporaryFile() as cert:
            cert.write(self.cert)
            cert.flush()
            key.write(self.key)
            key.flush()

            request.headers['SOAPAction'] = self.get_soap_action(request.message)

            resp = requests.post(
                request.url,
                data=request.message,
                headers=request.headers,
                cert=(cert.name, key.name),
                verify=True,
                timeout=self.timeout,
            )
            result = Reply(resp.status_code, resp.headers, resp.content)
            return result


class BloombergDataProvider(object):
    """
    Bloomberg python client for Finmars.
    """

    def __init__(self, cert=None, key=None, wsdl=None):
        """
        Constructor for BloomberDataProvider
        @param wsdl: url for WSDL file
        @type: str
        @param cert: SSL client pem certificate as string
        @type: str
        @param key: SSL client pem private key as string
        @type: str
        @return: BloomberDataProvider object
        @rtype: BloombergDataProvider
        """

        wsdl = wsdl or settings.BLOOMBERG_WSDL

        if not wsdl:
            raise BloombergException("wsdl should be provided")
        if not cert:
            raise BloombergException("client certificate pem file should be provided")
        if not key:
            raise BloombergException("private key pem file should be provided")

        transport = RequestsTransport(cert=cert, key=key)
        headers = {
            "Content-Type": "text/xml;charset=UTF-8",
            "SOAPAction": ""
        }
        self.soap_client = Client(wsdl, headers=headers, transport=transport)

    def _response_is_valid(self, response, pending=False, raise_exception=True):
        if response.statusCode.code == 0:
            return True
        elif pending and response.statusCode.code == 100:
            return True
        else:
            if raise_exception:
                raise BloombergException(
                    "Bloomberg failed with code %s and description '%s'" % (
                        response.statusCode.code, response.description))
            return False

    def _data_is_ready(self, response):
        return response.statusCode.code == 0

    def _invoke_sync(self, name, request_func, request_kwargs, response_func):
        _l.debug('> %s', name)
        response_id = request_func(**request_kwargs)
        _l.debug('response_id=%s', response_id)
        for attempt in six.moves.range(1000):
            sleep(0.5)
            _l.debug('attempt=%s', attempt)
            result = response_func(response_id)
            if result:
                _l.debug('<')
                return result
        _l.debug('< failed')
        raise BloombergException("%s('%s') failed" % (name, response_id,))

    def get_fields(self):
        """
        Test method to check SSL connectivity. (is free!)
        @return: bloomberg mnemonic test data.
        @rtype: dict
        """
        _l.debug('get_fields >')

        response = self.soap_client.service.getFields(
            criteria={
                "mnemonic": "NAME"
            }
        )
        _l.debug('response=%s', response)
        self._response_is_valid(response)
        return response

    def get_instrument_send_request(self, instrument, fields):
        """
        Get single instrument data using instrument ISIN and industry code. Async mode. Instrument data should be
        retrieved by get_instrument_get_response further call.
        @param instrument: requested instrument id
        @type tuple: (ISNIN, industry), i.e. (X73487634234,Corp)
        @param fields: list of bloombeg fields to retrieve
        @type list: list of strings
        @return: response id, used by get_instrument_get_response method
        @rtype: str
        """
        _l.debug('> get_instrument_send_request: instrument=%s, fields=%s', instrument, fields)

        fields_data = self.soap_client.factory.create('Fields')
        for field in fields:
            fields_data.field.append(field)

        response = self.soap_client.service.submitGetDataRequest(
            headers={"secmaster": True,},
            fields=fields_data,
            instruments=[
                {
                    "instrument": {
                        "id": instrument["code"],
                        "yellowkey": instrument["industry"],
                    },
                }
            ]
        )
        _l.debug('response=%s', response)
        self._response_is_valid(response)

        response_id = six.text_type(response.responseId)
        _l.debug('< response_id=%s', response_id)

        return response_id

    def get_instrument_get_response(self, response_id):
        """
        Get single instrument data response. If bloomberg task is not ready, would return None.
        @param response_id:
        @type str
        @return: dictionary where key is requested bloomberg field and value - retrieved data
        @rtype: dict
        """

        response = self.soap_client.service.retrieveGetDataResponse(responseId=response_id)
        _l.debug('> get_instrument_get_response: response_id=%s, response=%s', response_id, response)

        self._response_is_valid(response, pending=True)
        if self._data_is_ready(response):
            result = {}
            for i, field in enumerate(response.fields[0]):
                result[field] = response.instrumentDatas[0][0].data[i]._value
            _l.debug('< result=%s', result)
            return result
        return None

    def get_instrument_sync(self, instrument, fields):
        # response_id = self.get_instrument_send_request(instrument, fields)
        # for attempt in six.moves.range(1000):
        #     sleep(0.5)
        #     _l.debug('get_instrument_sync: response_id=%s, attempt=%s', response_id, attempt)
        #     result = self.get_instrument_get_response(response_id)
        #     if result:
        #         return result
        # _l.debug('get_instrument_sync: failed')
        # raise BloombergDataProviderException("get_instrument_sync('%s') failed" % response_id)
        return self._invoke_sync(name='get_instrument_sync',
                                 request_func=self.get_instrument_send_request,
                                 request_kwargs={'instrument': instrument, 'fields': fields},
                                 response_func=self.get_instrument_get_response)

    def get_pricing_latest_send_request(self, instruments):
        """
        Async method to get pricing data. Would return response id, used in
        get_pricing_latest_get_response method.
        This method should be used to collect "yesterday" data info. Normally should be used for automatic daily
        update methods.
        @param instruments: list of instrument tuples. Each tuple - (ISIN,Insustry)
        @type tuple
        @return: response_id: used to get data in get_pricing_latest_get_response
        @rtype: str
        """
        _l.debug('> get_pricing_latest_send_request: instrument=%s', instruments)

        fields = ['PX_YEST_BID', 'PX_YEST_ASK', 'PX_YEST_CLOSE', 'PX_CLOSE_1D', 'ACCRUED_FACTOR', 'CPN', 'SECURITY_TYP']

        fields_data = self.soap_client.factory.create('Fields')
        fields_data.field = fields

        instruments_data = self.soap_client.factory.create('Instruments')
        for instrument in instruments:
            instruments_data.instrument.append({
                "id": instrument["code"],
                "yellowkey": instrument["industry"],
            })

        response = self.soap_client.service.submitGetDataRequest(
            headers={"secmaster": True},
            fields=fields_data,
            instruments=instruments_data
        )
        _l.debug('response=%s', response)
        self._response_is_valid(response)

        response_id = six.text_type(response.responseId)
        _l.debug('< response_id=%s', response_id)

        return response_id

    def get_pricing_latest_get_response(self, response_id):
        """
        Retrieval of yesterday pricing data. Return None is data is not ready.
        @param response_id: request-response reference, received in get_pricing_latest_send_request
        @type str
        @return: dictionary, where key - ISIN, value - dict with {bloomberg_field:value} dicts
        @rtype: dict
        """
        response = self.soap_client.service.retrieveGetDataResponse(responseId=response_id)
        _l.debug('> get_pricing_latest_get_response: response_id=%s, response=%s', response_id, response)

        self._response_is_valid(response, pending=True)
        if self._data_is_ready(response):
            result = {}
            for instrument in response.instrumentDatas[0]:
                # i = 0
                # instrument_fields = {}
                # for field in resp.fields[0]:
                #     instrument_fields[field] = instrument.data[i]._value
                #     i += 1
                instrument_fields = {}
                for i, field in enumerate(response.fields[0]):
                    instrument_fields[field] = instrument.data[i]._value
                result[instrument.instrument.id] = instrument_fields

            _l.debug('< result=%s', result)
            return result
        return None

    def get_pricing_latest_sync(self, instruments):
        """
        Sync method to get pricing data. Would block until response is ready.
        @param instruments: list of instrument tuples. Each tuple - (ISIN,Insustry)
        @type tuple
        @return: dictionary, where key - ISIN, value - dict with {bloomberg_field:value} dicts
        @rtype: dict
        """

        return self._invoke_sync(name='get_pricing_latest_sync',
                                 request_func=self.get_pricing_latest_send_request,
                                 request_kwargs={'instruments': instruments},
                                 response_func=self.get_pricing_latest_get_response)

    def get_pricing_history_send_request(self, instruments, date_from, date_to):
        """
        Async retrieval of historical pricing data. Return None is data is not ready.
        @param date_from: start of historical range
        @type datetime.date
        @param date_to: inclusive end of historical range
        @type datetime.date
        @param instruments: list of instrument tuples. Each tuple - (ISIN,Insustry)
        @type tuple
        @return: dictionary, where key - ISIN, value - dict with {bloomberg_field:value} dicts
        @rtype: dict
        """
        _l.debug('> get_pricing_history_send_request: instrument=%s, date_from=%s, date_to=%s',
                 instruments, date_from, date_to)

        start = date_from.strftime("%Y-%m-%d")
        end = date_to.strftime("%Y-%m-%d")
        fields = ['PX_BID', 'PX_ASK', 'PX_LAST']
        date_range = {
            "daterange": {
                "period": {
                    "start": start,
                    "end": end
                }
            }
        }

        fields_data = self.soap_client.factory.create('Fields')
        fields_data.field = fields

        instruments_data = self.soap_client.factory.create('Instruments')
        for instrument in instruments:
            instruments_data.instrument.append({"id": instrument["code"], "yellowkey": instrument["industry"]})

        response = self.soap_client.service.submitGetHistoryRequest(
            headers=date_range,
            fields=fields_data,
            instruments=instruments_data
        )
        _l.debug('response=%s', response)
        self._response_is_valid(response)

        response_id = six.text_type(response.responseId)
        _l.debug('< response_id=%s', response_id)

        return response_id

    def get_pricing_history_get_response(self, response_id):
        """
        Retrieval of historical pricing data. Return None is data is not ready.
        @param response_id: request-response reference, received in get_pricing_history_send_request
        @type str
        @return: dictionary, where key - ISIN, value - dict with {bloomberg_field:value} dicts
        @rtype: dict
        """

        response = self.soap_client.service.retrieveGetHistoryResponse(responseId=response_id)
        _l.debug('> get_pricing_history_get_response: response_id=%s, response=%s', response_id, response)

        self._response_is_valid(response, pending=True)
        if self._data_is_ready(response):
            result = {}
            for instrument in response.instrumentDatas[0]:
                instrument_fields = {
                    'DATE': instrument.date,
                }
                for i, field in enumerate(response.fields[0]):
                    instrument_fields[field] = instrument.data[i]._value

                if instrument.instrument.id in result:
                    result[instrument.instrument.id].append(instrument_fields)
                else:
                    result[instrument.instrument.id] = [instrument_fields]
            _l.debug('< result=%s', response_id, result)
            return result
        return None

    def get_pricing_history_sync(self, instruments, date_from, date_to):
        """
        Sync method to get historical pricing data. Would block until response is ready.
        @param date_from: start of historical range
        @type datetime
        @param date_to: inclusive end of historical range
        @type datetime
        @param instruments: list of instrument tuples. Each tuple - (ISIN,Insustry)
        @type tuple
        @return: dictionary, where key - ISIN, value - dict with {bloomberg_field:value} dicts
        @rtype: dict
        """

        return self._invoke_sync(name='get_pricing_history_sync',
                                 request_func=self.get_pricing_history_send_request,
                                 request_kwargs={'instruments': instruments, 'date_from': date_from,
                                                 'date_to': date_to},
                                 response_func=self.get_pricing_history_get_response)

    def __str__(self):
        return six.text_type(self.soap_client)


# ----------------------------------------------------------------------------------------------------------------------

class FakeBloombergDataProvider(object):
    """
    Bloomberg python client for Finmars.
    """

    def __init__(self, *args, **kwargs):
        from django.core.cache import caches
        self._cache = caches['default']

    def _make_id(self):
        return '%s' % uuid.uuid4()

    def get_fields(self):
        return 'fake'

    def get_instrument_send_request(self, instrument, fields):
        _l.debug('> get_instrument_send_request: instrument=%s, fields=%s', instrument, fields)
        response_id = self._make_id()

        key = 'instrument.%s' % response_id
        self._cache.set(key, {
            'action': 'instrument',
            'instrument': instrument,
            'fields': fields,
            'response_id': response_id,
        }, timeout=30)

        _l.debug('< response_id=%s', response_id)

        return response_id

    def get_instrument_get_response(self, response_id):
        _l.debug('> get_instrument_get_response: response_id=%s', response_id)

        fake_data = {
            "ACCRUED_FACTOR": "1.000000000",
            "CALC_TYP": "1",
            "CALC_TYP_DES": "STREET CONVENTION",
            "CNTRY_OF_RISK": "N.S.",
            "COUPON_FREQUENCY_DESCRIPTION": "S/A",
            "CPN": "5.375000",
            "CPN_FREQ": "2",
            "CPN_TYP": "FIXED",
            "CPN_TYP_SPECIFIC": "",
            "CRNCY": "USD",
            "CUR_CPN": "",
            "DAYS_TO_SETTLE": "2",
            "DAY_CNT": "20",
            "DAY_CNT_DES": "ISMA-30/360",
            "DES_NOTES": "",
            "FIRST_CPN_DT": "12/16/2016",
            "FIRST_SETTLE_DT": "06/16/2016",
            "ID_BB_GLOBAL": "BBG00D2QX2B8",
            "ID_CUSIP": "LW4068711",
            "ID_ISIN": "XS1433454243",
            "INDUSTRY_SECTOR": "Industrial",
            "INDUSTRY_SUBGROUP": "Transport-Marine",
            "INT_ACC_DT": "06/16/2016",
            "ISSUER": "SCF CAPITAL LTD",
            "MATURITY": "06/16/2023",
            "MTY_TYP": "AT MATURITY",
            "OPT_PUT_CALL": "",
            "PAYMENT_RANK": "Sr Unsecured",
            "SECURITY_DES": "SCFRU 5 3/8 06/16/23",
            "SECURITY_TYP": "EURO-DOLLAR"
        }

        key = 'instrument.%s' % response_id
        req = self._cache.get(key)
        if not req:
            raise RuntimeError('invalid response_id')

        result = {}
        for field in req['fields']:
            result[field] = fake_data.get(field, None)
        _l.debug('< result=%s', result)
        return result

    def get_pricing_latest_send_request(self, instruments):
        _l.debug('> get_pricing_latest_send_request: instruments=%s', instruments)
        response_id = self._make_id()
        fields = ['PX_YEST_BID', 'PX_YEST_ASK', 'PX_YEST_CLOSE', 'PX_CLOSE_1D', 'ACCRUED_FACTOR', 'CPN', 'SECURITY_TYP']

        key = 'pricing_latest.%s' % response_id
        self._cache.set(key, {
            'action': 'pricing_latest',
            'instruments': instruments,
            'fields': fields,
            'response_id': response_id,
        }, timeout=30)

        _l.debug('< response_id=%s', response_id)

        return response_id

    def get_pricing_latest_get_response(self, response_id):
        _l.debug('> get_pricing_latest_get_response: response_id=%s', response_id)
        fake_data = {
            "ACCRUED_FACTOR": "1.000000000",
            "CPN": "6.625000",
            # "PX_CLOSE_1D": "N.S.",
            # "PX_YEST_ASK": "N.S.",
            # "PX_YEST_BID": "N.S.",
            # "PX_YEST_CLOSE": "N.S.",
            # "PX_CLOSE_1D": "N.S.",
            "PX_YEST_ASK": "10.0",
            "PX_YEST_BID": "11.0",
            "PX_YEST_CLOSE": "12.0",
            "SECURITY_TYP": "EURO-DOLLAR"
        }

        key = 'pricing_latest.%s' % response_id
        req = self._cache.get(key)
        if not req:
            raise RuntimeError('invalid response_id')

        result = {}
        for instrument in req['instruments']:
            instrument_fields = {}
            for field in req['fields']:
                instrument_fields[field] = fake_data.get(field, None)
            result[instrument['code']] = instrument_fields
        _l.debug('< result=%s', result)
        return result

    def get_pricing_history_send_request(self, instruments, date_from, date_to):
        _l.debug('> get_pricing_history_send_request: instrument=%s, date_from=%s, date_to=%s',
                 instruments, date_from, date_to)
        response_id = self._make_id()
        fields = ['PX_BID', 'PX_ASK', 'PX_LAST']

        key = 'pricing_history.%s' % response_id
        self._cache.set(key, {
            'action': 'pricing_history',
            'instruments': instruments,
            'date_from': '%s' % date_from,
            'date_to': '%s' % date_to,
            'fields': fields,
            'response_id': response_id,
        }, timeout=30)

        _l.debug('< response_id=%s', response_id)

        return response_id

    def get_pricing_history_get_response(self, response_id):
        _l.debug('> get_pricing_history_get_response: response_id=%s', response_id)
        fake_data = {
            "DATE": "<REPLACE>",
            "PX_ASK": "20.0",
            "PX_BID": "21.0",
            "PX_LAST": "22.0",
        }

        key = 'pricing_history.%s' % response_id
        req = self._cache.get(key)
        if not req:
            raise RuntimeError('invalid response_id')

        date_from = parser.parse(req['date_from']).date()
        date_to = parser.parse(req['date_to']).date()

        result = {}
        for instrument in req['instruments']:
            d = date_from
            while d <= date_to:
                price_fields = {
                    'DATE': d
                }
                for i, field in enumerate(req['fields']):
                    price_fields[field] = fake_data.get(field, None)

                instrument_code = instrument['code']
                if instrument_code in result:
                    result[instrument_code].append(price_fields)
                else:
                    result[instrument_code] = [price_fields]

                d += timedelta(days=1)
        _l.debug('< result=%s', result)
        return result


def get_provider_class():
    if settings.BLOOMBERG_SANDBOX:
        return FakeBloombergDataProvider
    else:
        return BloombergDataProvider


def get_provider(*args, **kwargs):
    clazz = get_provider_class()
    return clazz(*args, **kwargs)


def _safe_float(v):
    if v is None:
        return None
    try:
        return float(v)
    except ValueError:
        return 0.0


def fix_pricing_latest(value):
    ret = {
        'FM_PRICING': 'L',

        'ACCRUED_FACTOR': None,
        'CPN': None,
        'PX_CLOSE_1D': None,
        'PX_YEST_ASK': None,
        'PX_YEST_BID': None,
        'PX_YEST_CLOSE': None,

        'DATE': None,
        'PX_ASK': None,
        'PX_BID': None,
        'PX_LAST': None,
    }
    for k, v in six.iteritems(value):
        if k in ['SECURITY_TYP']:
            ret[k] = v
        elif k in ["ACCRUED_FACTOR", "CPN", "PX_CLOSE_1D", "PX_YEST_ASK", "PX_YEST_BID", "PX_YEST_CLOSE"]:
            tk = k
            # if k == 'PX_YEST_ASK':
            #     tk = 'ASK'
            # elif k == 'PX_YEST_BID':
            #     tk = 'BID'
            # elif k == 'PX_YEST_CLOSE':
            #     tk = 'LAST'
            ret[tk] = _safe_float(v)
    return ret


def fix_price_history(value):
    ret = {
        'FM_PRICING': 'H',

        'ACCRUED_FACTOR': None,
        'CPN': None,
        'PX_CLOSE_1D': None,
        'PX_YEST_ASK': None,
        'PX_YEST_BID': None,
        'PX_YEST_CLOSE': None,

        'DATE': None,
        'PX_ASK': None,
        'PX_BID': None,
        'PX_LAST': None,
    }
    for k, v in six.iteritems(value):
        if k in ['DATE']:
            ret[k] = v
        elif k in ["PX_ASK", "PX_BID", "PX_LAST"]:
            tk = k
            # if k == 'PX_ASK':
            #     tk = 'ASK'
            # elif k == 'PX_BID':
            #     tk = 'BID'
            # elif k == 'PX_LAST':
            #     tk = 'LAST'
            ret[tk] = _safe_float(v)
    return ret


def str_to_date(value):
    return datetime.strptime(value, '%Y-%m-%d').date()


def date_to_str(value):
    return value.strftime(value, '%Y-%m-%d')


def create_instrument_price_history(task, instruments=None, pricing_policies=None, save=False,
                                    fail_silently=True, delete_exists=False, date_range=None, bulk=False,
                                    expr_fail_silently=False):
    _l.debug('> create_instrument_price_history: task_id=%s', task.id)

    kwargs = task.kwargs_object
    result = task.result_object

    if instruments is None:
        instruments = list(task.master_user.instruments.all())
    instr_map = {six.text_type(i.id): i for i in instruments}

    if pricing_policies is None:
        pricing_policies = task.master_user.pricing_policies.all()
    pricing_policies = [pp for pp in pricing_policies if pp.expr]

    if delete_exists and date_range:
        PriceHistory.objects.filter(instrument__in=instruments, date__range=date_range).delete()
    exists = set()
    if fail_silently and date_range and not delete_exists:
        for p in PriceHistory.objects.filter(instrument__in=instruments, date__range=date_range):
            exists.add(
                (p.instrument_id, p.pricing_policy_id, p.date)
            )

    histories = []

    def _create(instr, price_data, price_date):
        for pp in pricing_policies:
            if not pp.expr:
                continue
            p = PriceHistory()
            p.instrument = instr
            if price_date is not None:
                p.date = price_date
            else:
                p.date = str_to_date(price_data['DATE'])
            p.pricing_policy = pp
            try:
                p.principal_price = formula.safe_eval(pp.expr, names=price_data)
            except formula.InvalidExpression:
                if expr_fail_silently:
                    continue
                else:
                    raise
            p.accrued_price = 0.0
            p.factor = price_data['ACCRUED_FACTOR'] if 'ACCRUED_FACTOR' in price_data else 1.0

            if fail_silently and (p.instrument_id, p.pricing_policy_id, p.date) in exists:
                continue

            if save and not bulk:
                try:
                    p.save()
                except IntegrityError:
                    if not fail_silently:
                        raise

            histories.append(p)

    for instr_code, values in result.items():
        instr = instr_map.get(instr_code, None)
        if instr is None:
            continue

        if task.action == Task.ACTION_PRICING_LATEST:
            values = fix_pricing_latest(values)
            _create(instr, values, price_date=kwargs['date_from'])

        elif task.action == Task.ACTION_PRICE_HISTORY:
            for pd in values:
                pd = fix_price_history(pd)
                _create(instr, pd, price_date=None)

        else:
            raise RuntimeError('Invalid action "%s" in task "%s"' % (task.action, task.id))


    if save and bulk:
        PriceHistory.objects.bulk_create(histories)

    _l.debug('< %s', histories)

    return histories


def create_currency_price_history(task, currencies=None, pricing_policies=None, save=False,
                                  fail_silently=False, delete_exists=False, date_range=None, bulk=False,
                                  expr_fail_silently=False):
    _l.debug('> create_currency_price_history: task_id=%s', task.id)

    kwargs = task.kwargs_object
    result = task.result_object

    if currencies is None:
        currencies = list(task.master_user.currencies.all())

    ccy_map = {six.text_type(i.id): i for i in currencies}

    if pricing_policies is None:
        pricing_policies = list(task.master_user.pricing_policies.all())
    pricing_policies = [pp for pp in pricing_policies if pp.expr]

    if delete_exists and date_range:
        CurrencyHistory.objects.filter(currency__in=currencies, date__range=date_range).delete()
    exists = set()
    if fail_silently and date_range and not delete_exists:
        for p in CurrencyHistory.objects.filter(currency__in=currencies, date__range=date_range):
            exists.add(
                (p.currency_id, p.pricing_policy_id, p.date)
            )

    histories = []

    def _create(ccy, price_data, price_date):
        for pp in pricing_policies:
            if not pp.expr:
                continue
            p = CurrencyHistory()
            p.currency = ccy
            if price_date:
                p.date = price_date
            else:
                p.date = str_to_date(price_data['DATE'])
            p.pricing_policy = pp
            try:
                p.fx_rate = formula.safe_eval(pp.expr, names=price_data)
            except formula.InvalidExpression:
                if expr_fail_silently:
                    continue
                else:
                    raise

            if fail_silently and (p.currency_id, p.pricing_policy_id, p.date) in exists:
                continue

            if save and not bulk:
                try:
                    p.save()
                except IntegrityError:
                    if not fail_silently:
                        raise

            histories.append(p)

    for ccy_code, values in result.items():
        ccy = ccy_map.get(ccy_code, None)
        if ccy is None:
            continue

        if task.action == Task.ACTION_PRICING_LATEST:
            values = fix_pricing_latest(values)
            _create(ccy, values, price_date=kwargs['date_from'])

        elif task.action == Task.ACTION_PRICE_HISTORY:
            for pd in values:
                pd = fix_price_history(pd)
                _create(ccy, pd, price_date=None)

        else:
            raise RuntimeError('Invalid action "%s" in task "%s"' % (task.action, task.id))

        # for pd in values:
        #     pd = map_func(pd)
        #     for pp in pricing_policies:
        #         p = CurrencyHistory()
        #         p.currency = ccy
        #         if fixed_date:
        #             p.date = fixed_date
        #         else:
        #             p.date = str_to_date(pd['DATE'])
        #         p.pricing_policy = pp
        #         p.fx_rate = formula.safe_eval(pp.expr, names=pd)
        #
        #         if fail_silently and (p.currency_id, p.pricing_policy_id, p.date) in exists:
        #             continue
        #
        #         if save and not bulk:
        #             try:
        #                 p.save()
        #             except IntegrityError:
        #                 if not fail_silently:
        #                     raise
        #
        #         histories.append(p)

    if save and bulk:
        PriceHistory.objects.bulk_create(histories)

    _l.debug('< %s', histories)

    return histories


def test_instrument_data(b):
    """
    Test instrument data methods
    """
    _l.info('-' * 79)

    instrument_fields = [
        "CRNCY", "SECURITY_TYP", "ISSUER", "CNTRY_OF_RISK", "INDUSTRY_SECTOR", "INDUSTRY_SUBGROUP", "SECURITY_DES",
        "ID_ISIN", "ID_CUSIP", "ID_BB_GLOBAL", "MATURITY", "CPN", "CUR_CPN", "CPN_FREQ",
        "COUPON_FREQUENCY_DESCRIPTION", "CALC_TYP", "CALC_TYP_DES", "DAY_CNT", "DAY_CNT_DES", "INT_ACC_DT",
        "FIRST_SETTLE_DT", "FIRST_CPN_DT", "OPT_PUT_CALL", "MTY_TYP", "PAYMENT_RANK", "CPN_TYP",
        "CPN_TYP_SPECIFIC", "ACCRUED_FACTOR", "DAYS_TO_SETTLE", "DES_NOTES",
    ]

    instrument = {
        "code": 'XS1433454243',
        "industry": "Corp"
    }

    response = b.get_instrument_sync(instrument, instrument_fields)

    # res = {
    #     "ACCRUED_FACTOR": "1.000000000",
    #     "CALC_TYP": "1",
    #     "CALC_TYP_DES": "STREET CONVENTION",
    #     "CNTRY_OF_RISK": "N.S.",
    #     "COUPON_FREQUENCY_DESCRIPTION": "S/A",
    #     "CPN": "5.375000",
    #     "CPN_FREQ": "2",
    #     "CPN_TYP": "FIXED",
    #     "CPN_TYP_SPECIFIC": "",
    #     "CRNCY": "USD",
    #     "CUR_CPN": "",
    #     "DAYS_TO_SETTLE": "2",
    #     "DAY_CNT": "20",
    #     "DAY_CNT_DES": "ISMA-30/360",
    #     "DES_NOTES": "",
    #     "FIRST_CPN_DT": "12/16/2016",
    #     "FIRST_SETTLE_DT": "06/16/2016",
    #     "ID_BB_GLOBAL": "BBG00D2QX2B8",
    #     "ID_CUSIP": "LW4068711",
    #     "ID_ISIN": "XS1433454243",
    #     "INDUSTRY_SECTOR": "Industrial",
    #     "INDUSTRY_SUBGROUP": "Transport-Marine",
    #     "INT_ACC_DT": "06/16/2016",
    #     "ISSUER": "SCF CAPITAL LTD",
    #     "MATURITY": "06/16/2023",
    #     "MTY_TYP": "AT MATURITY",
    #     "OPT_PUT_CALL": "",
    #     "PAYMENT_RANK": "Sr Unsecured",
    #     "SECURITY_DES": "SCFRU 5 3/8 06/16/23",
    #     "SECURITY_TYP": "EURO-DOLLAR"
    # }

    _l.info('response: %s', pprint.pformat(response))


def test_pricing_latest(b):
    """
    Test pricing data methods
    """
    _l.info('-' * 79)

    instrument1 = {"code": 'XS1433454243', "industry": "Corp"}
    instrument2 = {"code": 'USL9326VAA46', "industry": "Corp"}

    response = b.get_pricing_latest_sync([instrument1, instrument2])
    # res = {
    #     "USL9326VAA46": {
    #         "ACCRUED_FACTOR": "1.000000000",
    #         "CPN": "6.625000",
    #         "PX_CLOSE_1D": "N.S.",
    #         "PX_YEST_ASK": "N.S.",
    #         "PX_YEST_BID": "N.S.",
    #         "PX_YEST_CLOSE": "N.S.",
    #         "SECURITY_TYP": "EURO-DOLLAR"
    #     },
    #     "XS1433454243": {
    #         "ACCRUED_FACTOR": "1.000000000",
    #         "CPN": "5.375000",
    #         "PX_CLOSE_1D": "N.S.",
    #         "PX_YEST_ASK": "N.S.",
    #         "PX_YEST_BID": "N.S.",
    #         "PX_YEST_CLOSE": "N.S.",
    #         "SECURITY_TYP": "EURO-DOLLAR"
    #     }
    # }
    _l.info('response: %s', pprint.pformat(response))


def test_pricing_history(b):
    """
    Test pricing data methods
    """
    _l.info('-' * 79)

    instrument1 = {"code": 'XS1433454243', "industry": "Corp"}
    instrument2 = {"code": 'USL9326VAA46', "industry": "Corp"}

    response = b.get_pricing_history_sync(instruments=[instrument1, instrument2],
                                          date_from=date(year=2016, month=6, day=14),
                                          date_to=date(year=2016, month=6, day=15))

    # res = {
    #     "USL9326VAA46": [
    #         {
    #             "PX_ASK": "94.413",
    #             "PX_BID": "93.108",
    #             "PX_LAST": "93.761",
    #             "date": "2016-06-15"
    #         }
    #     ],
    #     "XS1433454243": [
    #         {
    #             "PX_ASK": "100.302",
    #             "PX_BID": "99.88",
    #             "PX_LAST": "100.091",
    #             "date": "2016-06-15"
    #         }
    #     ]
    # }

    _l.info('response: %s', pprint.pformat(response))


if __name__ == "__main__":
    # noinspection PyUnresolvedReferences
    import env_ai

    import django

    django.setup()

    p12cert = os.environ['TEST_BLOOMBERG_CERT']
    password = os.environ['TEST_BLOOMBERG_CERT_PASSWORD']

    cert, key = get_certs_from_file(p12cert, password)

    # b = BloomberDataProvider(wsdl="https://service.bloomberg.com/assets/dl/dlws.wsdl", cert=cert, key=key)
    b = FakeBloombergDataProvider(wsdl="https://service.bloomberg.com/assets/dl/dlws.wsdl", cert=cert, key=key)
    # b.get_fields()
    # test_instrument_data(b)
    # test_pricing_latest(b)
    # test_pricing_history(b)

    # from dateutil import parser
    # _l.info('1: %s', parser.parse("06/16/2023"))
    # _l.info('2: %s', parser.parse("2016-06-15"))

    from poms.integrations.tasks import bloomberg_call
    from poms.users.models import MasterUser

    master_user = MasterUser.objects.first()

    a = bloomberg_call(
        master_user=master_user,
        action='fields'
    )
    # a = bloomberg_instrument(
    #     master_user=master_user,
    #     instrument={
    #         "code": 'XS1433454243',
    #         "industry": "Corp"
    #     },
    #     fields=['CRNCY']
    # )
    # a = bloomberg_pricing_latest(
    #     master_user=master_user,
    #     instruments=[
    #         {"code": 'XS1433454243', "industry": "Corp"},
    #         {"code": 'USL9326VAA46', "industry": "Corp"},
    #     ]
    # )
    # a = bloomberg_pricing_history(
    #     master_user=master_user,
    #     instruments=[
    #         {"code": 'XS1433454243', "industry": "Corp"},
    #         {"code": 'USL9326VAA46', "industry": "Corp"},
    #     ],
    #     date_from=date(year=2016, month=6, day=14),
    #     date_to=date(year=2016, month=6, day=15),
    # )

    # if getattr(settings, 'CELERY_ALWAYS_EAGER', False):
    #     print('a.get ->', a.get(timeout=60, interval=0.1))
    # else:
    #     b = AsyncResult(a.id)
    #     print('b.get ->', b.get(timeout=60, interval=0.1))

    pass
