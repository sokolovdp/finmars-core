from __future__ import unicode_literals

from functools import lru_cache

import pytz
from babel import Locale
from babel.dates import get_timezone, get_timezone_gmt, get_timezone_name
from django.conf import settings
from django.utils import translation, timezone
from rest_framework import status
from rest_framework.response import Response

from poms.api.serializers import LanguageSerializer, Language, TimezoneSerializer, Timezone, ExpressionSerializer
from poms.common.views import AbstractViewSet

_languages = [Language(code, name) for code, name in settings.LANGUAGES]


@lru_cache()
def _get_timezones(locale, now):
    locale = Locale(locale)
    timezones = []
    for code in pytz.common_timezones:
        tz = get_timezone(code)
        d = timezone.localtime(now, tz)
        tz_offset = get_timezone_gmt(datetime=d, locale=locale)[3:]
        name = '%s - %s' % (
            tz_offset,
            get_timezone_name(tz, width='short', locale=locale),
        )
        timezones.append(Timezone(code, name, offset=d.utcoffset()))
    timezones = sorted(timezones, key=lambda v: v.offset)
    return timezones


def get_timezones():
    now = timezone.now()
    now = now.replace(minute=0, second=0, microsecond=0)
    # now = timezone.make_aware(datetime(2009, 10, 31, 23, 30))
    return _get_timezones(translation.get_language(), now)


class LanguageViewSet(AbstractViewSet):
    serializer_class = LanguageSerializer

    def list(self, request, *args, **kwargs):
        languages = _languages
        serializer = self.get_serializer(instance=languages, many=True)
        return Response(serializer.data)


class TimezoneViewSet(AbstractViewSet):
    serializer_class = TimezoneSerializer

    def list(self, request, *args, **kwargs):
        timezones = get_timezones()
        serializer = self.get_serializer(instance=timezones, many=True)
        return Response(serializer.data)


class ExpressionViewSet(AbstractViewSet):
    serializer_class = ExpressionSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
