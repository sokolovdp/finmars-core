from __future__ import unicode_literals, print_function, division

import ast
import datetime
import logging
import operator
import random
import time
from collections import OrderedDict

from django.utils import numberformat

from poms.common.utils import date_now, isclose

_l = logging.getLogger('poms.formula')

MAX_STRING_LENGTH = 100000
MAX_POWER = 4000000  # highest exponent
MAX_LEN = 100
MAX_ITERATIONS = 1000


class InvalidExpression(Exception):
    pass


class ExpressionSyntaxError(InvalidExpression):
    pass


class FunctionNotDefined(InvalidExpression):
    def __init__(self, name):
        self.message = "Function '%s' not defined" % name
        super(InvalidExpression, self).__init__(self.message)


class NameNotDefined(InvalidExpression):
    def __init__(self, name):
        self.message = "Name '%s' not defined" % name
        super(InvalidExpression, self).__init__(self.message)


class AttributeDoesNotExist(InvalidExpression):
    def __init__(self, attr):
        self.message = "Attribute '%s' does not exist in expression" % attr
        super(AttributeDoesNotExist, self).__init__(self.message)


# def _check_string(a):
#     if not isinstance(a, str):
#         raise InvalidExpression('Value error')


# def _check_number(a):
#     if not isinstance(a, (int, float)):
#         raise InvalidExpression('Value error')


# def _check_date(a):
#     if not isinstance(a, datetime.date):
#         raise InvalidExpression('Value error')


# def _check_timedelta(a):
#     if not isinstance(a, datetime.timedelta):
#         raise InvalidExpression('Value error')


def _str(a):
    return str(a)


def _upper(a):
    return str(a).upper()


def _lower(a):
    return str(a).lower()


def _contains(a, b):
    return str(b) in str(a)


def _int(a):
    return int(a)


def _float(a):
    return float(a)


def _round(a):
    return round(float(a))


def _trunc(a):
    return int(a)


def _isclose(a, b, rel_tol=1e-09, abs_tol=0.0):
    return isclose(float(a), float(b), rel_tol=float(rel_tol), abs_tol=float(abs_tol))


def _iff(test, a, b):
    return a if test else b


def _now():
    return date_now()


def _date(year, month=1, day=1):
    return datetime.date(year=int(year), month=int(month), day=int(day))


def _days(days):
    if isinstance(days, datetime.timedelta):
        return days
    return datetime.timedelta(days=int(days))


def _add_days(date, days):
    if not isinstance(date, datetime.date):
        date = _parse_date(str(date))
    # _check_date(date)
    if not isinstance(days, datetime.timedelta):
        days = datetime.timedelta(days=int(days))
    return date + days


def _add_weeks(date, weeks):
    if not isinstance(date, datetime.date):
        date = _parse_date(str(date))
    # _check_date(date)
    if not isinstance(weeks, datetime.timedelta):
        weeks = datetime.timedelta(weeks=int(weeks))
    return date + weeks


def _add_workdays(date, workdays, only_workdays=True):
    # _check_date(date)
    if not isinstance(date, datetime.date):
        date = _parse_date(str(date))
    workdays = int(workdays)
    weeks = int(workdays / 5)
    days_remainder = workdays % 5
    date = date + datetime.timedelta(weeks=weeks, days=days_remainder)
    if only_workdays:
        if date.weekday() == 5:
            return date + datetime.timedelta(days=2)
        if date.weekday() == 6:
            return date + datetime.timedelta(days=1)
    return date


def _format_date(date, format=None):
    if not isinstance(date, datetime.date):
        date = _parse_date(str(date))
    # _check_date(date)
    if format is None:
        format = '%Y-%m-%d'
    else:
        format = str(format)
    return date.strftime(format)


def _parse_date(date_string, format=None):
    if not date_string:
        return None
    date_string = str(date_string)
    if format is None:
        format = '%Y-%m-%d'
    else:
        format = str(format)
    return datetime.datetime.strptime(date_string, format).date()


