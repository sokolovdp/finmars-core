from __future__ import unicode_literals, print_function, division

import ast
import collections
import datetime
import random
from collections import Callable

import simpleeval
import six
from babel import numbers
from dateutil import parser


class InvalidExpression(Exception):
    def __init__(self, e):
        super(InvalidExpression, self).__init__(e)
        self.message = getattr(e, "message", str(e))


def now_date():
    from django.utils import timezone
    return timezone.now().date()


def add_workdays(d, x, only_workdays=True):
    weeks = int(x / 5)
    days_remainder = x % 5
    d = d + datetime.timedelta(weeks=weeks, days=days_remainder)
    if only_workdays:
        if d.weekday() == 5:
            return d + datetime.timedelta(days=2)
        if d.weekday() == 6:
            return d + datetime.timedelta(days=1)
    return d


def format_date(x, fmt=None, locale=None):
    if fmt:
        from django.utils import translation
        if locale is None:
            locale = translation.get_language()
        # return dates.format_date(x, fmt, locale=locale)
        return x.strftime(fmt)
    else:
        return six.text_type(x)


def parse_date(x, fmt=None, locale=None):
    if fmt is None:
        return parser.parse(x).date()
    from django.utils import translation
    if locale is None:
        locale = translation.get_language()
    return datetime.datetime.strptime(x, fmt).date()


def format_decimal(x, fmt=None, locale=None):
    if fmt:
        from django.utils import translation
        if locale is None:
            locale = translation.get_language()
        return numbers.format_decimal(x, fmt, locale=locale)
    else:
        return six.text_type(x)


def format_currency(x, ccy, locale=None):
    from django.utils import translation
    if locale is None:
        locale = translation.get_language()
    return numbers.format_currency(x, ccy, locale=locale)


def w_random():
    return random.random()


DEFAULT_FUNCTIONS = {
    "str": lambda x: six.text_type(x),
    "int": lambda x: int(x),
    "float": lambda x: float(x),
    "round": lambda x: round(x),
    "trunc": lambda x: int(x),
    "iff": lambda x, v1, v2: v1 if x else v2,
    "now": now_date,
    "days": lambda x: datetime.timedelta(days=x),
    "add_days": lambda d, x: d + datetime.timedelta(days=x),
    "add_weeks": lambda d, x: d + datetime.timedelta(weeks=x),
    "add_workdays": add_workdays,
    "format_date": format_date,
    "parse_date": parse_date,
    "format_decimal": format_decimal,
    "format_currency": format_currency,
    "random": w_random,
}


class SimpleEval2(object):  # pylint: disable=too-few-public-methods
    expr = ""

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
        self.names = names

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
            if isinstance(node.op, (ast.Mult, ast.Mod,)) and isinstance(l, (six.text_type, six.binary_type)):
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
                return self.functions[node.func.id](*(self._eval(a) for a in node.args))
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
                elif isinstance(self.names, dict):
                    return self.names[node.id]
                elif isinstance(self.names, Callable):
                    return self.names(node)
                else:
                    raise InvalidExpression('Trying to use name (variable) "{0}"'
                                            ' when no "names" defined for'
                                            ' evaluator'.format(node.id))

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


if __name__ == "__main__":
    import os

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "poms_app.settings")
    import django

    django.setup()

    from django.utils import timezone, translation


    # names = {
    #     "v0": 1.00001,
    #     "v1": "str",
    #     "v2": {
    #         "id": 1,
    #         "name": "V2",
    #         "code": 12354
    #     },
    #     "v3": [
    #         {
    #             "id": 2,
    #             "name": "V31"
    #         },
    #         {
    #             "id": 3,
    #             "name": "V32"
    #         },
    #     ],
    # }

    # print(safe_eval('(1).__class__.__bases__', names=names))
    # print(safe_eval2('(1).__class__.__bases__', names=names))
    # print(safe_eval3('(1).__class__.__bases__[0].__subclasses__()', names=names))
    # print(safe_eval('5 % 2'))

    def demo():
        import pprint
        from poms.instruments.models import Instrument
        from poms.transactions.models import Transaction
        from poms.common.formula_serializers import EvalInstrumentSerializer, EvalTransactionSerializer

        def play(expr, names=None):
            try:
                res = safe_eval(expr, names=names)
            except InvalidExpression as e:
                res = "<ERROR1: %s>" % e.message
            except Exception as e:
                res = "<ERROR2: %s>" % e
            print('\t%-60s -> %s' % (expr, res))

        names = {
            "v0": 1.00001,
            "v1": "str",
            "v2": {"id": 1, "name": "V2", "trn_code": 12354, "num": 1.234},
            "v3": [{"id": 2, "name": "V31"}, {"id": 3, "name": "V32"}, ],
            "instr": collections.OrderedDict(EvalInstrumentSerializer(instance=Instrument.objects.first()).data),
            "trns": [collections.OrderedDict(EvalTransactionSerializer(instance=t).data)
                     for t in Transaction.objects.all()[:2]],
        }
        print('test variables:')
        for n in sorted(six.iterkeys(names)):
            print(n, '\n')
            pprint.pprint(names[n])
            # print('\t%s -> %s' % (n, json.dumps(names[n], sort_keys=True, indent=2)))

        print()
        print('simple:')
        play('2 * 2 + 2', names)
        play('2 * (2 + 2)', names)
        play('16 ** 16', names)
        play('5 / 2', names)
        play('5 % 2', names)

        print()
        print('with variables:')
        play('v0 + 1', names)
        play('v1 + " & " + str(v0)', names)
        play('v2.name', names)
        play('v2.num * 3', names)
        play('v3[1].name', names)
        play('v3[1].name', names)
        play('instr.name', names)
        play('instr.instrument_type.id', names)
        play('instr.instrument_type.user_code', names)

        print()
        print('functions: ')
        play('round(1.5)', names)
        play('trunc(1.5)', names)
        play('int(1.5)', names)
        play('now()', names)
        play('add_days(now(), 10)', names)
        play('add_workdays(now(), 10)', names)
        play('iff(1.001 > 1.002, "really?", "ok")', names)
        play('"really?" if 1.001 > 1.002 else "ok"', names)
        play('"N" + format_date(now(), "YMMdd") + "/" + str(v2.trn_code)', names)

        for lang in ['ru', 'en', 'de', 'fr']:
            print()
            print('localized (from master user settings): language=%s' % lang)
            translation.activate(lang)
            play('format_date(now(), "full")', names)
            play('format_date(now(), "long")', names)
            play('format_date(now(), "short")', names)
            play('format_decimal(1234.234, "#,##0.##;-#")', names)
            play('format_currency(1234.234, "USD")', names)
            play('format_currency(1234.234, "RUB")', names)

            # r = safe_eval3('"%r" % now()', names=names, functions=functions)
            # r = safe_eval('format_date(now(), "EEE, MMM d, yy")')
            # print(repr(r))
            # print(add_workdays(datetime.date(2016, 6, 15), 3, only_workdays=False))
            # print(add_workdays(datetime.date(2016, 6, 15), 4, only_workdays=False))
            # print(add_workdays(datetime.date(2016, 6, 15), 3))
            # print(add_workdays(datetime.date(2016, 6, 15), 4))


    demo()
