from __future__ import unicode_literals, print_function, division

import ast
import calendar
import datetime
import logging
import random
import time
from collections import OrderedDict

from dateutil import relativedelta
from django.utils import numberformat
from django.utils.functional import Promise

from poms.common.utils import date_now, isclose

_l = logging.getLogger('poms.formula')

MAX_STR_LEN = 2000
# MAX_EXPONENT = 4000000  # highest exponent
MAX_EXPONENT = 10000  # highest exponent
MAX_SHIFT = 1000
MAX_LEN = 1000


class InvalidExpression(Exception):
    pass


class ExpressionSyntaxError(InvalidExpression):
    pass


class ExpressionEvalError(InvalidExpression):
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


class _Break(InvalidExpression):
    pass


class _Return(InvalidExpression):
    def __init__(self, value):
        self.value = value
        super(_Return, self).__init__()


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


def _len(a):
    return len(a)


def _range(*args):
    return range(*args)


def _now():
    return date_now()


def _date(year, month=1, day=1):
    return datetime.date(year=int(year), month=int(month), day=int(day))


def _isleap(date_or_year):
    if isinstance(date_or_year, datetime.date):
        return calendar.isleap(date_or_year.year)
    else:
        return calendar.isleap(int(date_or_year))


def _days(days):
    return datetime.timedelta(days=int(days))


def _weeks(weeks):
    return datetime.timedelta(weeks=int(weeks))


def _months(months):
    return relativedelta.relativedelta(months=int(months))


def _timedelta(years=0, months=0, days=0, leapdays=0, weeks=0,
               year=None, month=None, day=None, weekday=None,
               yearday=None, nlyearday=None):
    return relativedelta.relativedelta(
        years=int(years),
        months=int(months),
        days=int(days),
        leapdays=int(leapdays),
        weeks=int(weeks),
        year=int(year) if year is not None else None,
        month=int(month) if month is not None else None,
        day=int(day) if day is not None else None,
        weekday=int(weekday) if weekday is not None else None,
        yearday=int(yearday) if yearday is not None else None,
        nlyearday=int(nlyearday) if nlyearday is not None else None,
    )


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


def _find_name(*args):
    for s in args:
        if s is not None:
            return str(s)
    return ''


def _random():
    return random.random()


def _print(message, *args, **kwargs):
    _l.debug(message, *args, **kwargs)


def _op_power(a, b):
    """ a limited exponent/to-the-power-of function, for safety reasons """
    if abs(a) > MAX_EXPONENT or abs(b) > MAX_EXPONENT:
        raise InvalidExpression("Invalid exponent, max exponent is %s" % MAX_EXPONENT)
    return a ** b


def _op_mult(a, b):
    # """ limit the number of times a string can be repeated... """
    # if isinstance(a, int) and a * len(b) > MAX_STRING_LENGTH:
    #         raise InvalidExpression("Sorry, a string that long is not allowed")
    #     elif isinstance(b, int) and b * len(a) > MAX_STRING_LENGTH:
    #         raise InvalidExpression("Sorry, a string that long is not allowed")
    if isinstance(a, str):
        raise TypeError("Can't convert '%s' object to str implicitly" % type(a).__name__)
    if isinstance(b, str):
        raise TypeError("Can't convert '%s' object to str implicitly" % type(b).__name__)
    return a * b


def _op_add(a, b):
    """ string length limit again """
    if isinstance(a, str) and isinstance(b, str) and len(a) + len(b) > MAX_STR_LEN:
        raise InvalidExpression("Sorry, adding those two strings would make a too long string.")
    return a + b


def _op_lshift(a, b):
    if b > MAX_SHIFT:
        raise InvalidExpression("Invalid left shift, max left shift is %s" % MAX_SHIFT)
    return a << b


OPERATORS = {
    ast.Is: lambda a, b: a is b,
    ast.IsNot: lambda a, b: a is not b,
    ast.In: lambda a, b: a in b,
    ast.NotIn: lambda a, b: a not in b,
    ast.Add: _op_add,
    ast.BitAnd: lambda a, b: a & b,
    ast.BitOr: lambda a, b: a | b,
    ast.BitXor: lambda a, b: a ^ b,
    ast.Div: lambda a, b: a / b,
    ast.FloorDiv: lambda a, b: a // b,
    ast.LShift: _op_lshift,
    ast.RShift: lambda a, b: a >> b,
    ast.Mult: _op_mult,
    ast.Pow: _op_power,
    ast.Sub: lambda a, b: a - b,
    ast.Mod: lambda a, b: a % b,
    ast.And: lambda a, b: a and b,
    ast.Or: lambda a, b: a or b,
    ast.Eq: lambda a, b: a == b,
    ast.Gt: lambda a, b: a > b,
    ast.GtE: lambda a, b: a >= b,
    ast.Lt: lambda a, b: a < b,
    ast.LtE: lambda a, b: a <= b,
    ast.NotEq: lambda a, b: a != b,
    ast.Invert: lambda a: ~a,
    ast.Not: lambda a: not a,
    ast.UAdd: lambda a: +a,
    ast.USub: lambda a: -a
}


