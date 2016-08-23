from datetime import date, datetime
from logging import getLogger

import six
from dateutil import parser
from dateutil.rrule import rrule, DAILY
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from poms.common import formula
from poms.currencies.models import CurrencyHistory
from poms.instruments.models import Instrument, InstrumentAttribute, PriceHistory
from poms.integrations.models import InstrumentDownloadScheme, ProviderClass, CurrencyMapping, InstrumentTypeMapping, \
    InstrumentAttributeValueMapping, AccrualCalculationModelMapping, PeriodicityMapping
from poms.obj_attrs.models import AbstractAttributeType

_l = getLogger('poms.integrations')


class ProviderException(Exception):
    pass


class AbstractProvider(object):
    def get_factor_schedule_method_fields(self, factor_schedule_method=None):
        return []

    def get_accrual_calculation_schedule_method_fields(self, accrual_calculation_schedule_method=None):
        return []

    def download_instrument(self, options):
        return None, True

    def download_instrument_pricing(self, options):
        return None, True

    def download_currency_pricing(self, options):
        return None, True

    def parse_date(self, v):
        if v is not None:
            if isinstance(v, date):
                return v
            elif isinstance(v, datetime):
                return v.date()
            else:
                v = parser.parse(v)
                if v:
                    return v.date()
        return None

    def parse_float(self, v):
        if v is None:
            return None
        try:
            return float(v)
        except ValueError:
            return 0.0

    def get_currency(self, master_user, provider, value):
        if not value:
            return None
        try:
            obj = CurrencyMapping.objects.select_related('currency').get(
                master_user=master_user, provider=provider, value=value)
        except CurrencyMapping.DoesNotExist:
            return None
        return obj.currency

    def get_instrument_type(self, master_user, provider, value):
        if not value:
            return None
        try:
            obj = InstrumentTypeMapping.objects.select_related('instrument_type').get(
                master_user=master_user, provider=provider, value=value)
        except InstrumentTypeMapping.DoesNotExist:
            return None
        return obj.instrument_type

    def get_instrument_attribute_value(self, master_user, provider, attribute_type, value):
        if not value:
            return None
        try:
            obj = InstrumentAttributeValueMapping.objects.select_related('classifier').get(
                master_user=master_user, provider=provider, attribute_type=attribute_type, value=value)
        except InstrumentAttributeValueMapping.DoesNotExist:
            return None
        return obj.value_string, obj.value_float, obj.value_date, obj.classifier

    def get_accrual_calculation_model(self, master_user, provider, value):
        if not value:
            return None
        try:
            obj = AccrualCalculationModelMapping.objects.select_related('accrual_calculation_model').get(
                master_user=master_user, provider=provider, value=value)
        except AccrualCalculationModelMapping.DoesNotExist:
            return None
        return obj.accrual_calculation_model

    def get_periodicity(self, master_user, provider, value):
        if not value:
            return None
        try:
            obj = PeriodicityMapping.objects.select_related('periodicity').get(
                master_user=master_user, provider=provider, value=value)
        except PeriodicityMapping.DoesNotExist:
            return None
        return obj.periodicity

    def create_instrument(self, instrument_download_scheme, values, save=False):
        master_user = instrument_download_scheme.master_user
        provider = instrument_download_scheme.provider

        instr = Instrument(master_user=master_user)

        instr.instrument_type = master_user.instrument_type
        # instr.pricing_currency = master_user.currency
        # instr.accrued_currency = master_user.currency

        for attr in InstrumentDownloadScheme.BASIC_FIELDS:
            expr = getattr(instrument_download_scheme, attr)
            if expr:
                try:
                    v = formula.safe_eval(expr, names=values)
                except formula.InvalidExpression:
                    _l.debug('Invalid expression "%s"', attr, exc_info=True)
                    continue
                if attr in ['pricing_currency', 'accrued_currency']:
                    if v is not None:
                        v = self.get_currency(master_user, provider, v)
                        setattr(instr, attr, v)
                elif attr in ['instrument_type']:
                    if v is not None:
                        v = self.get_instrument_type(master_user, provider, v)
                        setattr(instr, attr, v)
                elif attr in ['price_multiplier', 'accrued_multiplier', 'default_price', 'default_accrued']:
                    if v is not None:
                        v = float(v)
                        setattr(instr, attr, v)
                else:
                    if v is not None:
                        v = six.text_type(v)
                        setattr(instr, attr, v)

        if save:
            instr.save()

        instr._attributes = self.create_instrument_attributes(
            instrument_download_scheme=instrument_download_scheme, instrument=instr, values=values, save=save)

        instr._accrual_calculation_schedules = self.create_accrual_calculation_schedules(
            instrument_download_scheme=instrument_download_scheme, instrument=instr, values=values, save=save)

        instr._factor_schedules = self.create_factor_schedules(
            instrument_download_scheme=instrument_download_scheme, instrument=instr, values=values, save=save)

        return instr

    def create_instrument_attributes(self, instrument_download_scheme, instrument, values, save=False):
        iattrs = []
        master_user = instrument_download_scheme.master_user
        provider = instrument_download_scheme.provider
        for attr in instrument_download_scheme.attributes.select_related('attribute_type').all():
            tattr = attr.attribute_type

            iattr = InstrumentAttribute(content_object=instrument, attribute_type=tattr)
            iattrs.append(iattr)

            if attr.value:
                try:
                    v = formula.safe_eval(attr.value, names=values)
                except formula.InvalidExpression as e:
                    _l.debug('Invalid expression "%s"', attr.value, exc_info=True)
                    v = None
                attr_mapped_values = self.get_instrument_attribute_value(master_user, provider, tattr, v)
                if attr_mapped_values:
                    iattr.value_string, iattr.value_float, iattr.value_date, iattr.classifier = attr_mapped_values
                else:
                    if tattr.value_type == AbstractAttributeType.STRING:
                        if v is not None:
                            iattr.value_string = six.text_type(v)
                    elif tattr.value_type == AbstractAttributeType.NUMBER:
                        if v is not None:
                            iattr.value_float = float(v)
                    elif tattr.value_type == AbstractAttributeType.DATE:
                        if v is not None:
                            iattr.value_date = self.parse_date(v)
                    elif tattr.value_type == AbstractAttributeType.CLASSIFIER:
                        if v is not None:
                            v = six.text_type(v)
                            v = tattr.classifiers.filter(name=v).first()
                            iattr.classifier = v

            if save:
                iattr.save()

        return iattrs

    def create_accrual_calculation_schedules(self, instrument_download_scheme, instrument, values, save=False):
        return []

    def create_factor_schedules(self, instrument_download_scheme, instrument, values, save=False):
        return []

        # def create_instrument_pricing(self, price_download_scheme, values, save=False):
        #     return []
        #
        # def create_currency_pricing(self, price_download_scheme, values, save=False):
        #     return []


