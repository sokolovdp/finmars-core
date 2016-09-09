from collections import OrderedDict
from datetime import date, datetime
from logging import getLogger

from dateutil import parser
from dateutil.rrule import rrule, DAILY
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy as _

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
    def get_max_retries(self):
        return 3

    def get_retry_delay(self):
        return 5

    def parse_date(self, v):
        if v is not None:
            if isinstance(v, date):
                return v
            elif isinstance(v, datetime):
                return v.date()
            else:
                try:
                    v = parser.parse(v)
                    return v.date()
                except ValueError:
                    return None
        return None

    def parse_float(self, v):
        if v is None:
            return None
        try:
            return float(v)
        except ValueError:
            return 0.0

    def get_factor_schedule_method_fields(self, factor_schedule_method=None):
        return []

    def get_accrual_calculation_schedule_method_fields(self, accrual_calculation_schedule_method=None):
        return []

    def is_valid_reference(self, value):
        return True

    def download_instrument(self, options):
        return None, True

    def download_instrument_pricing(self, options):
        return None, True

    def download_currency_pricing(self, options):
        return None, True

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

    def create_instrument(self, instrument_download_scheme, values):
        errors = OrderedDict()
        master_user = instrument_download_scheme.master_user
        provider = instrument_download_scheme.provider

        instr = Instrument(master_user=master_user)

        instr.instrument_type = master_user.instrument_type
        instr.pricing_currency = master_user.currency
        instr.accrued_currency = master_user.currency

        instr.payment_size_detail = instrument_download_scheme.payment_size_detail
        instr.daily_pricing_model = instrument_download_scheme.daily_pricing_model
        instr.price_download_scheme = instrument_download_scheme.price_download_scheme
        instr.default_price = instrument_download_scheme.default_price
        instr.default_accrued = instrument_download_scheme.default_accrued

        for attr in InstrumentDownloadScheme.BASIC_FIELDS:
            expr = getattr(instrument_download_scheme, attr)
            if not expr:
                continue
            try:
                v = formula.safe_eval(expr, names=values)
            except formula.InvalidExpression as e:
                # _l.debug('Invalid expression "%s"', attr, exc_info=True)
                errors[attr] = [_('Invalid expression')]
                continue
            if attr in ['pricing_currency', 'accrued_currency']:
                if v is not None:
                    v = self.get_currency(master_user, provider, v)
                    if v:
                        setattr(instr, attr, v)
                    else:
                        errors[attr] = [_('This field is required.')]
            elif attr in ['instrument_type']:
                if v is not None:
                    v = self.get_instrument_type(master_user, provider, v)
                    if v:
                        setattr(instr, attr, v)
                    else:
                        errors[attr] = [_('This field is required.')]
            elif attr in ['price_multiplier', 'accrued_multiplier', 'default_price', 'default_accrued']:
                if v is not None:
                    try:
                        setattr(instr, attr, float(v))
                    except (ValueError, TypeError):
                        errors[attr] = [_('A valid number is required.')]
            elif attr in ['maturity_date']:
                if v is not None:
                    if isinstance(v, datetime):
                        v = v.date()
                    if isinstance(v, date):
                        setattr(instr, attr, v)
                    else:
                        errors[attr] = [_('A valid date is required.')]
            else:
                if v is not None:
                    v = str(v)
                    setattr(instr, attr, v)

        instr._attributes = self.create_instrument_attributes(
            instrument_download_scheme=instrument_download_scheme, instrument=instr, values=values, errors=errors)

        instr._accrual_calculation_schedules = self.create_accrual_calculation_schedules(
            instrument_download_scheme=instrument_download_scheme, instrument=instr, values=values)

        instr._factor_schedules = self.create_factor_schedules(
            instrument_download_scheme=instrument_download_scheme, instrument=instr, values=values)

        return instr, errors

    def create_instrument_attributes(self, instrument_download_scheme, instrument, values, errors):
        iattrs = []
        master_user = instrument_download_scheme.master_user
        provider = instrument_download_scheme.provider
        for attr in instrument_download_scheme.attributes.select_related('attribute_type').all():
            tattr = attr.attribute_type

            iattr = InstrumentAttribute(content_object=instrument, attribute_type=tattr)
            iattrs.append(iattr)

            err_name = 'attribute_type:%s' % attr.attribute_type.id

            if attr.value:
                try:
                    v = formula.safe_eval(attr.value, names=values)
                except formula.InvalidExpression as e:
                    # _l.debug('Invalid expression "%s"', attr.value, exc_info=True)
                    errors[err_name] = [_('Invalid expression')]
                    continue
                attr_mapped_values = self.get_instrument_attribute_value(master_user, provider, tattr, v)
                if attr_mapped_values:
                    iattr.value_string, iattr.value_float, iattr.value_date, iattr.classifier = attr_mapped_values
                else:
                    if tattr.value_type == AbstractAttributeType.STRING:
                        if v is not None:
                            iattr.value_string = str(v)
                    elif tattr.value_type == AbstractAttributeType.NUMBER:
                        if v is not None:
                            try:
                                iattr.value_float = float(v)
                            except (ValueError, TypeError):
                                errors[err_name] = [_('A valid number is required.')]
                    elif tattr.value_type == AbstractAttributeType.DATE:
                        if v is not None:
                            if isinstance(v, datetime):
                                v = v.date()
                            if isinstance(v, date):
                                iattr.value_date = v
                            else:
                                errors[err_name] = [_('A valid date is required.')]
                    elif tattr.value_type == AbstractAttributeType.CLASSIFIER:
                        if v is not None:
                            v = str(v)
                            v = tattr.classifiers.filter(name=v).first()
                            if v:
                                iattr.classifier = v
                            else:
                                errors[err_name] = [_('This field is required.')]
            else:
                errors[err_name] = [_('Expression required')]
        return iattrs

    def create_accrual_calculation_schedules(self, instrument_download_scheme, instrument, values):
        return []

    def create_factor_schedules(self, instrument_download_scheme, instrument, values):
        return []

    def create_instrument_pricing(self, price_download_scheme, options, values, instruments, pricing_policies):
        return []

    def create_currency_pricing(self, price_download_scheme, options, values, currencies, pricing_policies):
        return []


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
