from __future__ import unicode_literals, print_function, division

import ast
import collections
import datetime
import random
import time

import simpleeval
from django.utils import numberformat

from poms.common.utils import date_now, isclose


class InvalidExpression(Exception):
    def __init__(self, e):
        super(InvalidExpression, self).__init__(e)
        self.message = getattr(e, "message", str(e))


def _check_string(a):
    if not isinstance(a, str):
        raise InvalidExpression('Value error')


def _check_number(a):
    if not isinstance(a, (int, float)):
        raise InvalidExpression('Value error')


def _check_date(a):
    if not isinstance(a, datetime.date):
        raise InvalidExpression('Value error')


def _check_timedelta(a):
    if not isinstance(a, datetime.timedelta):
        raise InvalidExpression('Value error')


def _str(a):
    return str(a)


def _int(a):
    return int(a)


def _float(a):
    return float(a)


def _round(number):
    _check_number(number)
    return round(number)


def _trunc(number):
    _check_number(number)
    return int(number)


def _iff(expr, a, b):
    return a if expr else b


def _isclose(a, b, rel_tol=1e-09, abs_tol=0.0):
    _check_number(a)
    _check_number(b)
    return isclose(a, b, rel_tol=rel_tol, abs_tol=abs_tol)


def _now():
    return date_now()


def _date(year, month=1, day=1):
    _check_number(year)
    _check_number(month)
    _check_number(day)
    return datetime.date(year=year, month=month, day=day)


def _days(days):
    if isinstance(days, datetime.timedelta):
        return days
    _check_number(days)
    return datetime.timedelta(days=days)


def _add_days(date, days):
    _check_date(date)
    if not isinstance(days, datetime.timedelta):
        _check_number(days)
        days = datetime.timedelta(days=days)
    return date + days


def _add_weeks(date, weeks):
    _check_date(date)
    if not isinstance(weeks, datetime.timedelta):
        _check_number(weeks)
        weeks = datetime.timedelta(weeks=weeks)
    return date + weeks


def _add_workdays(date, workdays, only_workdays=True):
    _check_date(date)
    _check_number(workdays)

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
    if date is None:
        return ''
    _check_date(date)
    if format is None:
        format = '%Y-%m-%d'
    _check_string(format)
    return date.strftime(format)


def _parse_date(date_string, format=None):
    if not date_string:
        return None
    _check_string(date_string)
    if format is None:
        format = '%Y-%m-%d'
    _check_string(format)
    return datetime.datetime.strptime(date_string, format).date()


def _format_number(number, decimal_sep='.', decimal_pos=None, grouping=3, thousand_sep='', use_grouping=False):
    _check_number(number)
    if decimal_sep is not None:
        _check_string(decimal_sep)
    if decimal_pos is not None:
        _check_number(decimal_pos)
    if grouping is not None:
        _check_number(grouping)
    if thousand_sep is not None:
        _check_string(thousand_sep)
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
    _check_date(date)
    _check_date(date1)
    _check_date(date2)
    _check_number(value1)
    _check_number(value2)
    if isclose(value1, value2):
        return value1
    if date1 == date2:
        if isclose(value1, value2):
            return value1
        raise ValueError()
    if date < date1:
        return 0.0
    if date == date1:
        return value1
    if date > date2:
        return 0.0
    if date == date2:
        return value2
    d = 1.0 * (date - date1).days / (date2 - date1).days
    return value1 + d * (value2 - value1)


def _random():
    return random.random()


DEFAULT_FUNCTIONS = {
    'str': _str,
    'int': _int,
    'float': _float,
    'round': _round,
    'trunc': _trunc,
    'iff': _iff,
    'isclose': _isclose,
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
    'random': _random,
}

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

