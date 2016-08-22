from datetime import date, datetime
from logging import getLogger

import six
from dateutil import parser
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from poms.common import formula
from poms.instruments.models import Instrument, InstrumentAttribute
from poms.integrations.models import InstrumentDownloadScheme, ProviderClass, CurrencyMapping, InstrumentTypeMapping, \
    InstrumentAttributeValueMapping, AccrualCalculationModelMapping, PeriodicityMapping
from poms.obj_attrs.models import AbstractAttributeType

_l = getLogger('poms.integrations')


class AbstractProvider(object):
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

    def create_instrument(self, task, value_overrides, save=False):
        master_user = task.master_user
        provider = task.provider
        scheme = task.instrument_download_scheme

        values = task.result_object.copy()
        if value_overrides:
            values.update(value_overrides)

        instr = Instrument(master_user=master_user)

        instr.instrument_type = master_user.instrument_type
        # instr.pricing_currency = master_user.currency
        # instr.accrued_currency = master_user.currency

        for attr in InstrumentDownloadScheme.BASIC_FIELDS:
            expr = getattr(scheme, attr)
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

        iattrs = []
        for attr in scheme.attributes.select_related('attribute_type').all():
            tattr = attr.attribute_type

            iattr = InstrumentAttribute(content_object=instr, attribute_type=tattr)
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

        instr._attributes = iattrs

        accrual_calculation_schedule_method = scheme.accrual_calculation_schedule_method_id
        instr._accrual_calculation_schedules = self.create_accrual_calculation_schedules(
            task=task,
            instrument=instr,
            values=values,
            accrual_calculation_schedule_method=accrual_calculation_schedule_method,
            save=save
        )

        factor_schedule_method = scheme.factor_schedule_method_id
        instr._factor_schedules = self.create_factor_schedules(
            task=task,
            instrument=instr,
            values=values,
            factor_schedule_method=factor_schedule_method,
            save=save
        )

        return instr

    def create_accrual_calculation_schedules(self, task, instrument, values, accrual_calculation_schedule_method=None,
                                             save=False):
        return []

    def create_factor_schedules(self, task, instrument, values, factor_schedule_method=None, save=False):
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