def _format_number(number, decimal_sep='.', decimal_pos=None, grouping=3, thousand_sep='', use_grouping=False):
    number = float(number)
    decimal_sep = str(decimal_sep)
    if decimal_pos is not None:
        decimal_pos = int(decimal_pos)
    grouping = int(grouping)
    thousand_sep = str(thousand_sep)
    return numberformat.format(number, decimal_sep, decimal_pos=decimal_pos, grouping=grouping,
                               thousand_sep=thousand_sep, force_grouping=use_grouping)


def _parse_number(a):
    return float(a)


def _simple_price(date, date1, value1, date2, value2):
    if isinstance(date, str):
        date = _parse_date(date)
    if isinstance(date1, str):
        date1 = _parse_date(date1)
    if isinstance(date2, str):
        date2 = _parse_date(date2)
    if not isinstance(date, datetime.date):
        date = _parse_date(str(date))
    if not isinstance(date1, datetime.date):
        date1 = _parse_date(str(date1))
    if not isinstance(date2, datetime.date):
        date2 = _parse_date(str(date2))
    # _check_date(date)
    # _check_date(date1)
    # _check_date(date2)
    value1 = float(value1)
    value2 = float(value2)
    # _check_number(value1)
    # _check_number(value2)

    # if isclose(value1, value2):
    #     return value1
    # if date1 == date2:
    #     if isclose(value1, value2):
    #         return value1
    #     raise ValueError()
    # if date < date1:
    #     return 0.0
    # if date == date1:
    #     return value1
    # if date > date2:
    #     return 0.0
    # if date == date2:
    #     return value2
    if date1 <= date <= date2:
        d = 1.0 * (date - date1).days / (date2 - date1).days
        return value1 + d * (value2 - value1)
    return 0.0


def _random():
    return random.random()


def _op_safe_power(a, b):
    """ a limited exponent/to-the-power-of function, for safety reasons """
    if abs(a) > MAX_POWER or abs(b) > MAX_POWER:
        raise InvalidExpression("Sorry! I don't want to evaluate {0} ** {1}"
                                .format(a, b))
    return a ** b


def _op_safe_mult(a, b):
    """ limit the number of times a string can be repeated... """
    if isinstance(a, str) or isinstance(b, str):
        if isinstance(a, int) and a * len(b) > MAX_STRING_LENGTH:
            raise InvalidExpression("Sorry, a string that long is not allowed")
        elif isinstance(b, int) and b * len(a) > MAX_STRING_LENGTH:
            raise InvalidExpression("Sorry, a string that long is not allowed")

    return a * b


def _op_safe_add(a, b):
    """ string length limit again """
    if isinstance(a, str) and isinstance(b, str):
        if len(a) + len(b) > MAX_STRING_LENGTH:
            raise InvalidExpression("Sorry, adding those two strings would"
                                    " make a too long string.")
    return a + b


def _op_in(a, b):
    return a in b


