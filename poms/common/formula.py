from __future__ import unicode_literals, print_function

import datetime
import pprint


class InvalidExpression(Exception):
    pass


def is_valid(expr):
    import ast
    try:
        ast.parse(expr)
    except (SyntaxError, ValueError):
        return False
    return True


def parse(expr):
    import ast
    try:
        return ast.parse(expr), None
    except (SyntaxError, ValueError) as e:
        return None, e


DEFAULT_FUNCTIONS = {
    # 'now': lambda: timezone.now()
    'now': lambda: datetime.datetime.utcnow(),
    # 'now2': lambda: '%s' % datetime.datetime.utcnow(),
}


def funcs(f, with_default=True):
    if with_default:
        res = f.copy()
        res.update(DEFAULT_FUNCTIONS)
        return res
    return f


def safe_eval(expr, functions=DEFAULT_FUNCTIONS, names=None):
    import simpleeval
    try:
        v = simpleeval.simple_eval(expr, functions=functions, names=names)
        # v = simpleeval.simple_eval(expr,names=names)
    except (simpleeval.InvalidExpression, KeyError, AttributeError) as e:
        raise InvalidExpression(e)
    pprint.pprint(v)
    return v


if __name__ == "__main__":
    # safe_eval('now()')
    safe_eval('"a".__class__.__class__()')
    safe_eval('"-" * 2 ** 2 ** 2 ** 2 ** 2')
    # safe_eval('2 >> 2')