# OPERATORS = {
#     ast.Add: _op_add,
#     ast.Sub: operator.sub,
#     ast.Mult: _op_mult,
#     ast.Div: operator.truediv,
#     ast.Pow: _op_power,
#     ast.Mod: operator.mod,
#     ast.Eq: operator.eq,
#     ast.NotEq: operator.ne,
#     ast.Gt: operator.gt,
#     ast.Lt: operator.lt,
#     ast.GtE: operator.ge,
#     ast.LtE: operator.le,
#     ast.USub: operator.neg,
#     ast.UAdd: operator.pos,
#     ast.In: _op_in,
#     ast.Is: operator.is_,
#     ast.IsNot: operator.is_not,
#     ast.Not: operator.not_,
# }


class _SysDef(object):
    def __init__(self, name, func):
        self.name = name
        self.func = func

    def __str__(self):
        return '<def %s>' % self.name

    def __repr__(self):
        return '<def %s>' % self.name

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)


class _UserDef(object):
    def __init__(self, parent, node):
        self.parent = parent
        self.node = node

    def __str__(self):
        return '<def %s>' % self.node.name

    def __repr__(self):
        return '<def %s>' % self.node.name

    def __call__(self, *args, **kwargs):
        kwargs = kwargs.copy()
        for i, val in enumerate(args):
            name = self.node.args.args[i].arg
            kwargs[name] = val

        offset = len(self.node.args.args) - len(self.node.args.defaults)
        for i, arg in enumerate(self.node.args.args):
            if arg.arg not in kwargs:
                val = self.parent._eval(self.node.args.defaults[i - offset])
                kwargs[arg.arg] = val

        save_table = self.parent._table
        try:
            self.parent._table = save_table.copy()
            self.parent._table.update(kwargs)
            try:
                ret = self.parent._eval(self.node.body)
            except _Return as e:
                ret = e.value
        finally:
            self.parent._table = save_table

        return ret


FUNCTIONS = [
    _SysDef('str', _str),
    _SysDef('upper', _upper),
    _SysDef('lower', _lower),
    _SysDef('contains', _contains),

    _SysDef('int', _int),
    _SysDef('float', _float),
    _SysDef('round', _round),
    _SysDef('trunc', _trunc),
    _SysDef('isclose', _isclose),
    _SysDef('random', _random),

    _SysDef('iff', _iff),
    _SysDef('len', _len),
    _SysDef('range', _range),

    _SysDef('now', _now),
    _SysDef('date', _date),
    _SysDef('isleap', _isleap),
    _SysDef('days', _days),
    _SysDef('weeks', _weeks),
    _SysDef('months', _months),
    _SysDef('timedelta', _timedelta),
    _SysDef('add_days', _add_days),
    _SysDef('add_weeks', _add_weeks),
    _SysDef('add_workdays', _add_workdays),
    _SysDef('format_date', _format_date),
    _SysDef('parse_date', _parse_date),

    _SysDef('format_number', _format_number),
    _SysDef('parse_number', _parse_number),

    _SysDef('simple_price', _simple_price),

    _SysDef('find_name', _find_name),
]

# FUNCTIONS = {
#     'str': _WrapDef('str', _str),
#     'upper': _WrapDef('upper', _upper),
#     'lower': _WrapDef('lower', _lower),
#     'contains': _WrapDef('contains', _contains),
#
#     'int': _WrapDef('int', _int),
#     'float': _WrapDef('float', _float),
#     'round': _WrapDef('round', _round),
#     'trunc': _WrapDef('trunc', _trunc),
#     'isclose': _WrapDef('isclose', _isclose),
#     'random': _WrapDef('random', _random),
#
#     'iff': _WrapDef('iff', _iff),
#     'len': _WrapDef('len', _len),
#     'range': _WrapDef('range', _range),
#
#     'now': _WrapDef('now', _now),
#     'date': _WrapDef('date', _date),
#     'isleap': _WrapDef('isleap', _isleap),
#     'days': _WrapDef('days', _days),
#     'weeks': _WrapDef('weeks', _weeks),
#     'months': _WrapDef('months', _months),
#     'timedelta': _WrapDef('timedelta', _timedelta),
#     'add_days': _WrapDef('add_days', _add_days),
#     'add_weeks': _WrapDef('add_weeks', _add_weeks),
#     'add_workdays': _WrapDef('add_workdays', _add_workdays),
#     'format_date': _WrapDef('format_date', _format_date),
#     'parse_date': _WrapDef('parse_date', _parse_date),
#
#     'format_number': _WrapDef('format_number', _format_number),
#     'parse_number': _WrapDef('parse_number', _parse_number),
#
#     'simple_price': _WrapDef('simple_price', _simple_price),
# }


empty = object()