class SimpleEval2(object):
    def __init__(self, names=None):
        self.expr = None

        self.operators = {
            ast.Add: _op_safe_add,
            ast.Sub: operator.sub,
            ast.Mult: _op_safe_mult,
            ast.Div: operator.truediv,
            ast.Pow: _op_safe_power,
            ast.Mod: operator.mod,
            ast.Eq: operator.eq,
            ast.NotEq: operator.ne,
            ast.Gt: operator.gt,
            ast.Lt: operator.lt,
            ast.GtE: operator.ge,
            ast.LtE: operator.le,
            ast.USub: operator.neg,
            ast.UAdd: operator.pos,
            ast.In: _op_in,
        }

        self.functions = {
            'str': _str,
            'upper': _upper,
            'lower': _lower,
            'contains': _contains,

            'int': _int,
            'float': _float,
            'round': _round,
            'trunc': _trunc,
            'isclose': _isclose,
            'random': _random,

            'iff': _iff,

            'now': _now,
            'date': _date,
            'days': _days,
            'add_days': _add_days,
            'add_weeks': _add_weeks,
            'add_workdays': _add_workdays,
            'format_date': _format_date,
            'parse_date': _parse_date,

            'format_number': _format_number,
            'parse_number': _parse_number,

            'simple_price': _simple_price,

            'globals': lambda: self.names if isinstance(self.names, (dict, OrderedDict)) else {},
            'locals': lambda: self.local_names,
        }
        self.local_functions = {}
        # self.names = deep_value(names) if names else {}
        self.names = names or {}
        # self.names.update({"True": True, "False": False, "None": None})
        self.local_names = None
        self.state = None
        self.result = None

    @staticmethod
    def is_valid(expr):
        if expr:
            try:
                ast.parse(expr)
            except (KeyError, AttributeError, TypeError, ValueError):
                return False
            except Exception:
                return False
        return True

    @staticmethod
    def try_parse(expr):
        if expr:
            try:
                ast.parse(expr)
            except (KeyError, AttributeError, TypeError, ValueError) as e:
                raise InvalidExpression(e)
            except Exception as e:
                raise InvalidExpression(e)
        else:
            raise InvalidExpression('Empty value')

    def eval(self, expr):
        # set a copy of the expression aside, so we can give nice errors...
        self.local_names = {}
        self.state = {}
        self.result = None

        try:
            if expr:
                self.expr = expr

                try:
                    self.result = self._eval_stmt(ast.parse(expr).body)
                    return self.result
                except InvalidExpression:
                    raise
                except SyntaxError as e:
                    raise ExpressionSyntaxError(e)
                except Exception as e:
                    raise InvalidExpression(e)
            else:
                raise InvalidExpression('Empty value')
        except InvalidExpression:
            raise
        except (KeyError, AttributeError, TypeError, ValueError) as e:
            raise InvalidExpression(e)
        except Exception as e:
            raise InvalidExpression(e)

    def _eval_stmt(self, body):
        ret = None

        for node in body:
            if isinstance(node, ast.Assign):
                val = self._eval(node.value)
                for t in node.targets:
                    if isinstance(t, ast.Name):
                        self.local_names[t.id] = val
                    else:
                        raise InvalidExpression('Invalid assign')
                ret = val

            elif isinstance(node, ast.If):
                ret = self._eval_stmt(node.body) if self._eval(node.test) else self._eval_stmt(node.orelse)

            elif isinstance(node, ast.For):
                for val in self._eval(node.iter):
                    self.local_names[node.target.id] = val
                    ret = self._eval_stmt(node.body)

            elif isinstance(node, ast.While):
                iter = 0
                while self._eval(node.test):
                    ret = self._eval_stmt(node.body)
                    iter += 1
                    if iter > MAX_ITERATIONS:
                        raise InvalidExpression('Max iterations')

            elif isinstance(node, ast.FunctionDef):
                self.local_functions[node.name] = node

            else:
                ret = self._eval(node.value)

        return ret

    def _eval(self, node):
        if isinstance(node, ast.Num):  # <number>
            return node.n

        elif isinstance(node, ast.Str):  # <string>
            if len(node.s) > MAX_STRING_LENGTH:
                raise InvalidExpression(
                    "String Literal in statement is too long! (%s, when %s is max)" % (len(node.s), MAX_STRING_LENGTH))
            return node.s

        # python 3 compatibility:
        elif hasattr(ast, 'NameConstant') and isinstance(node, ast.NameConstant):  # <bool>
            return node.value

        # operators, functions, etc:

        elif isinstance(node, ast.UnaryOp):  # - and + etc.
            return self.operators[type(node.op)](self._eval(node.operand))

        elif isinstance(node, ast.BinOp):  # <left> <operator> <right>
            # return self.operators[type(node.op)](self._eval(node.left), self._eval(node.right))
            l = self._eval(node.left)
            r = self._eval(node.right)
            # if isinstance(node.op, ast.Mult) and isinstance(l, str):
            #     raise simpleeval.InvalidExpression("Invalid first argument")
            # if isinstance(node.op, ast.Mod) and isinstance(l, str):
            #     raise simpleeval.InvalidExpression("Invalid first argument")
            if isinstance(node.op, (ast.Mult, ast.Mod,)) and isinstance(l, str):
                raise InvalidExpression("Binary operation does't support string")
            return self.operators[type(node.op)](l, r)

        elif isinstance(node, ast.BoolOp):  # and & or...
            if isinstance(node.op, ast.And):
                return all((self._eval(v) for v in node.values))
            elif isinstance(node.op, ast.Or):
                return any((self._eval(v) for v in node.values))

        elif isinstance(node, ast.Compare):  # 1 < 2, a == b...
            return self.operators[type(node.ops[0])](self._eval(node.left), self._eval(node.comparators[0]))

        elif isinstance(node, ast.IfExp):  # x if y else z
            return self._eval(node.body) if self._eval(node.test) else self._eval(node.orelse)

        elif isinstance(node, ast.Call):  # function...
            # if node.func.id == 'locals':
            #     return self.local_names
            # if node.func.id == 'globals':
            #     return self.names

            if node.func.id in self.functions:
                f = self.functions[node.func.id]
                f_args = [self._eval(a) for a in node.args]
                f_kwargs = {k.arg: self._eval(k.value) for k in node.keywords}
                return f(*f_args, **f_kwargs)

            if node.func.id in self.local_functions:
                f = self.local_functions[node.func.id]
                f_args = [self._eval(a) for a in node.args]
                f_kwargs = {k.arg: self._eval(k.value) for k in node.keywords}

                for i, val in enumerate(f_args):
                    # f_kwargs.setdefault(k, v)
                    name = f.args.args[i].arg
                    f_kwargs[name] = val

                defaults_args_correction = len(f.args.args) - len(f.args.defaults)
                for i, arg in enumerate(f.args.args):
                    if arg.arg not in f_kwargs:
                        val = self._eval(f.args.defaults[i - defaults_args_correction])
                        f_kwargs[arg.arg] = val

                local_names = self.local_names.copy()

                self.local_names.update(f_kwargs)
                ret = self._eval_stmt(f.body)

                self.local_names = local_names

                return ret

            raise FunctionNotDefined(node.func.id)

        # variables/names:
        elif isinstance(node, ast.Name):  # a, b, c...
            try:
                # This happens at least for slicing
                # This is a safe thing to do because it is impossible
                # that there is a true expression assigning to none
                # (the compiler rejects it, so you can't even pass that to ast.parse)
                if node.id == 'None':
                    return None

                if node.id == 'True':
                    return True
                if node.id == 'False':
                    return False

                if node.id in self.local_names:
                    return self.local_names[node.id]

                if isinstance(self.names, (dict, OrderedDict)):
                    return self.names[node.id]
                elif callable(self.names):
                    return self.names(node.id)

                raise NameNotDefined(node.id)
            except KeyError:
                raise NameNotDefined(node.id)

        elif isinstance(node, ast.Subscript):  # b[1]
            val = self._eval(node.value)
            return val[self._eval(node.slice)]

        elif isinstance(node, ast.Attribute):  # a.b.c
            val = self._eval(node.value)

            if isinstance(val, datetime.date):
                if node.attr == 'year':
                    return val.year
                if node.attr == 'month':
                    return val.month
                if node.attr == 'day':
                    return val.day

            if isinstance(val, datetime.timedelta):
                if node.attr == 'days':
                    return val.days

            if isinstance(val, dict):
                try:
                    return val[node.attr]
                except (KeyError, TypeError):
                    pass

            # # Maybe the base object is an actual object, not just a dict
            # try:
            #     return getattr(self._eval(node.value), node.attr)
            # except (AttributeError, TypeError):
            #     pass

            # If it is neither, raise an exception
            raise AttributeDoesNotExist(node.attr)
        elif isinstance(node, ast.Index):
            return self._eval(node.value)

        # elif isinstance(node, ast.Slice):
        #     lower = upper = step = None
        #     if node.lower is not None:
        #         lower = self._eval(node.lower)
        #     if node.upper is not None:
        #         upper = self._eval(node.upper)
        #     if node.step is not None:
        #         step = self._eval(node.step)
        #     return slice(lower, upper, step)

        elif isinstance(node, ast.Dict):
            d = {}
            for k, v in zip(node.keys, node.values):
                k = self._eval(k)
                v = self._eval(v)
                d[k] = v
            return d

        elif isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            d = []
            for v in node.elts:
                v = self._eval(v)
                d.append(v)
                if len(d) > MAX_LEN:
                    raise InvalidExpression('Max list length.')
            if isinstance(node, ast.Tuple):
                return tuple(d)
            elif isinstance(node, ast.Set):
                return set(d)
            else:
                return d

        else:
            raise InvalidExpression("Sorry, %s is not available in this evaluator" % type(node).__name__)


