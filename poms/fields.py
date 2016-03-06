from __future__ import unicode_literals

from decimal import Decimal

import pycountry
import pytz
from django.conf import settings
from django.db.models import CharField, DecimalField
from django.utils.translation import ugettext_lazy as _

from poms.validators import PhoneNumberValidator

LANGUAGE_MAX_LENGTH = 5
CURRENCY_MAX_LENGTH = 3
MONEY_MAX_DIGITS = 14
MONEY_MAX_DECIMAL_PLACES = 4
PHONENUMBER_MAX_LENGTH = 20
TIMEZONE_MAX_LENGTH = 20

money_zero = Decimal('0')

COUNTRY_CHOICES = sorted(list((c.alpha2, '%s: %s' % (c.alpha2, c.name)) for c in pycountry.countries))
CURRENCY_CHOICES = sorted(list((c.letter, '%s: %s' % (c.letter, c.name)) for c in pycountry.currencies))
TIMEZONE_CHOICES = sorted(list((k, k) for k in pytz.all_timezones))
TIMEZONE_COMMON_CHOICES = sorted(list((k, k) for k in pytz.common_timezones))


class LanguageField(CharField):
    description = _("Language")

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = kwargs.get('max_length', LANGUAGE_MAX_LENGTH)
        kwargs['choices'] = kwargs.get('choices', settings.LANGUAGES)
        kwargs['default'] = kwargs.get('default', settings.LANGUAGE_CODE)
        super(LanguageField, self).__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(LanguageField, self).deconstruct()
        return name, path, args, kwargs


class CurrencyField(CharField):
    description = _("Currency")

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = kwargs.get('max_length', CURRENCY_MAX_LENGTH)
        kwargs['choices'] = kwargs.get('choices', CURRENCY_CHOICES)
        kwargs['default'] = kwargs.get('default', settings.CURRENCY_CODE)
        super(CurrencyField, self).__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(CurrencyField, self).deconstruct()
        return name, path, args, kwargs


class TimezoneField(CharField):
    description = _("Timezone")

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = kwargs.get('max_length', TIMEZONE_MAX_LENGTH)
        kwargs['choices'] = kwargs.get('choices', TIMEZONE_CHOICES)
        super(TimezoneField, self).__init__(*args, **kwargs)


class CountryField(CharField):
    description = _("Timezone")

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = kwargs.get('max_length', 2)
        kwargs['choices'] = kwargs.get('choices', COUNTRY_CHOICES)
        super(CountryField, self).__init__(*args, **kwargs)


class SimpleMoneyField(DecimalField):
    description = _("Money")

    def __init__(self, *args, **kwargs):
        kwargs['max_digits'] = kwargs.get('max_digits', MONEY_MAX_DIGITS)
        kwargs['decimal_places'] = kwargs.get('decimal_places', MONEY_MAX_DECIMAL_PLACES)
        kwargs['null'] = kwargs.get('null', False)
        kwargs['blank'] = kwargs.get('blank', False)
        if not kwargs['null']:
            kwargs['default'] = kwargs.get('default', money_zero)
        super(SimpleMoneyField, self).__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(SimpleMoneyField, self).deconstruct()
        # if kwargs.get('max_digits', -1) != MONEY_MAX_DIGITS:
        #     kwargs['max_digits'] = MONEY_MAX_DIGITS
        # if kwargs.get('decimal_places', -1) != MONEY_MAX_DECIMAL_PLCAES:
        #     kwargs['decimal_places'] = MONEY_MAX_DECIMAL_PLCAES
        return name, path, args, kwargs

        # def get_internal_type(self):
        #     return "MoneyField"


class PhoneNumberField(CharField):
    description = _("Phone number")
    default_validators = [PhoneNumberValidator()]

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = kwargs.get('max_length', PHONENUMBER_MAX_LENGTH)
        super(PhoneNumberField, self).__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(PhoneNumberField, self).deconstruct()
        # print('deconstruct', 'max_length', '->', kwargs.get('max_length', None))
        # if kwargs.get('max_length', -1) != LANGUAGE_MAX_LENGTH:
        #     kwargs['max_length'] = LANGUAGE_MAX_LENGTH
        return name, path, args, kwargs