class SimpleEval2(object):
    def __init__(self, names=None, max_time=None, add_print=False, allow_assign=False, now=None):
        self.max_time = max_time or 1  # one second
        # self.max_time = 10000000000
        self.start_time = 0
        self.tik_time = 0
        self.allow_assign = allow_assign

        self.expr = None
        self.expr_ast = None
        self.result = None

        _globals = {f.name: f for f in FUNCTIONS}
        if now is not None and callable(now):
            _globals['now'] = _SysDef('now', now)
        _globals['globals'] = _SysDef('globals', lambda: _globals)
        _globals['locals'] = _SysDef('locals', lambda: self._table)
        _globals['true'] = True
        _globals['false'] = False
        if names:
            for k, v in names.items():
                _globals[k] = v
        if add_print:
            _globals['print'] = _print

        self._table = _globals

    @staticmethod
    def try_parse(expr):
        if not expr:
            raise InvalidExpression('Empty expression')
        try:
            return ast.parse(expr)
        except SyntaxError as e:
            raise ExpressionSyntaxError(e)
        except Exception as e:
            raise InvalidExpression(e)

    @staticmethod
    def is_valid(expr):
        try:
            SimpleEval2.try_parse(expr)
            return True
        except:
            return False

    def find_name(self, name):
        try:
            return self._table[name]
        except KeyError:
            raise NameNotDefined(name)

    def eval(self, expr, names=None):
        if not expr:
            raise InvalidExpression('Empty expression')

        self.expr = expr
        self.expr_ast = SimpleEval2.try_parse(expr)

        save_table = self._table
        self._table = save_table.copy()
        if names:
            for k, v in names.items():
                self._table[k] = v
        try:
            self.start_time = time.time()
            self.result = self._eval(self.expr_ast.body)
            return self.result
        except InvalidExpression:
            raise
        except Exception as e:
            raise ExpressionEvalError(e)
        finally:
            self._table = save_table

    def _eval(self, node):
        # _l.info('%s - %s - %s', node, type(node), node.__class__)
        self.tik_time = time.time()
        if self.tik_time - self.start_time > self.max_time:
            raise InvalidExpression("Execution exceeded time limit, max runtime is %s" % self.max_time)

        # if isinstance(node, (list, tuple)):
        #     return self._on_many(node)
        #
        # elif isinstance(node, ast.Assign):
        #     return self._on_ast_Assign(node)
        #
        # elif isinstance(node, ast.If):
        #     return self._on_ast_If(node)
        #
        # elif isinstance(node, ast.For):
        #     return self._on_ast_For(node)
        #
        # elif isinstance(node, ast.While):
        #     return self._on_ast_While(node)
        #
        # elif isinstance(node, ast.Break):
        #     return self._on_ast_Break(node)
        #
        # elif isinstance(node, ast.FunctionDef):
        #     return self._on_ast_FunctionDef(node)
        #
        # elif isinstance(node, ast.Pass):
        #     return self._on_ast_Pass(node)
        #
        # elif isinstance(node, ast.Try):
        #     return self._on_ast_Try(node)
        #
        # elif isinstance(node, ast.Num):  # <number>
        #     return self._on_ast_Num(node)
        #
        # elif isinstance(node, ast.Str):  # <string>
        #     return self._on_ast_Str(node)
        #
        # # python 3 compatibility:
        # elif hasattr(ast, 'NameConstant') and isinstance(node, ast.NameConstant):  # <bool>
        #     return self._on_ast_NameConstant(node)
        #
        # elif isinstance(node, ast.Dict):
        #     return self._on_ast_Dict(node)
        #
        # elif isinstance(node, ast.List):
        #     return self._on_ast_List(node)
        #
        # elif isinstance(node, ast.Tuple):
        #     return self._on_ast_Tuple(node)
        #
        # elif isinstance(node, ast.Set):
        #     return self._on_ast_Set(node)
        #
        # elif isinstance(node, ast.UnaryOp):  # - and + etc.
        #     return self._on_ast_UnaryOp(node)
        #
        # elif isinstance(node, ast.BinOp):  # <left> <operator> <right>
        #     return self._on_ast_BinOp(node)
        #
        # elif isinstance(node, ast.BoolOp):  # and & or...
        #     return self._on_ast_BoolOp(node)
        #
        # elif isinstance(node, ast.Compare):  # 1 < 2, a == b...
        #     return self._on_ast_Compare(node)
        #
        # elif isinstance(node, ast.IfExp):  # x if y else z
        #     return self._on_ast_IfExp(node)
        #
        # elif isinstance(node, ast.Call):  # function...
        #     return self._on_ast_Call(node)
        #
        # elif isinstance(node, ast.Return):
        #     return self._on_ast_Return(node)
        #
        # elif isinstance(node, ast.Name):  # a, b, c...
        #     return self._on_ast_Name(node)
        #
        # elif isinstance(node, ast.Subscript):  # b[1]
        #     return self._on_ast_Subscript(node)
        #
        # elif isinstance(node, ast.Attribute):  # a.b.c
        #     return self._on_ast_Attribute(node)
        #
        # elif isinstance(node, ast.Index):
        #     return self._on_ast_Index(node)
        #
        # elif isinstance(node, ast.Expr):
        #     return self._on_ast_Expr(node)
        #
        # else:
        #     raise InvalidExpression("Sorry, %s is not available in this evaluator" % type(node).__name__)

        if isinstance(node, (list, tuple)):
            return self._on_many(node)
        else:
            op = '_on_ast_%s' % type(node).__name__
            if hasattr(self, op):
                return getattr(self, op)(node)
            else:
                raise InvalidExpression("Sorry, %s is not available in this evaluator" % type(node).__name__)

    def _on_many(self, node):
        ret = None
        for n in node:
            ret = self._eval(n)
        return ret

    def _on_ast_Assign(self, node):
        if not self.allow_assign:
            raise InvalidExpression("Sorry, %s is not available in this evaluator" % type(node).__name__)

        ret = self._eval(node.value)
        for t in node.targets:
            if isinstance(t, ast.Name):
                self._table[t.id] = ret
            elif isinstance(t, ast.Subscript):
                obj = self._eval(t.value)
                obj[self._eval(t.slice)] = ret
            elif isinstance(t, ast.Attribute):
                # TODO: check security
                obj = self._eval(t.value)
                if isinstance(obj, (dict, OrderedDict)):
                    obj[t.attr] = ret
                else:
                    raise ExpressionSyntaxError('Invalid assign')
                    # raise ExpressionSyntaxError('Invalid assign')
            else:
                raise ExpressionSyntaxError('Invalid assign')
        return ret

    def _on_ast_If(self, node):
        return self._eval(node.body) if self._eval(node.test) else self._eval(node.orelse)

    def _on_ast_For(self, node):
        ret = None
        for val in self._eval(node.iter):
            self._table[node.target.id] = val
            try:
                ret = self._eval(node.body)
            except _Break:
                break
        return ret

    def _on_ast_While(self, node):
        ret = None
        while self._eval(node.test):
            try:
                ret = self._eval(node.body)
            except _Break:
                break
        return ret

    def _on_ast_Break(self, node):
        raise _Break()

    def _on_ast_FunctionDef(self, node):
        # self.local_functions[node.name] = node
        self._table[node.name] = _UserDef(self, node)
        return None

    def _on_ast_Pass(self, node):
        return None

    def _on_ast_Try(self, node):
        ret = None
        try:
            ret = self._eval(node.body)
        except:
            if node.handlers:
                for n in node.handlers:
                    # ast.ExceptHandler
                    if n.body:
                        ret = self._eval(n.body)
        else:
            if node.orelse:
                ret = self._eval(node.orelse)
        finally:
            if node.finalbody:
                ret = self._eval(node.finalbody)

        return ret

    def _on_ast_Num(self, node):
        return node.n

    def _on_ast_Str(self, node):
        if len(node.s) > MAX_STR_LEN:
            raise ExpressionEvalError(
                "String Literal in statement is too long! (%s, when %s is max)" % (len(node.s), MAX_STR_LEN))
        return node.s

    def _on_ast_NameConstant(self, node):
        return node.value

    def _on_ast_Dict(self, node):
        d = {}
        for k, v in zip(node.keys, node.values):
            k = self._eval(k)
            v = self._eval(v)
            d[k] = v
            if len(d) > MAX_LEN:
                raise ExpressionEvalError('Max dict length.')
        return d

    def _on_ast_List(self, node):
        d = []
        for v in node.elts:
            v = self._eval(v)
            d.append(v)
            if len(d) > MAX_LEN:
                raise ExpressionEvalError('Max list/tuple/set length.')
        return d

    def _on_ast_Tuple(self, node):
        return tuple(self._on_ast_List(node))

    def _on_ast_Set(self, node):
        return set(self._on_ast_List(node))

    def _on_ast_UnaryOp(self, node):
        return OPERATORS[type(node.op)](self._eval(node.operand))

    def _on_ast_BinOp(self, node):
        return OPERATORS[type(node.op)](self._eval(node.left), self._eval(node.right))

    def _on_ast_BoolOp(self, node):
        if isinstance(node.op, ast.And):
            # return all((self._eval(v) for v in node.values))
            res = False
            for v in node.values:
                res = self._eval(v)
                if not res:
                    return False
            return res
        elif isinstance(node.op, ast.Or):
            # return any((self._eval(v) for v in node.values))
            res = True
            for v in node.values:
                res = self._eval(v)
                if res:
                    return res
            return res

    def _on_ast_Compare(self, node):
        return OPERATORS[type(node.ops[0])](self._eval(node.left), self._eval(node.comparators[0]))

    def _on_ast_IfExp(self, node):
        return self._eval(node.body) if self._eval(node.test) else self._eval(node.orelse)

    def _on_ast_Call(self, node):
        f = self._eval(node.func)
        if not callable(f):
            raise FunctionNotDefined(node.func.id)

        f_args = [self._eval(a) for a in node.args]
        f_kwargs = {k.arg: self._eval(k.value) for k in node.keywords}
        return f(*f_args, **f_kwargs)

    def _on_ast_Return(self, node):
        val = self._eval(node.value)
        raise _Return(val)

    def _on_ast_Name(self, node):
        ret = self.find_name(node.id)
        return ret

    def _on_ast_Subscript(self, node):
        val = self._eval(node.value)
        index_or_key = self._eval(node.slice)
        try:
            return val[index_or_key]
        except KeyError:
            return None

    def _on_ast_Attribute(self, node, val=empty):
        if val is empty:
            val = self._eval(node.value)
        if val is None:
            return None
        if isinstance(val, (dict, OrderedDict)):
            try:
                return val[node.attr]
            except (KeyError, TypeError):
                raise AttributeDoesNotExist(node.attr)
        else:
            if isinstance(val, datetime.date):
                if node.attr in ['year', 'month', 'day']:
                    return getattr(val, node.attr)

            elif isinstance(val, datetime.timedelta):
                if node.attr in ['days']:
                    return getattr(val, node.attr)

            elif isinstance(val, relativedelta.relativedelta):
                if node.attr in ['years', 'months', 'days', 'leapdays', 'year', 'month', 'day', 'weekday']:
                    return getattr(val, node.attr)

        raise AttributeDoesNotExist(node.attr)

    def _on_ast_Index(self, node):
        return self._eval(node.value)

    def _on_ast_Expr(self, node):
        return self._eval(node.value)


