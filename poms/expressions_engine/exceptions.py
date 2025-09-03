class InvalidExpression(Exception):
    pass


class ExpressionSyntaxError(InvalidExpression):
    pass


class ExpressionEvalError(InvalidExpression):
    pass


class FunctionNotDefined(InvalidExpression):
    def __init__(self, name):
        self.message = f"Function '{name}' not defined"
        super(InvalidExpression, self).__init__(self.message)


class NameNotDefined(InvalidExpression):
    def __init__(self, name):
        self.message = f"Name '{name}' not defined"
        super(InvalidExpression, self).__init__(self.message)


class AttributeDoesNotExist(InvalidExpression):
    def __init__(self, attr):
        self.message = f"Attribute '{attr}' does not exist in expression"
        super().__init__(self.message)


class _Break(InvalidExpression):
    pass


class _Return(InvalidExpression):
    def __init__(self, value):
        self.value = value
        super().__init__()
