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
    try:
        return ast.parse(expr), None
    except (SyntaxError, ValueError) as e:
        return None, e


DEFAULT_FUNCTIONS = {
    # 'now': lambda: timezone.now()
    'now': lambda: datetime.datetime.utcnow(),
    'now2': lambda: '%s' % datetime.datetime.utcnow(),
}


def safe_eval(expr, functions=DEFAULT_FUNCTIONS, names=None):
    import simpleeval
    try:
        v = simpleeval.simple_eval(expr, functions=functions, names=names)
    except simpleeval.InvalidExpression as e:
        raise InvalidExpression(e)
    pprint.pprint(v)
    return v


# safe_eval('now2()')
safe_eval('{"a": 1}')