# class ModelSimpleEval(SimpleEval2):
#     def __init__(self, *args, **kwargs):
#         self.member = kwargs.pop('member')
#         super(ModelSimpleEval, self).__init__(*args, **kwargs)
#
#     def _on_ast_Subscript(self, node):
#         val = self._eval(node.value)
#
#         # from django.db import models
#         # if isinstance(val, (models.Manager, models.QuerySet)):
#         #     if isinstance(val, models.Manager):
#         #         val = val.all()
#         #     pass
#         val = self._filter_value(val, wrap=False)
#
#         try:
#             return val[self._eval(node.slice)]
#         except KeyError:
#             return None
#
#     def _on_ast_Attribute(self, node, val=empty):
#         from django.db import models
#         from poms.obj_perms.utils import has_view_perms
#
#         val = self._eval(node.value)
#         if isinstance(val, (models.Manager, models.QuerySet)):
#             if isinstance(val, models.Manager):
#                 val = val.all()
#             val = self._filter_value(val, wrap=True)
#             return val
#
#         elif isinstance(val, models.Model):
#             rejected = False
#             if self._has_object_permission(val):
#                 if has_view_perms(self.member, val):
#                     pass
#                 else:
#                     if node.attr in ['id', 'public_name', 'display_name']:
#                         pass
#                     else:
#                         rejected = True
#
#             self._check_field(val, node.attr)
#
#             if node.attr == 'display_name':
#                 if rejected:
#                     res = getattr(val, 'public_name', None)
#                 else:
#                     res = getattr(val, 'name', None)
#             else:
#                 res = getattr(val, node.attr)
#                 if rejected:
#                     return None
#
#                 res = self._filter_value(res, wrap=True)
#                 if node.attr == 'attributes':
#                     if rejected:
#                         res = None
#                     else:
#                         res = {a.attribute_type.name: a for a in res if has_view_perms(self.member, a.attribute_type)}
#
#             if callable(res):
#                 raise AttributeDoesNotExist(node.attr)
#
#             return None if rejected else res
#
#         return super(ModelSimpleEval, self)._on_ast_Attribute(node, val=val)
#
#     def _filter_value(self, val, wrap=False):
#         from django.db import models
#
#         if isinstance(val, (models.Manager, models.QuerySet)):
#             if isinstance(val, models.Manager):
#                 val = val.all()
#             if self._has_object_permission(val.model):
#                 # use prefetched permissions!
#                 from poms.obj_perms.utils import has_view_perms
#                 return [
#                     o for o in val if has_view_perms(self.member, o)
#                     ]
#             if wrap:
#                 return list(val)
#
#         return val
#
#     def _has_object_permission(self, model_or_instance):
#         from django.db import models
#
#         if isinstance(model_or_instance, models.Model):
#             model = model_or_instance.__class__
#         else:
#             model = model_or_instance
#         try:
#             model._meta.get_field('object_permissions')
#             return True
#         except models.FieldDoesNotExist:
#             return False
#
#     def _check_field(self, obj, name):
#         from django.db import models
#         from poms.obj_attrs.models import GenericAttribute
#
#         try:
#             field = obj._meta.get_field(name)
#             if field.many_to_many or field.one_to_many or field.one_to_one:
#                 if field.name != 'attributes':
#                     raise AttributeDoesNotExist(name)
#         except models.FieldDoesNotExist:
#             if isinstance(obj, GenericAttribute):
#                 if name == 'value':
#                     return
#             if name == 'display_name':
#                 return
#             raise


