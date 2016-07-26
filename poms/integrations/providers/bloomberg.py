import base64
import json
import os
import uuid
from datetime import datetime
from logging import getLogger
from tempfile import NamedTemporaryFile
from time import sleep

import requests
import six
from OpenSSL import crypto
from django.utils.encoding import force_text
from suds.client import Client
from suds.transport import Reply
from suds.transport.http import HttpAuthenticated

__author__ = 'alyakhov'

_l = getLogger('poms.integrations.providers.bloomberg')


# _l = getLogger(__name__)


class BloombergException(Exception):
    pass


class BloombergTransportException(BloombergException):
    pass


class BloombergDataProviderException(BloombergException):
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


class BloomberDataProvider(object):
    """
    Bloomberg python client for Finmars.
    """

    def __init__(self, wsdl=None, cert=None, key=None):
        """
        Constructor for BloomberDataProvider
        @param wsdl: url for WSDL file
        @type: str
        @param cert: SSL client pem certificate as string
        @type: str
        @param key: SSL client pem private key as string
        @type: str
        @return: BloomberDataProvider object
        @rtype: BloomberDataProvider
        """

        if not wsdl:
            raise BloombergDataProviderException("wsdl should be provided")

        if not cert:
            raise BloombergDataProviderException("client certificate pem file should be provided")

        if not key:
            raise BloombergDataProviderException("private key pem file should be provided")

        transport = RequestsTransport(cert=cert, key=key)
        headers = {
            "Content-Type": "text/xml;charset=UTF-8",
            "SOAPAction": ""
        }
        self.soap_client = Client(wsdl, headers=headers, transport=transport)

    def get_fields(self):
        """
        Test method to check SSL connectivity.
        @return: bloomberg mnemonic test data.
        @rtype: dict
        """
        # request = {"mnemonic": "NAME"}
        resp = self.soap_client.service.getFields(
            criteria={
                "mnemonic": "NAME"
            }
        )
        return resp

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

        fields_data = self.soap_client.factory.create('Fields')
        for field in fields:
            fields_data.field.append(field)

        resp = self.soap_client.service.submitGetDataRequest(
            headers={
                "secmaster": True
            },
            fields=fields_data,
            instruments=[
                {
                    "instrument": {
                        "id": instrument["code"],
                        "yellowkey": instrument["industry"]
                    }
                }
            ]
        )

        response_id = six.text_type(resp.responseId)
        _l.debug('get_instrument_send_request: response_id=%s', response_id)
        return response_id

    def get_instrument_get_response(self, response_id):
        """
        Get single instrument data response. If bloomberg task is not ready, would return None.
        @param response_id:
        @type str
        @return: dictionary where key is requested bloomberg field and value - retrieved data
        @rtype: dict
        """

        resp = self.soap_client.service.retrieveGetDataResponse(responseId=response_id)
        _l.debug('get_instrument_get_response: response_id=%s, resp=%s', response_id, resp)

        if resp.statusCode.code == 0:
            res = {}
            # i = 0
            # for field in resp.fields[0]:
            #     res[field] = resp.instrumentDatas[0][0].data[i]._value
            #     i += 1
            for i, field in enumerate(resp.fields[0]):
                res[field] = resp.instrumentDatas[0][0].data[i]._value
            return res
        else:
            return None

    def get_instrument_sync(self, instrument, fields):
        response_id = self.get_instrument_send_request(instrument, fields)
        attempt = 0
        while attempt < 1000:
            sleep(0.5)
            _l.debug('get_instrument_sync: response_id=%s, attempt=%s', response_id, attempt)
            res = self.get_instrument_get_response(response_id)
            if not res:
                attempt += 1
                continue
            else:
                return res
        raise BloombergDataProviderException("Failed after %d attempts" % attempt)

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
        fields_data = self.soap_client.factory.create('Fields')
        fields_data.field = ['PX_YEST_BID', 'PX_YEST_ASK', 'PX_YEST_CLOSE', 'PX_CLOSE_1D', 'ACCRUED_FACTOR', 'CPN',
                             'SECURITY_TYP']

        instruments_data = self.soap_client.factory.create('Instruments')
        for instrument in instruments:
            instruments_data.instrument.append({"id": instrument["code"], "yellowkey": instrument["industry"]})

        resp = self.soap_client.service.submitGetDataRequest(
            headers={"secmaster": True},
            fields=fields_data,
            instruments=instruments_data
        )

        response_id = six.text_type(resp.responseId)
        _l.debug('get_pricing_latest_send_request: response_id=%s', response_id)
        return response_id

    def get_pricing_latest_get_response(self, response_id):
        """
        Retrieval of yesterday pricing data. Return None is data is not ready.
        @param response_id: request-response reference, received in get_pricing_latest_send_request
        @type str
        @return: dictionary, where key - ISIN, value - dict with {bloomberg_field:value} dicts
        @rtype: dict
        """
        resp = self.soap_client.service.retrieveGetDataResponse(responseId=response_id)
        _l.debug('get_pricing_latest_get_response: response_id=%s, resp=%s', response_id, resp)

        if resp.statusCode.code == 0:
            res = {}
            for instrument in resp.instrumentDatas[0]:
                # i = 0
                # instrument_fields = {}
                # for field in resp.fields[0]:
                #     instrument_fields[field] = instrument.data[i]._value
                #     i += 1
                instrument_fields = {}
                for i, field in enumerate(resp.fields[0]):
                    instrument_fields[field] = instrument.data[i]._value
                res[instrument.instrument.id] = instrument_fields
            return res
        return None

    def get_pricing_latest_sync(self, instruments):
        """
        Sync method to get pricing data. Would block until response is ready.
        @param instruments: list of instrument tuples. Each tuple - (ISIN,Insustry)
        @type tuple
        @return: dictionary, where key - ISIN, value - dict with {bloomberg_field:value} dicts
        @rtype: dict
        """

        response_id = self.get_pricing_latest_send_request(instruments)
        attempt = 0
        while attempt < 1000:
            sleep(0.5)
            _l.debug('get_pricing_latest_sync: response_id=%s, attempt=%s', response_id, attempt)
            res = self.get_pricing_latest_get_response(response_id)
            if not res:
                attempt += 1
                continue
            else:
                return res
        raise BloombergDataProviderException("Failed after %d attempts" % attempt)

    def get_pricing_history_send_request(self, date_from, date_to, instruments):
        """
        Async retrieval of historical pricing data. Return None is data is not ready.
        @param date_from: start of historical range
        @type datetime
        @param date_to: inclusive end of historical range
        @type datetime
        @param instruments: list of instrument tuples. Each tuple - (ISIN,Insustry)
        @type tuple
        @return: dictionary, where key - ISIN, value - dict with {bloomberg_field:value} dicts
        @rtype: dict
        """

        start = date_from.strftime("%Y-%m-%d")
        end = date_to.strftime("%Y-%m-%d")

        daterange = {"daterange": {"period": {"start": start, "end": end}}}

        fields_data = self.soap_client.factory.create('Fields')
        fields_data.field = ['PX_BID', 'PX_ASK', 'PX_LAST']

        instruments_data = self.soap_client.factory.create('Instruments')
        for instrument in instruments:
            instruments_data.instrument.append({"id": instrument["code"], "yellowkey": instrument["industry"]})

        resp = self.soap_client.service.submitGetHistoryRequest(
            headers=daterange,
            fields=fields_data,
            instruments=instruments_data
        )

        response_id = six.text_type(resp.responseId)
        _l.debug('get_pricing_history_send_request: response_id=%s', response_id)
        return response_id

    def get_pricing_history_get_response(self, response_id):
        """
        Retrieval of historical pricing data. Return None is data is not ready.
        @param response_id: request-response reference, received in get_pricing_history_send_request
        @type str
        @return: dictionary, where key - ISIN, value - dict with {bloomberg_field:value} dicts
        @rtype: dict
        """

        resp = self.soap_client.service.retrieveGetHistoryResponse(responseId=response_id)
        _l.debug('get_pricing_history_get_response: response_id=%s, resp=%s', response_id, resp)

        if resp.statusCode.code == 0:
            res = {}
            for instrument in resp.instrumentDatas[0]:
                # i = 0
                # instrument_fields = {}
                # for field in resp.fields[0]:
                #     instrument_fields[field] = instrument.data[i]._value
                #     i += 1
                date = instrument.date  # actual is datetime.date
                date = force_text(date)

                instrument_fields = {'date': date}
                for i, field in enumerate(resp.fields[0]):
                    instrument_fields[field] = instrument.data[i]._value

                if instrument.instrument.id in res:
                    res[instrument.instrument.id].append(instrument_fields)
                else:
                    res[instrument.instrument.id] = [instrument_fields]
            return res
        return None

    def get_pricing_history_sync(self, date_from, date_to, instruments):
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

        response_id = self.get_pricing_history_send_request(date_from, date_to, instruments)
        attempt = 0
        while attempt < 1000:
            sleep(0.5)
            _l.debug('get_pricing_history_sync: response_id=%s, attempt=%s', response_id, attempt)
            res = self.get_pricing_history_get_response(response_id)
            if not res:
                attempt += 1
                continue
            else:
                return res
        raise BloombergDataProviderException("Failed after %d attempts" % attempt)

    def __str__(self):
        return six.text_type(self.soap_client)


