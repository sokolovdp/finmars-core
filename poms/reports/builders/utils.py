import sys

from datetime import date

empty = object()


def check_int_min(val):
    return val if val is not None else sys.maxsize


def check_int_max(val):
    return val if val is not None else -sys.maxsize


def check_date_min(val):
    return val if val is not None else date.min


def check_date_max(val):
    return val if val is not None else date.max


def check_val(obj, val, attr, default=None):
    if val is empty:
        if callable(attr):
            val = attr()
        else:
            val = getattr(obj, attr, None)
    if val is None:
        return default
    return val