def is_valid(expr):
    return SimpleEval2.is_valid(expr)


def try_parse(expr):
    return SimpleEval2.try_parse(expr)


def validate(expr):
    from rest_framework.exceptions import ValidationError
    try:
        try_parse(expr)
    except InvalidExpression as e:
        raise ValidationError('Invalid expression: %s' % e)


def safe_eval(s, names=None):
    # _l.debug('> safe_eval: s="%s", names=%s, functions=%s',
    #          s, names, functions)
    se = SimpleEval2(names=names)
    ret = se.eval(s)
    # _l.debug('< safe_eval: s="%s", local_names=%s, local_functions=%s',
    #          ret, se.local_names, se.local_functions)
    return ret


# def deep_dict(data):
#     ret = {}
#     for k, v in data.items():
#         ret[k] = deep_value(v)
#     return ret
#
#
# def deep_list(data):
#     ret = []
#     for v in data:
#         ret.append(deep_value(v))
#     return ret
#
#
# def deep_tuple(data):
#     return tuple(deep_list(data))
#
#
# def deep_value(data):
#     if isinstance(data, (dict, collections.OrderedDict)):
#         return deep_dict(data)
#     if isinstance(data, list):
#         return deep_list(data)
#     if isinstance(data, tuple):
#         return deep_tuple(data)
#     return data