# ----------------------------------------------------------------------------------------------------------------------

class FakeBloomberDataProvider(BloomberDataProvider):
    """
    Bloomberg python client for Finmars.
    """

    def __init__(self, *args, **kwargs):
        super(FakeBloomberDataProvider, self).__init__(*args, **kwargs)
        self._requests = {}

    def get_fields(self):
        return 'fake'

    def get_instrument_send_request(self, instrument, fields):
        id = uuid.uuid4().hex
        self._requests[id] = {
            'action': 'instrument',
            'id': id,
            'instrument': instrument,
            'fields': fields,
        }
        _l.debug('get_instrument_send_request: response_id=%s', id)
        return id

    def get_instrument_get_response(self, response_id):
        req = self._requests.pop(response_id, None)
        if not req:
            return None
        res = {}
        for field in req['fields']:
            res[field] = field
        _l.debug('get_instrument_get_response: response_id=%s, res=%s', response_id, res)
        return res

    def get_pricing_latest_send_request(self, instruments):
        id = uuid.uuid4().hex
        self._requests[id] = {
            'action': 'pricing_latest',
            'id': id,
            'instruments': instruments,
            'fields': ['PX_YEST_BID', 'PX_YEST_ASK', 'PX_YEST_CLOSE', 'PX_CLOSE_1D', 'ACCRUED_FACTOR', 'CPN',
                       'SECURITY_TYP']
        }
        _l.debug('get_pricing_latest_send_request: response_id=%s', id)
        return id

    def get_pricing_latest_get_response(self, response_id):
        req = self._requests.pop(response_id, None)
        if not req:
            return None
        res = {}
        for instrument in req['instruments']:
            instrument_fields = {}
            for field in req['fields']:
                instrument_fields[field] = field
            res[instrument['code']] = instrument_fields
        _l.debug('get_pricing_latest_get_response: response_id=%s, res=%s', response_id, res)
        return res

    def get_pricing_history_send_request(self, date_from, date_to, instruments):
        id = uuid.uuid4().hex
        self._requests[id] = {
            'action': 'pricing_history',
            'id': id,
            'instruments': instruments,
            'date_from': date_from,
            'date_to': date_to,
            'fields': ['PX_BID', 'PX_ASK', 'PX_LAST'],
        }
        _l.debug('get_pricing_history_send_request: response_id=%s', id)
        return id

    def get_pricing_history_get_response(self, response_id):
        req = self._requests.pop(response_id, None)
        if not req:
            return None
        res = {}
        for instrument in req['instruments']:
            instrument_fields = {}
            for field in req['fields']:
                instrument_fields[field] = field
            res[instrument['code']] = instrument_fields
        _l.debug('get_pricing_history_get_response: response_id=%s, res=%s', response_id, res)
        return res


