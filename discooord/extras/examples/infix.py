import math
import random
import re

from collections import namedtuple

from .vector import Vector


REGEX_SPLIT = re.compile(r'([(,)^*/%+\-=])')  # TODO: Build from operators list

REGEX_PART_LITERAL = r'\d+(?:\.\d+)?'
REGEX_PART_VARIABLE = r'[A-Z](?:[\w\d]+)?|_'
REGEX_PART_FUNCTION = r'[a-z](?:[\w\d]+)?'

REGEX_LITERAL = re.compile(r'^{}|{}$'.format(REGEX_PART_LITERAL, REGEX_PART_VARIABLE))
REGEX_VARIABLE = re.compile(r'^{}$'.format(REGEX_PART_VARIABLE))
REGEX_FUNCTION = re.compile(r'^{}$'.format(REGEX_PART_FUNCTION))

ASSOCIATIVITY_LEFT = 1
ASSOCIATIVITY_RIGHT = 2


Literal = namedtuple('Literal', ['value'])


class Operation(object):
    token = None
    func = None
    arg_count = None

    on_shunt = None

    hidden = False

    def __init__(self, token=None, func=None, arg_count=None, on_shunt=None, hidden=None):
        if token is not None:
            self.token = token

        if func is not None:
            self.func = func

        if arg_count is not None:
            self.arg_count = arg_count

        if on_shunt is not None:
            self.on_shunt = on_shunt

        if hidden is not None:
            self.hidden = hidden

        self.validate()

    def _validate(self, key):
        if getattr(self, key) is None:
            raise ValueError('{} attribute invalid for operation {}.'.format(key, self.__class__.__name__))

    def validate(self):
        self._validate('token')
        self._validate('func')
        self._validate('arg_count')


class Operator(Operation):
    arg_count = 2

    precedence = None
    associativity = None

    def __init__(self, token=None, func=None, arg_count=None, precedence=None, associativity=None, on_shunt=None, hidden=None):
        if precedence is not None:
            self.precedence = precedence

        if associativity is not None:
            self.associativity = associativity

        super(Operator, self).__init__(token, func, arg_count, on_shunt, hidden)

    def validate(self):
        super(Operator, self).validate()
        self._validate('precedence')
        self._validate('associativity')


class Function(Operation):
    arg_count = 1


class Parser(object):
    operations = None
    operators = None
    functions = None

    variables = None

    def __init__(self):
        self.operations = {}
        self.operators = {}
        self.functions = {}

        self.variables = {}

    def assign(self, key, value):
        self.variables[key] = value
        return value

    def on_shunt_subtract_negate(self, stack, output, last):
        if last is None or last in self.operators or last in '(,':
            return '-n'

    def register(self, operation):
        self.operations[operation.token] = operation

        if isinstance(operation, Operator):
            self.operators[operation.token] = operation
        elif isinstance(operation, Function):
            self.functions[operation.token] = operation

    def extract_tokens(self, equation):
        equation = equation.replace(' ', '')
        return [t for t in REGEX_SPLIT.split(equation) if t]

    def shunt_tokens(self, tokens):
        stack = []
        output = []
        last = None

        if '=' in tokens:
            assignment = tokens.index('=')
            if assignment <= 1:
                if assignment == 0:
                    assignment = '_'
                elif not REGEX_VARIABLE.match(tokens[0]):
                    raise ArithmeticError('Assignment invalid')
                else:
                    assignment = tokens.pop(0)

                output.append(Literal(assignment))
                stack.append(tokens.pop(0))
            else:
                raise ArithmeticError('Assignment invalid')

        for i, t in enumerate(tokens):
            if REGEX_LITERAL.match(t):
                try:
                    output.append(Literal(float(t)))
                except ValueError:
                    v = self.variables.get(t)
                    if v is not None:
                        output.append(v)
                    else:
                        raise ArithmeticError('Unknown variable `{}`'.format(t))
            elif t == '(' or REGEX_FUNCTION.match(t):
                stack.append(t)
            elif t == ',':
                while stack[-1] != '(' and stack[-1] in self.operators:
                    output.append(stack.pop())
                if stack[-1] != '(':
                    raise ArithmeticError('Parenthesis mismatch')
            elif t in self.operators:
                o1 = self.operators[t]

                # TODO: Recursive and all operations
                if o1.on_shunt:
                    on_shunt = o1.on_shunt(stack, output, last)
                    if on_shunt:
                        o1 = self.operators[on_shunt]

                while stack and stack[-1] in self.operators:
                    o2 = self.operators[stack[-1]]
                    if (o1.associativity == ASSOCIATIVITY_LEFT and o1.precedence <= o2.precedence) or (o1.associativity == ASSOCIATIVITY_RIGHT and o1.precedence < o2.precedence):
                        output.append(stack.pop())
                    else:
                        break

                stack.append(o1.token)
            elif t == ')':
                while stack[-1] != '(' and stack[-1] in self.operators:
                    output.append(stack.pop())

                if stack[-1] != '(':
                    raise ArithmeticError('Parenthesis mismatch')
                stack.pop()  # Drop (

                if stack and REGEX_FUNCTION.match(stack[-1]):
                    output.append(stack.pop())

            last = t

        if len(stack) > 0:
            if stack[-1] in '()':
                raise ArithmeticError('Parenthesis mismatch')
            stack.reverse()
            output += stack

        return output

    def parse_rpn(self, rpn):
        stack = []

        for t in rpn:
            #if isinstance(t, (int, long, float, Vector)) or REGEX_VARIABLE.match(t):
            if isinstance(t, Literal) or REGEX_VARIABLE.match(t):
                stack.append(t)
            else:
                operation = self.operations.get(t)
                if operation is None:
                    raise ArithmeticError('Unknown operation `{}`'.format(t))

                if len(stack) < operation.arg_count:
                    raise ArithmeticError('Not enough arguments passed to {}'.format(t))

                args = [stack.pop().value for x in xrange(0, operation.arg_count)]
                args.reverse()

                stack.append(Literal(operation.func(*args)))

        if len(stack) == 1:
            return stack[0].value
        else:
            raise ArithmeticError('Failed to parse expression.')

    def parse(self, equation):
        tokens = self.extract_tokens(equation)
        rpn = self.shunt_tokens(tokens)
        return self.parse_rpn(rpn)