class SimpleEval2(object):  # pylint: disable=too-few-public-methods
    expr = ''

    def __init__(self, operators=None, functions=None, names=None):
        '''
            Create the evaluator instance.  Set up valid operators (+,-, etc)
            functions (add, random, get_val, whatever) and names. '''

        if not operators:
            operators = simpleeval.DEFAULT_OPERATORS
        if not functions:
            functions = DEFAULT_FUNCTIONS
        if not names:
            names = simpleeval.DEFAULT_NAMES

        self.operators = operators
        self.functions = functions
        self.names = deep_value(names)

    @staticmethod
    def is_valid(expr):
        try:
            ast.parse(expr)
        except (SyntaxError, ValueError):
            return False
        return True

    @staticmethod
    def try_parse(expr):
        try:
            ast.parse(expr)
        except (SyntaxError, ValueError) as e:
            raise InvalidExpression(e)

    def eval(self, expr):
        ''' evaluate an expresssion, using the operators, functions and
            names previously set up. '''

        # set a copy of the expression aside, so we can give nice errors...

        self.expr = expr

        # and evaluate:
        try:
            return self._eval(ast.parse(expr).body[0].value)
        except Exception as e:
            if isinstance(e, InvalidExpression):
                raise e
            else:
                raise InvalidExpression(e)

    def _eval(self, node):
        ''' The internal eval function used on each node in the parsed tree. '''

        # literals:

        if isinstance(node, ast.Num):  # <number>
            return node.n

        elif isinstance(node, ast.Str):  # <string>
            if len(node.s) > simpleeval.MAX_STRING_LENGTH:
                raise simpleeval.StringTooLong("String Literal in statement is too long! ({0}, when {1} is max)".format(
                    len(node.s), simpleeval.MAX_STRING_LENGTH))
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
                raise simpleeval.InvalidExpression("Binary operation does't support string")
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
            try:
                f = self.functions[node.func.id]
                f_args = [self._eval(a) for a in node.args]
                f_kwargs = {k.arg: self._eval(k.value) for k in node.keywords}
                return f(*f_args, **f_kwargs)
            except KeyError:
                #     raise FunctionNotDefined(node.func.id, self.expr)
                raise

        # variables/names:
        elif isinstance(node, ast.Name):  # a, b, c...
            try:
                # This happens at least for slicing
                # This is a safe thing to do because it is impossible
                # that there is a true exression assigning to none
                # (the compiler rejects it, so you can't even pass that to ast.parse)
                if node.id == "None":
                    return None
                if node.id == "context" or node.id == "CONTEXT" and isinstance(self.names, dict):
                    return self.names
                if isinstance(self.names, dict):
                    return self.names[node.id]
                if callable(self.names):
                    return self.names(node.id)
                raise InvalidExpression(
                    'Trying to use name (variable) "%s" when no "names" defined for  evaluator' % (node.id,))
            except KeyError:
                raise simpleeval.NameNotDefined(node.id, self.expr)

        elif isinstance(node, ast.Subscript):  # b[1]
            return self._eval(node.value)[self._eval(node.slice)]

        elif isinstance(node, ast.Attribute):  # a.b.c
            try:
                return self._eval(node.value)[node.attr]
            except (KeyError, TypeError):
                pass

            # # Maybe the base object is an actual object, not just a dict
            # try:
            #     return getattr(self._eval(node.value), node.attr)
            # except (AttributeError, TypeError):
            #     pass

            # If it is neither, raise an exception
            raise simpleeval.AttributeDoesNotExist(node.attr, self.expr)
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

        elif isinstance(node, (ast.List, ast.Tuple)):
            d = []
            for v in node.elts:
                v = self._eval(v)
                d.append(v)
            if isinstance(node, ast.Tuple):
                return tuple(d)
            return d

        else:
            raise simpleeval.FeatureNotAvailable("Sorry, {0} is not available in this "
                                                 "evaluator".format(type(node).__name__))


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


def safe_eval(s, names=None, functions=None):
    try:
        return SimpleEval2(names=names, functions=functions).eval(s)
    except (simpleeval.InvalidExpression, KeyError, AttributeError) as e:
        raise InvalidExpression(e)