def test_instrument_data(b):
    """
    Test instrument data methods
    """
    _l.info('test_instrument_data ------')

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

    res = b.get_instrument_sync(instrument, instrument_fields)

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

    _l.info('res: %s', json.dumps(res, sort_keys=True, indent=4))


def test_pricing_latest(b):
    """
    Test pricing data methods
    """
    _l.info('test_pricing_latest ------')

    instrument1 = {"code": 'XS1433454243', "industry": "Corp"}
    instrument2 = {"code": 'USL9326VAA46', "industry": "Corp"}

    res = b.get_pricing_latest_sync([instrument1, instrument2])
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
    _l.info('res: %s', json.dumps(res, sort_keys=True, indent=4))


def test_pricing_history(b):
    """
    Test pricing data methods
    """
    _l.info('test_pricing_history ------')

    instrument1 = {"code": 'XS1433454243', "industry": "Corp"}
    instrument2 = {"code": 'USL9326VAA46', "industry": "Corp"}

    res = b.get_pricing_history_sync(datetime(year=2016, month=6, day=15),
                                     datetime(year=2016, month=6, day=15),
                                     [instrument1, instrument2])

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

    _l.info('res: %s', json.dumps(res, sort_keys=True, indent=4))


if __name__ == "__main__":
    # noinspection PyUnresolvedReferences
    import env_ai

    import django

    django.setup()

    p12cert = os.environ['TEST_BLOOMBERG_CERT']
    password = os.environ['TEST_BLOOMBERG_CERT_PASSWORD']

    cert, key = get_certs_from_file(p12cert, password)

    b = BloomberDataProvider(wsdl="https://service.bloomberg.com/assets/dl/dlws.wsdl", cert=cert, key=key)
    # b = FakeBloomberDataProvider(wsdl="https://service.bloomberg.com/assets/dl/dlws.wsdl", cert=cert, key=key)
    # pprint.pprint(b.get_fields())
    # test_instrument_data(b)
    # test_pricing_latest(b)
    test_pricing_history(b)