# def get_currency_field_name(name):
#     return '%s_currency' % name
#
#
# def get_currency(value):
#     """
#     Extracts currency from value.
#     """
#     if isinstance(value, Money):
#         return value.currency
#     elif isinstance(value, (list, tuple)):
#         return value[0]
#
#
# def validate_money_value(value):
#     """
#     Valid value for money are:
#       - Single numeric value
#       - Money instances
#       - Pairs of numeric value and currency. Currency can't be None.
#     """
#     # if isinstance(value, (list, tuple)) and (len(value) != 2 or value[1] is None):
#     #     raise ValidationError(
#     #         'Invalid value for MoneyField: %(value)s.',
#     #         code='invalid',
#     #         params={'value': value},
#     #     )
#     pass
#
#
# class MoneyFieldProxy(object):
#
#     def __init__(self, field):
#         self.field = field
#         self.currency_field_name = get_currency_field_name(self.field.name)
#
#     def _money_from_obj(self, obj):
#         amount = obj.__dict__[self.field.name]
#         currency = obj.__dict__[self.currency_field_name]
#         if amount is None:
#             return None
#         return Money(amount=amount, currency=currency)
#
#     def __get__(self, obj, type=None):
#         if obj is None:
#             raise AttributeError('Can only be accessed via an instance.')
#         if isinstance(obj.__dict__[self.field.name], BaseExpression):
#             return obj.__dict__[self.field.name]
#         if not isinstance(obj.__dict__[self.field.name], Money):
#             obj.__dict__[self.field.name] = self._money_from_obj(obj)
#         return obj.__dict__[self.field.name]
#
#     def __set__(self, obj, value):  # noqa
#         if isinstance(value, BaseExpression):
#             # validate_money_expression(obj, value)
#             # prepare_expression(value)
#             raise RuntimeError()
#         else:
#             validate_money_value(value)
#             currency = get_currency(value)
#             if currency:
#                 self.set_currency(obj, currency)
#             value = self.field.to_python(value)
#         obj.__dict__[self.field.name] = value
#
#     def set_currency(self, obj, value):
#         # we have to determine whether to replace the currency.
#         # i.e. if we do the following:
#         # .objects.get_or_create(money_currency='EUR')
#         # then the currency is already set up, before this code hits
#         # __set__ of MoneyField. This is because the currency field
#         # has less creation counter than money field.
#         object_currency = obj.__dict__[self.currency_field_name]
#         default_currency = str(self.field.default_currency)
#         if object_currency != value and (object_currency == default_currency or value != default_currency):
#             # in other words, update the currency only if it wasn't
#             # changed before.
#             setattr(obj, self.currency_field_name, value)
#
#
# class MoneyCurrencyField(CurrencyField):
#     description = _("Currency for money")
#
#     def __init__(self, money_field=None, *args, **kwargs):
#         self.money_field = money_field
#         super(MoneyCurrencyField, self).__init__(*args, **kwargs)
#
#     # def get_internal_type(self):
#     #     return 'CharField'
#
#     def contribute_to_class(self, cls, name, virtual_only=False):
#         if name not in [f.name for f in cls._meta.fields]:
#             super(MoneyCurrencyField, self).contribute_to_class(cls, name)
#
#
# class MoneyField(DecimalField):
#     description = _("Money")
#
#     def __init__(self, *args, **kwargs):
#         kwargs['max_digits'] = kwargs.get('max_digits', MONEY_MAX_DIGITS)
#         kwargs['decimal_places'] = kwargs.get('decimal_places', MONEY_MAX_DECIMAL_PLACES)
#         kwargs['null'] = kwargs.get('null', False)
#         kwargs['blank'] = kwargs.get('blank', False)
#         default = kwargs.get('default')
#         if default is None:
#             if not kwargs['blank']:
#                 default = Money(currency='XXX')
#         elif isinstance(default, (int, float, str, Decimal)):
#             default = Money(amount=default, currency='XXX')
#         kwargs['default'] = default
#         super(MoneyField, self).__init__(*args, **kwargs)
#
#     def to_python(self, value):
#         if isinstance(value, Expression):
#             return value
#         if isinstance(value, Money):
#             value = value.amount
#         # if isinstance(value, tuple):
#         #     value = value[0]
#         return super(MoneyField, self).to_python(value)
#
#     def get_internal_type(self):
#         return 'DecimalField'
#
#     def contribute_to_class(self, cls, name, virtual_only=False):
#         cls._meta.has_money_field = True
#
#         c_field_name = get_currency_field_name(name)
#         c_field = MoneyCurrencyField(default='XXX', editable=True, choices=settings.CURRENCIES)
#         c_field.creation_counter = self.creation_counter
#         cls.add_to_class(c_field_name, c_field)
#
#         super(MoneyField, self).contribute_to_class(cls, name)
#
#         setattr(cls, self.name, MoneyFieldProxy(self))
#
#     def get_db_prep_save(self, value, connection):
#         if isinstance(value, Expression):
#             return value
#         if isinstance(value, Money):
#             value = value.amount
#         return super(MoneyField, self).get_db_prep_save(value, connection)
#
#     def get_db_prep_lookup(self, lookup_type, value, connection,
#                            prepared=False):
#         # if lookup_type not in SUPPORTED_LOOKUPS:
#         #     raise NotSupportedLookup(lookup_type)
#         value = self.get_db_prep_save(value, connection)
#         return super(MoneyField, self).get_db_prep_lookup(lookup_type, value, connection, prepared)
#
#     def value_to_string(self, obj):
#         value = self._get_val_from_obj(obj)
#         return self.get_prep_value(value)
#
#     def deconstruct(self):
#         name, path, args, kwargs = super(MoneyField, self).deconstruct()
#         # if kwargs.get('default', None) is not None:
#         #     kwargs['default'] = kwargs['default'].amount
#         if self.default is not None:
#             kwargs['default'] = self.default.amount
#         return name, path, args, kwargs