HELP = """
TYPES:

string: '' or ""
number: 1 or 1.0
boolean: True/False

hidden types
date: date object
timedelta: time delta object for operations with dates

OPERATORS:

    +, -, /, *, ==, !=, >, >=, <, <=


VARIABLES:

access to context value in formulas
    x * 10
    context['x'] * 10
    instrument.price_multiplier
    instrument['price_multiplier']
    context['instrument']['price_multiplier']


FUNCTIONS:

function description
    function_name(arg1, arg2=<default value for arg>)

example of function call->
    iff(d==now(), 1, 2)
    iff(d==now(), v1=1, v2=2)

supported functions:

str(a)
    any value to string
float(a)
    convert string to number
round(number)
    math round float
trunc(number)
    math truncate float
iff(expr, a, b)
    return a if x is True else v2
isclose(a, b)
    compare to float number to equality
now()
    current date
date(year, month=1, day=1)
    create date object
days(days)
    create timedelta object for operations with dates
    now() - days(10)
    now() + days(10)
add_days(date, days)
    same as date + days(x)
add_weeks(date, days)
    same as d + days(x * 7)
add_workdays(date, workdays)
    add "x" work days to d
format_date(date, format='%Y-%m-%d')
    format date, by default format is '%Y-%m-%d'
parse_date(date_string, format='%Y-%m-%d')
    parse date from string, by default format is '%Y-%m-%d'
format_number(number, decimal_sep='.', decimal_pos=None, grouping=3, thousand_sep='', use_grouping=False)
    decimal_sep: Decimal separator symbol (for example ".")
    decimal_pos: Number of decimal positions
    grouping: Number of digits in every group limited by thousand separator
    thousand_sep: Thousand separator symbol (for example ",")
    use_grouping: use thousand separator
parse_number(a)
    same as float(a)
simple_price(date, date1, value1, date2, value2)
    calculate price on date using 2 point
    date, date1, date2 - date or string in format '%Y-%m-%d'


DATE format string:
    %w 	Weekday as a decimal number, where 0 is Sunday and 6 is Saturday - 0, 1, ..., 6
    %d 	Day of the month as a zero-padded decimal number - 01, 02, ..., 31
    %m 	Month as a zero-padded decimal number - 01, 02, ..., 12
    %y 	Year without century as a zero-padded decimal number - 00, 01, ..., 99
    %Y 	Year with century as a decimal number - 1970, 1988, 2001, 2013
    %j 	Day of the year as a zero-padded decimal number - 001, 002, ..., 366
    %U 	Week number of the year (Sunday as the first day of the week) as a zero padded decimal number.
        All days in a new year preceding the first Sunday are considered to be in week 0. - 00, 01, ..., 53
    %W 	Week number of the year (Monday as the first day of the week) as a decimal number.
        All days in a new year preceding the first Monday are considered to be in week 0. - 00, 01, ..., 53
    %% 	A literal '%' character - %
"""