def validate(expr):
    from rest_framework.exceptions import ValidationError
    try:
        SimpleEval2.try_parse(expr)
        # try_parse(expr)
    except InvalidExpression as e:
        raise ValidationError('Invalid expression: %s' % e)


def safe_eval(s, names=None, max_time=None, add_print=False, allow_assign=False, now=None):
    return SimpleEval2(names=names, max_time=max_time, add_print=add_print, allow_assign=allow_assign, now=now).eval(s)


def value_prepare(orig):
    def _dict(data):
        ret = OrderedDict()
        for k, v in data.items():
            if k in ['user_object_permissions', 'group_object_permissions', 'object_permissions',
                     'granted_permissions']:
                continue
            if k.endswith('_object'):
                k = k[:-7]
                ret[k] = _value(v)
            else:
                if k not in ret:
                    ret[k] = _value(v)
        return ret

    def _list(data):
        ret = []
        for v in data:
            ret.append(_value(v))
        return ret

    def _tuple(data):
        return tuple(_list(data))

    def _value(data):
        if data is None:
            return None
        elif isinstance(data, Promise):
            return str(data)
        elif isinstance(data, (dict, OrderedDict)):
            return _dict(data)
        elif isinstance(data, list):
            return _list(data)
        elif isinstance(data, tuple):
            return _tuple(data)
        return data

    return _value(orig)