def get_provider(master_user=None, provider=None, task=None):
    if master_user is None:
        master_user = task.master_user
    if provider is None:
        provider = task.provider_id

    if provider == ProviderClass.BLOOMBERG:
        if settings.BLOOMBERG_SANDBOX:
            from poms.integrations.providers.bloomberg import FakeBloombergDataProvider
            return FakeBloombergDataProvider()
        else:
            from poms.integrations.providers.bloomberg import BloombergDataProvider
            try:
                config = master_user.import_configs.get(provider=ProviderClass.BLOOMBERG)
                cert, key = config.pair
                return BloombergDataProvider(cert=cert, key=key)
            except ObjectDoesNotExist:
                # fo
                return BloombergDataProvider()
    return None


def parse_date_iso(v):
    if v is not None:
        return datetime.strptime(v, "%Y-%m-%d").date()
    return None


def fill_instrument_price(date_from, days, original):
    ret = []
    for d in rrule(freq=DAILY, count=days, dtstart=date_from):
        ret.append(PriceHistory(
            instrument=original.instrument,
            pricing_policy=original.pricing_policy,
            date=d.date(),
            principal_price=original.principal_price
        ))
    return ret


def fill_currency_price(date_from, days, original):
    ret = []
    for d in rrule(freq=DAILY, count=days, dtstart=date_from):
        ret.append(CurrencyHistory(
            currency=original.currency,
            pricing_policy=original.pricing_policy,
            date=d.date(),
            fx_rate=original.fx_rate
        ))
    return ret