def deep_dict(data):
    ret = {}
    for k, v in data.items():
        ret[k] = deep_value(v)
    return ret


def deep_list(data):
    ret = []
    for v in data:
        ret.append(deep_value(v))
    return ret


def deep_tuple(data):
    return tuple(deep_list(data))


def deep_value(data):
    if isinstance(data, (dict, collections.OrderedDict)):
        return deep_dict(data)
    if isinstance(data, list):
        return deep_list(data)
    if isinstance(data, tuple):
        return deep_tuple(data)
    return data


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
    }

    # print(safe_eval('(1).__class__.__bases__', names=names))
    # print(safe_eval('{"a":1, "b":2}'))
    # print(safe_eval('[1,]'))
    # print(safe_eval('(1,)'))
    # print(safe_eval('parse_date("2000-01-01") + days(100)'))
    # print(safe_eval('simple_price(parse_date("2000-01-02"), parse_date("2000-01-01"), 0, parse_date("2000-04-10"), 100)'))
    # print(safe_eval('simple_price("2000-01-02", "2000-01-01", 0, "2000-04-10", 100)'))
    # print(safe_eval('v0 * 10', names=names))
    # print(safe_eval('context["v0"] * 10', names=names))

    print(safe_eval('format_date(now(), format="%d-%m-%Y")'))


    def demo():
        from poms.instruments.models import Instrument
        from poms.transactions.models import Transaction
        from poms.common.formula_serializers import EvalInstrumentSerializer, EvalTransactionSerializer

        def play(expr, names=None):
            try:
                res = safe_eval(expr, names=names)
            except InvalidExpression as e:
                res = "<ERROR1: %s>" % e.message
                time.sleep(1)
                raise e
            except Exception as e:
                res = "<ERROR2: %s>" % e
            print("\t%-60s -> %s" % (expr, res))

        names = {
            "v0": 1.00001,
            "v1": "str",
            "v2": {"id": 1, "name": "V2", "trn_code": 12354, "num": 1.234},
            "v3": [{"id": 2, "name": "V31"}, {"id": 3, "name": "V32"}, ],
            "instr": collections.OrderedDict(EvalInstrumentSerializer(instance=Instrument.objects.first()).data),
            "trns": [collections.OrderedDict(EvalTransactionSerializer(instance=t).data)
                     for t in Transaction.objects.all()[:2]],

        }
        print("test variables:\n", names)
        print("test variables:\n", deep_value(names))
        # for n in sorted(six.iterkeys(names)):
        #     print(n, "\n")
        #     pprint.pprint(names[n])
        #     # print("\t%s -> %s" % (n, json.dumps(names[n], sort_keys=True, indent=2)))

        print("simple:")
        play("2 * 2 + 2", names)
        play("2 * (2 + 2)", names)
        play("16 ** 16", names)
        play("5 / 2", names)
        play("5 % 2", names)

        print()
        print("with variables:")
        play("v0 + 1", names)
        play("v1 + ' & ' + str(v0)", names)
        play("v2.name", names)
        play("v2.num * 3", names)
        play("v3[1].name", names)
        play("v3[1].name", names)
        play("instr.name", names)
        play("instr.instrument_type.id", names)
        play("instr.instrument_type.user_code", names)

        play("instr.price_multiplier", names)
        play("instr['price_multiplier']", names)
        play("context['instr']", names)
        play("context['instr'].price_multiplier", names)
        play("context['instr']['price_multiplier']", names)

        print()
        print("functions: ")
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
        # print(repr(r))
        # print(add_workdays(datetime.date(2016, 6, 15), 3, only_workdays=False))
        # print(add_workdays(datetime.date(2016, 6, 15), 4, only_workdays=False))
        # print(add_workdays(datetime.date(2016, 6, 15), 3))
        # print(add_workdays(datetime.date(2016, 6, 15), 4))


        # demo()