def build_parser():
    parser = Parser()

    parser.register(Operator(token='-n', precedence=4, associativity=ASSOCIATIVITY_RIGHT, func=lambda a: -a, arg_count=1, hidden=True))
    parser.register(Operator(token='^', precedence=3, associativity=ASSOCIATIVITY_RIGHT, func=lambda a, b: math.pow(a, b), arg_count=2))
    parser.register(Operator(token='*', precedence=2, associativity=ASSOCIATIVITY_LEFT, func=lambda a, b: a * b, arg_count=2))
    parser.register(Operator(token='/', precedence=2, associativity=ASSOCIATIVITY_LEFT, func=lambda a, b: a / b, arg_count=2))
    parser.register(Operator(token='%', precedence=2, associativity=ASSOCIATIVITY_LEFT, func=lambda a, b: a % b, arg_count=2))
    parser.register(Operator(token='+', precedence=1, associativity=ASSOCIATIVITY_LEFT, func=lambda a, b: a + b, arg_count=2))
    parser.register(Operator(token='-', precedence=1, associativity=ASSOCIATIVITY_LEFT, func=lambda a, b: a - b, arg_count=2, on_shunt=parser.on_shunt_subtract_negate))  # on_shunt translates - to -- for negating
    parser.register(Operator(token='=', precedence=0, associativity=ASSOCIATIVITY_RIGHT, func=parser.assign, arg_count=2))

    parser.register(Function(token='vec', func=lambda x, y, z: Vector(x, y, z), arg_count=3))
    parser.register(Function(token='vnorm', func=lambda a: a.normal(), arg_count=1))
    parser.register(Function(token='vdot', func=lambda a, b: a.dot(b), arg_count=2))
    parser.register(Function(token='vcross', func=lambda a, b: a.cross(b), arg_count=2))
    parser.register(Function(token='vlen', func=lambda a: a.length(), arg_count=1))
    parser.register(Function(token='vlensq', func=lambda a: a.length_sq(), arg_count=1))

    parser.register(Function(token='min', func=min, arg_count=2))
    parser.register(Function(token='max', func=max, arg_count=2))
    parser.register(Function(token='sqrt', func=math.sqrt, arg_count=1))
    parser.register(Function(token='abs', func=abs, arg_count=1))
    parser.register(Function(token='floor', func=math.floor, arg_count=1))
    parser.register(Function(token='ceil', func=math.ceil, arg_count=1))
    parser.register(Function(token='log', func=math.log10, arg_count=1))
    parser.register(Function(token='ln', func=math.log, arg_count=1))
    parser.register(Function(token='cos', func=math.cos, arg_count=1))
    parser.register(Function(token='sin', func=math.sin, arg_count=1))
    parser.register(Function(token='tan', func=math.tan, arg_count=1))
    parser.register(Function(token='acos', func=math.acos, arg_count=1))
    parser.register(Function(token='asin', func=math.asin, arg_count=1))
    parser.register(Function(token='atan', func=math.atan, arg_count=1))
    parser.register(Function(token='atan2', func=math.atan2, arg_count=2))
    parser.register(Function(token='deg', func=math.degrees, arg_count=1))
    parser.register(Function(token='rad', func=math.radians, arg_count=1))
    parser.register(Function(token='rand', func=random.random, arg_count=0))

    parser.register(Function(token='pi', func=lambda: math.pi, arg_count=0))
    parser.register(Function(token='e', func=lambda: math.e, arg_count=0))

    return parser


REGEX_MESSAGE_START = re.compile(r'^(?:{})?='.format(REGEX_PART_VARIABLE))
PARSER = build_parser()


def infix(client, message):
    if message.content == '=?':
        client.messages.put(message.channel_id, "<@{}> Here is what I understand about math:\n```Operators:\n  {}\n\nFunctions:\n  {}\n\nVariables:\n  {}```".format(
            message.author.id,
            ', '.join([op.token for op in PARSER.operators.itervalues() if not op.hidden]),
            ', '.join([fn for fn in sorted(PARSER.functions.keys())]),
            ', '.join(['{}={}'.format(k, PARSER.variables[k]) for k in sorted(PARSER.variables.keys())])
        ))
        return

    if not REGEX_MESSAGE_START.match(message.content):
        return

    try:
        result = PARSER.parse(message.content)
        client.messages.put(message.channel_id, '<@{}> I got {}'.format(message.author.id, result))
    except Exception as e:
        import traceback
        traceback.print_exc()
        client.messages.put(message.channel_id, "<@{}> I couldn't undestand that ({}).".format(message.author.id, str(e)))
