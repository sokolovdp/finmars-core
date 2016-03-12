from __future__ import unicode_literals

import pytz
from django.conf import settings
from django.db.models import CharField
from django.utils.translation import ugettext_lazy as _

LANGUAGE_MAX_LENGTH = 5
CURRENCY_MAX_LENGTH = 3
MONEY_MAX_DIGITS = 14
MONEY_MAX_DECIMAL_PLACES = 4
PHONENUMBER_MAX_LENGTH = 20
TIMEZONE_MAX_LENGTH = 20


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


class TimezoneField(CharField):
    description = _("Timezone")

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = kwargs.get('max_length', TIMEZONE_MAX_LENGTH)
        kwargs['choices'] = kwargs.get('choices', TIMEZONE_CHOICES)
        super(TimezoneField, self).__init__(*args, **kwargs)