def get_model_data(val, serializer_class, many=False, context=None, hide_fields=None):
    serializer = serializer_class(instance=val, many=many, context=context)
    if hide_fields:
        for f in hide_fields:
            serializer.fields.pop(f)
    data = serializer.data
    data = value_prepare(data)
    # import json
    # print(json.dumps(data, indent=2))
    return data


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


DATE format string (also used in parse):
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
    # _l.info(safe_eval('[1, 1.0, "str", None, True, False]'))


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
    # _l.info(safe_eval('y = now().year'))
    # _l.info(safe_eval('eval("2+eval(\\\"2+2\\\")")'))
    # _l.info(ast.literal_eval('2+2'))
    # _l.info(safe_eval("globals()['now']()"))


    def test_eval(expr, names=None):
        _l.info('-' * 79)
        try:
            se = SimpleEval2(names=names, add_print=True)
            ret = se.eval(expr)
            # res = safe_eval(expr, names=names)
        except InvalidExpression as e:
            import time
            ret = "<ERROR1: %s>" % e
            time.sleep(1)
            # raise e
        except Exception as e:
            ret = "<ERROR2: %s>" % e
        _l.info("\t%-60s -> %s" % (expr, ret))


    #     test_eval('''
    # pass
    #
    # a = 1000
    # # not supported
    # # if 1 <= a <= 2000:
    # #     pass
    # if 1 <= a and a <= 2000:
    #     pass
    #
    # for i in [1,2]:
    #     pass
    #
    # i = 0
    # while i < 2:
    #     pass
    #     i = i + 1
    #
    # a = 0
    # try:
    #     a = a + 1
    # except:
    #     a = a + 10
    # else:
    #     a = a + 100
    # finally:
    #     a = a + 1000
    #
    # b = 1
    # if b == 0:
    #     pass
    # elif b == 1:
    #     pass
    # else:
    #     pass
    #
    # def f1(v):
    #     pass
    #     for i in [1,2]:
    #         if v > 1:
    #             pass
    #             return True
    #         else:
    #             return False
    # f1(1)
    #
    # b = 0
    # for a in range(1,10):
    #     b = b + a
    # b
    #
    # b2 = 0
    # for a in range(10):
    #     b2 = b2 + a
    # b2
    #
    # range(10)
    # date(2016)
    # ''')


    def demo():
        # from poms.common.formula_serializers import EvalInstrumentSerializer, EvalTransactionSerializer


        from rest_framework.test import APIRequestFactory
        factory = APIRequestFactory()
        instrument_request = factory.get('/api/v1/instruments/instrument/1/', format='json')
        transactions_request = factory.get('/api/v1/transactions/transaction/', format='json')
        names = {
            "v0": 1.00001,
            "v1": "str",
            "v2": {"id": 1, "name": "V2", "trn_code": 12354, "num": 1.234},
            "v3": [{"id": 2, "name": "V31"}, {"id": 3, "name": "V32"}, ],
            "v4": OrderedDict([["id", 3], ["name", "Lol"]]),
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
        test_eval("2 * 2 + 2", names)
        test_eval("2 * (2 + 2)", names)
        test_eval("16 ** 16", names)
        test_eval("5 / 2", names)
        test_eval("5 % 2", names)

        _l.info('')
        _l.info("with variables:")
        test_eval("v0 + 1", names)
        test_eval("v1 + ' & ' + str(v0)", names)
        test_eval("v2.name", names)
        test_eval("v2.num * 3", names)
        test_eval("v3[1].name", names)
        test_eval("v3[1].name", names)
        test_eval("globals()", names)
        test_eval("globals()['v0']", names)
        # test_eval("instr.name", names)
        # test_eval("instr.instrument_type.id", names)
        # test_eval("instr.instrument_type.user_code", names)
        # test_eval("instr.price_multiplier", names)
        # test_eval("instr['price_multiplier']", names)
        # test_eval("globals()['instr']", names)
        # test_eval("globals()['instr'].price_multiplier", names)
        # test_eval("globals()['instr']['price_multiplier']", names)

        _l.info('')
        _l.info("functions: ")
        test_eval("round(1.5)", names)
        test_eval("trunc(1.5)", names)
        test_eval("int(1.5)", names)
        test_eval("now()", names)
        test_eval("add_days(now(), 10)", names)
        test_eval("add_workdays(now(), 10)", names)
        test_eval("iff(1.001 > 1.002, 'really?', 'ok')", names)
        test_eval("'really?' if 1.001 > 1.002 else 'ok'", names)
        test_eval("'N' + format_date(now(), '%Y%m%d') + '/' + str(v2.trn_code)", names)

        test_eval("format_date(now())", names)
        test_eval("format_date(now(), '%Y/%m/%d')", names)
        test_eval("format_date(now(), format='%Y/%m/%d')", names)
        test_eval("format_number(1234.234)", names)
        test_eval("format_number(1234.234, '.', 2)", names)

        # r = safe_eval3('"%r" % now()', names=names, functions=functions)
        # r = safe_eval('format_date(now(), "EEE, MMM d, yy")')
        # _l.info(repr(r))
        # _l.info(add_workdays(datetime.date(2016, 6, 15), 3, only_workdays=False))
        # _l.info(add_workdays(datetime.date(2016, 6, 15), 4, only_workdays=False))
        # _l.info(add_workdays(datetime.date(2016, 6, 15), 3))
        # _l.info(add_workdays(datetime.date(2016, 6, 15), 4))


    # demo()
    pass


    def demo_stmt():
        test_eval('a = 2 + 3')

        test_eval('''
a = {}
a['2'] = {}
a['2']['1'] = {}
a['2']['1'][1]=123
a
''')

        test_eval('''
a = 2
b = None
if b is None:
    b = 2
if b is not None:
    b = 3
if not b:
    b = 1
a * b
        ''')

        test_eval('''
r = 0
for a in [1,2,3]:
    r = r + a
r
        ''')

        test_eval('''
r = 0
while r < 100:
    r = r + 2
r
        ''')

        test_eval('''
a = date(2000, 1, 1)
b = date(2001, 1, 1)
r = a
k = 0
while r < b:
    r = r + weeks(k * 2)
    k = k + 1
k, r
        ''')

        test_eval('''
a = date(2000, 1, 1)
b = date(2001, 1, 1)
r = a
k = 0
while r < b:
    r = r + timedelta(weeks=k * 2)
    k = k + 1
k, r
        ''')

        test_eval('''
def f1(a, b = 200, c = 300):
    r = a * b
    return r + c
f1(10, b = 20)
        ''')

        test_eval('''
def accrl_C_30E_P_360(dt1, dt2):
    d1 = dt1.day
    d2 = dt2.day
    m1 = dt1.month
    m2 = dt1.month
    if d1 == 31:
        d1 = 30
    if d2 == 31:
        m2 += 1
        d2 = 1
    return ((dt2.year - dt1.year) * 360 + (m2 - m1) * 30 + (d2 - d1)) / 360
accrl_C_30E_P_360(parse_date('2001-01-01'), parse_date('2001-01-25'))
        ''')

        test_eval('''
def accrl_NL_365_NO_EOM(dt1, dt2):
    is_leap1 = isleap(dt1.year)
    is_leap2 = isleap(dt2.year)
    k = 0
    if is_leap1 and dt1 < date(dt1.year, 2, 29) and dt2 >= date(dt1.year, 2, 29):
        k = 1
    if is_leap2 and dt2 >= date(dt2.year, 2, 29) and dt1 < date(dt2.year, 2, 29):
        k = 1
    return (dt2 - dt1 - days(k)).days / 365
accrl_NL_365_NO_EOM(parse_date('2000-01-01'), parse_date('2000-01-25'))
        ''')

        test_eval('''
a = 1

def f1():
    print('f1: 1 - a=%s', a)

def f2():
    print('f2: 1 - a=%s', a)
    a = 2
    print('f2: 2 - a=%s', a)

def f3():
    print('f3: 1 - a=%s', a)
    a = 3
    print('f3: 2 - a=%s', a)

f1()
f2()
f3()
print('gg: 1 - a=%s', a)
        ''')


    # demo_stmt()
    pass


    def perf_tests():
        import timeit

        def f_native():
            def accrual_NL_365_NO_EOM(dt1, dt2):
                k = 0
                if _isleap(dt1.year) and dt1 < _date(dt1.year, 2, 29) <= dt2:
                    k = 1
                if _isleap(dt2.year) and dt2 >= _date(dt2.year, 2, 29) > dt1:
                    k = 1
                return ((dt2 - dt1).days - k) / 365

            # for i in range(50):
            #     accrual_NL_365_NO_EOM(_date(2000, 1, 1), _date(2000, 1, 25))
            # for i in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
            #     # accrual_NL_365_NO_EOM(_parse_date('2000-01-01'), _parse_date('2000-01-25'))
            #     accrual_NL_365_NO_EOM(_date(2000, 1, 1), _date(2000, i, 25))
            # accrual_NL_365_NO_EOM(_parse_date('2000-01-01'), _parse_date('2000-01-25'))
            accrual_NL_365_NO_EOM(_date(2000, 1, 1), _date(2000, 1, 25))

        expr = '''
def accrual_NL_365_NO_EOM(dt1, dt2):
    k = 0
    if isleap(dt1.year) and dt1 < date(dt1.year, 2, 29) <= dt2:
        k = 1
    if isleap(dt2.year) and dt2 >= date(dt2.year, 2, 29) > dt1:
        k = 1
    return ((dt2 - dt1).days - k) / 365
# for i in range(50):
#     accrual_NL_365_NO_EOM(date(2000, 1, 1), date(2000, 1, 25))
# for i in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
#     # accrual_NL_365_NO_EOM(parse_date('2000-01-01'), parse_date('2000-01-25'))
#     accrual_NL_365_NO_EOM(date(2000, 1, 1), date(2000, i, 25))
# accrual_NL_365_NO_EOM(parse_date('2000-01-01'), parse_date('2000-01-25'))
accrual_NL_365_NO_EOM(date(2000, 1, 1), date(2000, 1, 25))
        '''

        _l.info('PERF')
        number = 1000
        _l.info('-' * 79)
        _l.info(expr)
        _l.info('-' * 79)
        _l.info('native          : %f', timeit.timeit(f_native, number=number))
        _l.info('parse           : %f', timeit.timeit(lambda: ast.parse(expr), number=number))
        _l.info('exec            : %f', timeit.timeit(lambda: exec(expr, {
            'parse_date': _parse_date,
            'isleap': calendar.isleap,
            'date': _date,
            'days': _days,
        }), number=number))
        _l.info('safe_eval       : %f', timeit.timeit(lambda: safe_eval(expr, allow_assign=True), number=number))

        _l.info('-' * 79)
        expr = '-(4-1)*5+(2+4.67)+5.89/(.2+7)'
        _l.info('eval            : %f', timeit.timeit(lambda: exec(expr), number=number))
        _l.info('safe_eval       : %f', timeit.timeit(lambda: safe_eval(expr), number=number))


    # perf_tests()
    pass


    def model_access_test():
        from poms.users.models import Member
        from poms.transactions.models import Transaction

        member = Member.objects.get(pk=1)  # a
        # member = Member.objects.get(pk=4)  # b

        # ts_qs = Transaction.objects
        from poms.obj_attrs.utils import get_attributes_prefetch
        from poms.obj_perms.utils import get_permissions_prefetch_lookups
        from poms.accounts.models import Account, AccountType
        from poms.instruments.models import Instrument

        ts_qs = Transaction.objects.select_related(
            'account_cash', 'account_cash__type',
            'account_position', 'account_position__type',
            'account_interim', 'account_interim__type',
        ).prefetch_related(
            get_attributes_prefetch(),
            *get_permissions_prefetch_lookups(
                ('account_cash', Account),
                ('account_cash__type', AccountType),
                ('account_position', Account),
                ('account_position__type', AccountType),
                ('account_interim', Account),
                ('account_interim__type', AccountType),
            )
        )

        names = {
            # 'transactions': ts_qs,
            'transactions': list(ts_qs),
            'transaction': ts_qs.first(),
            'account': Account.objects.get(pk=1),
            'instrument': Instrument.objects.get(pk=1),
        }

        _l.info('---------')

        # seval = ModelSimpleEval(names=names, add_print=True, allow_assign=False, member=member)
        # _l.info(seval.eval('transactions1'))
        # _l.info(seval.eval('transactions1[0]'))
        # _l.info(seval.eval('transactions2'))
        # _l.info(seval.eval('transactions2[0]'))
        # _l.info(seval.eval('transaction.transaction_class'))
        # _l.info(seval.eval('transactions[0].attributes'))
        # _l.info(seval.eval('transactions[0].attributes["SomeNumber"]'))
        # _l.info(seval.eval('transactions[0].attributes.SomeNumber'))
        # _l.info(seval.eval('transactions[0].attributes["SomeNumber"].value'))
        # _l.info(seval.eval('transaction.account_position.user_code or transaction.account_position.public_name'))
        # _l.info(seval.eval('find_name(transaction.account_position.user_code, transaction.account_position.public_name)'))
        # _l.info(seval.eval('find_name(transaction.account_cash.user_code, transaction.account_cash.public_name)'))
        # _l.info(seval.eval('find_name(transaction.account_interim.user_code, transaction.account_interim.public_name)'))
        # _l.info(seval.eval('account.tags'))
        # _l.info(seval.eval('account.object_permissions'))
        # _l.info(seval.eval('account.attributes'))
        # _l.info(seval.eval('account.attributes["SomeString"].value'))
        # _l.info(seval.eval('instrument.attributes'))
        # _l.info(seval.eval('instrument.prices'))
        # _l.info(seval.eval('instrument.maturity_date'))
        # _l.info(seval.eval('instrument.maturity_date.year'))
        # _l.info(seval.eval('a = 3'))
        # _l.info(seval.eval('None or "a"'))
        # _l.info(seval.eval('"b" or "a"'))
        pass


    # model_access_test()
    pass


    def now_test():
        now = datetime.date(2000, 1, 1)
        _l.info(safe_eval('now()'))
        _l.info(safe_eval('now()', now=lambda: now))
    # now_test()
    pass

    def globals_test():
        _l.info(safe_eval('globals()["a"]', names={'a': 123}))

    globals_test()
    pass