# %a 	Weekday as locale’s abbreviated name - Sun, Mon, ..., Sat (en_US)
# %A 	Weekday as locale’s full name - Sunday, Monday, ..., Saturday (en_US);
# %b 	Month as locale’s abbreviated name - Jan, Feb, ..., Dec (en_US)
# %B 	Month as locale’s full name  - January, February, ..., December (en_US);

if __name__ == "__main__":
    import os

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "poms_app.settings_dev_ai")
    import django

    django.setup()

    names = {
        "v0": 1.00001,
        "v1": "str",
        "v2": {
            "id": 1,
            "name": "V2",
            "code": 12354
        },
        "v3": [
            {
                "id": 2,
                "name": "V31"
            },
            {
                "id": 3,
                "name": "V32"
            },
        ],
        "v4": OrderedDict(
            [
                ("id", 3),
                ("name", "Lol"),
            ]
        ),
    }


    # _l.info(safe_eval('(1).__class__.__bases__', names=names))
    # _l.info(safe_eval('{"a":1, "b":2}'))
    # _l.info(safe_eval('[1,]'))
    # _l.info(safe_eval('(1,)'))
    # _l.info(safe_eval('{1,}'))
    # _l.info(safe_eval('parse_date("2000-01-01") + days(100)'))
    # _l.info(safe_eval(
    #     'simple_price(parse_date("2000-01-05"), parse_date("2000-01-01"), 0, parse_date("2000-04-10"), 100)'))
    # _l.info(safe_eval('simple_price("2000-01-05", "2000-01-01", 0, "2000-04-10", 100)'))
    # _l.info(safe_eval('simple_price("2000-01-02", "2000-01-01", 0, "2000-04-10", 100)'))
    # _l.info(safe_eval('v0 * 10', names=names))
    # _l.info(safe_eval('globals()["v0"] * 10', names=names))
    # _l.info(safe_eval('v2.id', names=names))
    # _l.info(safe_eval('v4.id', names=names))


    # _l.info(safe_eval('func1()'))
    # _l.info(safe_eval('name1'))
    # _l.info(safe_eval('name1.id', names={"name1": {'id':1}}))
    # _l.info(safe_eval('name1.id2', names={"name1": {'id':1}}))
    # _l.info(safe_eval('1+'))
    # _l.info(safe_eval('1 if 1 > 2 else 2'))
    # _l.info(safe_eval('"a" in "ab"'))

    # _l.info(safe_eval('a = 2 + 3'))
    #     _l.info(safe_eval('''
    # if 1 > 2:
    #     a = 2
    #     b = 3
    # else:
    #     a = 3
    #     b = 4
    # a * b
    # '''))


    #     _l.info(safe_eval('''
    # r = 0
    # for a in [1,2,3]:
    #     r = r + a
    # r + 0
    # '''))
    #     _l.info(safe_eval('''
    # r = 0
    # while r < 100:
    #     r = r + 1
    # r + 0
    # '''))
    #     _l.info(safe_eval('''
    # r = now()
    # i = 0
    # while i < 100:
    #     r = r + days(1)
    #     i = i + 1
    #     pass
    # r
    # '''))
    #     _l.info(safe_eval('''
    # def f1(a, b = 200, c = 300):
    #     r = a * b
    #     return r + c
    # f1(10, b = 20)
    # '''))

    # _l.info(safe_eval('y = now().year'))

    def demo():
        # from poms.common.formula_serializers import EvalInstrumentSerializer, EvalTransactionSerializer

        def play(expr, names=None):
            try:
                res = safe_eval(expr, names=names)
            except InvalidExpression as e:
                res = "<ERROR1: %s>" % e
                time.sleep(1)
                raise e
            except Exception as e:
                res = "<ERROR2: %s>" % e
            _l.info("\t%-60s -> %s" % (expr, res))

        from rest_framework.test import APIRequestFactory
        factory = APIRequestFactory()
        instrument_request = factory.get('/api/v1/instruments/instrument/1/', format='json')
        transactions_request = factory.get('/api/v1/transactions/transaction/', format='json')
        names = {
            "v0": 1.00001,
            "v1": "str",
            "v2": {"id": 1, "name": "V2", "trn_code": 12354, "num": 1.234},
            "v3": [{"id": 2, "name": "V31"}, {"id": 3, "name": "V32"}, ],
            "v4": OrderedDict(("id", 3), ("name", "Lol")),
            # "instr": OrderedDict(
            #     InstrumentSerializer(instance=Instrument.objects.first(),
            #                          context={'request': instrument_request}).data
            # ),
            # "trns": [
            #     OrderedDict(
            #         TransactionSerializer(instance=Transaction.objects.all(), many=True,
            #                               context={'request': transactions_request}).data
            #     )
            # ],

        }
        _l.info("test variables:\n", names)
        # for n in sorted(six.iterkeys(names)):
        #     _l.info(n, "\n")
        #     pprint.pprint(names[n])
        #     # print("\t%s -> %s" % (n, json.dumps(names[n], sort_keys=True, indent=2)))

        _l.info("simple:")
        play("2 * 2 + 2", names)
        play("2 * (2 + 2)", names)
        play("16 ** 16", names)
        play("5 / 2", names)
        play("5 % 2", names)

        _l.info('')
        _l.info("with variables:")
        play("v0 + 1", names)
        play("v1 + ' & ' + str(v0)", names)
        play("v2.name", names)
        play("v2.num * 3", names)
        play("v3[1].name", names)
        play("v3[1].name", names)
        play("globals()", names)
        play("globals()['v0']", names)
        # play("instr.name", names)
        # play("instr.instrument_type.id", names)
        # play("instr.instrument_type.user_code", names)
        # play("instr.price_multiplier", names)
        # play("instr['price_multiplier']", names)
        # play("globals()['instr']", names)
        # play("globals()['instr'].price_multiplier", names)
        # play("globals()['instr']['price_multiplier']", names)

        _l.info('')
        _l.info("functions: ")
        play("round(1.5)", names)
        play("trunc(1.5)", names)
        play("int(1.5)", names)
        play("now()", names)
        play("add_days(now(), 10)", names)
        play("add_workdays(now(), 10)", names)
        play("iff(1.001 > 1.002, 'really?', 'ok')", names)
        play("'really?' if 1.001 > 1.002 else 'ok'", names)
        play("'N' + format_date(now(), '%Y%m%d') + '/' + str(v2.trn_code)", names)

        play("format_date(now())", names)
        play("format_date(now(), '%Y/%m/%d')", names)
        play("format_date(now(), format='%Y/%m/%d')", names)
        play("format_number(1234.234)", names)
        play("format_number(1234.234, '.', 2)", names)

        # r = safe_eval3('"%r" % now()', names=names, functions=functions)
        # r = safe_eval('format_date(now(), "EEE, MMM d, yy")')
        # _l.info(repr(r))
        # _l.info(add_workdays(datetime.date(2016, 6, 15), 3, only_workdays=False))
        # _l.info(add_workdays(datetime.date(2016, 6, 15), 4, only_workdays=False))
        # _l.info(add_workdays(datetime.date(2016, 6, 15), 3))
        # _l.info(add_workdays(datetime.date(2016, 6, 15), 4))


        # demo()
