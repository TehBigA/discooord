'''from shlex import shlex
from StringIO import StringIO'''


'''def parse_quoted_string(s):
    return list(shlex(StringIO(s), '', posix=True))'''


def parse_argument_string(s):
    output = []
    quote = None
    escape = 0
    argument = ''

    for i, c in enumerate(s):
        if c == '\\':
            if escape % 2 == 1:
                escape -= 1
                argument += c
            else:
                escape += 1
        elif c in '\'"':
            if escape % 2 == 1:
                escape -= 1
                argument += c
            elif c == quote:
                quote = None
                output.append(argument)
                argument = ''
            elif quote is None:
                quote = c
            else:
                argument += c
        elif c == ' ' and quote is None:
            if escape % 2 == 1:
                escape -= 1
                argument += c
            elif argument:
                output.append(argument)
                argument = ''
        else:
            if escape % 2 == 1:
                escape -= 1
                # TODO: Escape chars
            argument += c

    if argument:
        output.append(argument)

    return output
