#!/usr/bin/env python

"""
a work in progress toy python interpreter
"""

# python 2/3 compatibility
from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals
)
import sys
if sys.version_info < (3, 0):
    input = raw_input  # pylint: disable=redefined-builtin,invalid-name


class Token(object):  # pylint: disable=too-few-public-methods
    """ basic token, holds identifier along with human readable strings """
    def __init__(self, ident, string=None, value=None):
        self.ident = ident
        if string is None:
            self.string = str(self.ident)
        else:
            self.string = string
        self.value = value

    def __repr__(self):
        if self.value is None:
            return '<' + str(self.string) + '>'
        else:
            return '<' + str(self.string) + ', ' + str(self.value) + '>'

    def with_value(self, value):
        """ return a new token like self but with a specific value """
        new_token = Token(self.ident, self.string)
        new_token.value = value
        return new_token


class Lexer(object):
    """ convert input line into a stream of tokens """

    # tokens
    nothing = Token(0)
    error = Token(1)
    error_indentation = Token(error.ident, 'IndentationError')
    error_syntax = Token(error.ident, 'SyntaxError', 'invalid syntax')

    newline = Token(100, 'newline')
    indent = Token(101, 'indent')
    dedent = Token(102, 'dedent')

    # identifiers
    identifier = Token(200, 'identifier')

    # keywords
    keyword = Token(300, 'keyword')
    keywords = ['False', 'None', 'True', 'and', 'as', 'assert', 'break',
                'class', 'continue', 'def', 'del', 'elif', 'else', 'except',
                'finally', 'for', 'from', 'global', 'if', 'import', 'in',
                'is', 'lambda', 'nonlocal', 'not', 'or', 'pass', 'raise',
                'return', 'try', 'while', 'with', 'yield']

    # literals
    literal_string = Token(400, 'literal_string')
    literal_integer = Token(401, 'literal_integer')
    literal_float = Token(402, 'literal_float')

    # operators
    operator = Token(500, 'operator')
    operators = ['+', '-', '*', '**', '/', '//', '%', '<<', '>>', '&', '|',
                 '^', '~', '<', '>', '<=', '>=', '==', '!=']

    # delimiters
    delimiter = Token(600, 'delimiter')
    delimiters = ['(', ')', '[', ']', '{', '}', ',', ':', '.', ';', '=', '@']

    def __init__(self):
        self.state = None
        self.indent = None
        self.parens = None
        self.line = None
        self.continuation = None
        self._reset()

    def _reset(self):
        """ reset full lexer state """
        self.state = self.state_indent
        self.indent = [0]
        self.parens = 0
        self.line = ''
        self.continuation = False

    def _peek(self, count):
        """
        get a list of length count with either character values or None
        do not modify current data
        """
        if len(self.line) >= count:
            return self.line[:count]
        return [None] * count

    def _pop(self, count):
        """
        get a list of length count with either character values or None
        update current data by removing count values
        """
        if len(self.line) >= count:
            res = self._peek(count)
            self.line = self.line[count:]
            return res
        return [None] * count

    def lex(self, line):
        """ add another line to be lexed and run current state """

        # only add line if we are in a continuation or line is not empty
        if self.continuation is True or line.strip() != '':
            self.line += line

        self.continuation = False
        # keep running states until out of data or we need a continuation
        while self.continuation is False and len(self.line) > 0:
            for token in self.state():
                if token.ident == Lexer.error.ident:
                    yield token
                    # reset state on error
                    self._reset()
                    return
                yield token

    def state_indent(self):
        """ starting lex state for a new, non-continued line """
        # get indent level
        indent = 0
        while self._peek(1) == ' ' or self._peek(1) == '\t':
            indent += 1
            self._pop(1)

        # if new indent is larger, push it and generate indent token
        if indent > self.indent[0]:
            self.indent.insert(0, indent)
            yield Lexer.indent

        # if new indent is smaller, pop off the stack till we match
        while indent < self.indent[0]:
            self.indent = self.indent[1:]
            yield Lexer.dedent

        # make sure the new indent level matches a previous level
        if self.indent[0] != indent:
            yield Lexer.error_indentation.with_value(
                'unindent does not match any outer indentation level')
            return

        self.state = self.state_whitespace

    def state_whitespace(self):
        """ consume all whitespace, but don't generate tokens """
        while self._peek(1) == ' ' or self._peek(1) == '\t':
            self._pop(1)
        self.state = self.state_newline
        return []  # fake generator

    def state_newline(self):
        """ lex a newline, if found then go to starting state """
        if self._peek(1) == '\n':
            self._pop(1)
            if self.parens == 0:
                # only generate newline if we are not in a paren block
                yield Lexer.newline
                # go to starting state
                self.state = self.state_indent
            else:
                # we are in a paren block
                self.state = self.state_whitespace
        else:
            self.state = self.state_comment

    def state_comment(self):
        """ discard comments, turns into a newline and go to starting state"""
        if self._peek(1) == '#':
            # consume through the newline
            while self._pop(1) != '\n':
                pass
            yield Lexer.newline
            # go to starting state
            self.state = self.state_indent
        else:
            self.state = self.state_line_continuation

    def state_line_continuation(self):
        """ backslash means we need another line """
        if self._peek(2) == '\\\n':
            self._pop(2)
            self.continuation = True
            self.state = self.state_whitespace
        else:
            self.state = self.state_identifier
        return []  # fake generator

    def state_identifier(self):
        """ either an identifier or a keyword """
        if self._peek(1) in 'abcdefghijklmnopqrstuvwxyz' \
                            'ABCDEFGHIJKLMNOPQRSTUVWXYZ_':
            identifier = ''
            while self._peek(1) in 'abcdefghijklmnopqrstuvwxyz' \
                                   'ABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789':
                identifier += self._pop(1)
            if identifier in Lexer.keywords:
                yield Lexer.keyword.with_value(identifier)
            else:
                yield Lexer.identifier.with_value(identifier)
            self.state = self.state_whitespace
        else:
            self.state = self.state_number

    def state_number(self):
        """ integer or float literal """
        if (self._peek(2)[0] == '.' and self._peek(2)[1] in '0123456789') or \
                self._peek(1) in '0123456789':
            number = ''
            token = Lexer.literal_integer
            while self._peek(1) in '0123456789.':
                char = self._pop(1)
                number += char
                if token.ident == Lexer.literal_integer.ident and \
                        char == '.':
                    token = Lexer.literal_float
                elif char == '.':
                    yield Lexer.error_syntax
                    return
            yield token.with_value(number)
            self.state = self.state_whitespace
        else:
            self.state = self.state_string

    def state_string(self):
        """ long and short strings """
        quote = None

        if self._peek(3) == '\'\'\'' or self._peek(3) == '"""':
            quote = self._pop(3)
        elif self._peek(1) == '\'' or self._peek(1) == '"':
            quote = self._pop(1)
        else:
            self.state = self.state_operator
            return

        string = ''
        while self._peek(len(quote)) != quote:
            char = self._pop(1)

            # handle escape sequences
            if char == '\\':
                char = self._peek(1)
                if char == '\\':
                    char = self._pop(1)
                elif char == '\'':
                    char = self._pop(1)
                elif char == '"':
                    char = self._pop(1)
                elif char == 't':
                    char = '\t'
                    self._pop(1)

            string += char
            if char == '\n' and len(quote) == 1:
                yield Lexer.error_syntax.with_value(
                    'EOL while scanning string literal')
                return
            elif char == '\n' and len(self.line) == 0:
                # multi-line triple quote string, so reset and get more lines
                # NOTE: this seems a bit clumsy
                self.line = quote + string
                self.continuation = True
                return
        self._pop(len(quote))

        yield Lexer.literal_string.with_value(string)
        self.state = self.state_whitespace

    def state_operator(self):
        """ binary and unary operators """
        if self._peek(2) in Lexer.operators:
            yield Lexer.operator.with_value(self._pop(2))
            self.state = self.state_whitespace
        elif self._peek(1) in Lexer.operators:
            yield Lexer.operator.with_value(self._pop(1))
            self.state = self.state_whitespace
        else:
            self.state = self.state_delimiter

    def state_delimiter(self):
        """ lexer delimiters, some may be syntax operators """
        if self._peek(1) in Lexer.delimiters:
            if self._peek(1) == '(':
                self.parens += 1
            elif self._peek(1) == ')':
                self.parens -= 1
            yield Lexer.delimiter.with_value(self._pop(1))
            if self.parens < 0:
                yield Lexer.error_syntax
            self.state = self.state_whitespace
        else:
            self.state = self.state_whitespace  # no more states


class Parser(object):  # pylint: disable=too-few-public-methods
    """ lex and evaluate input lines """

    def __init__(self):
        self.lexer = Lexer()

    def parse(self, line):
        """ parse tokens line by line """

        for token in self.lexer.lex(line):
            if token.ident == Lexer.error.ident:
                # if the lexer found an error, print it
                print("Traceback\n " + line)
                print(token)
                return ''
            print(repr(token), end=' ')
        print()

        # if we need another line, return None
        if self.lexer.continuation is True or self.lexer.parens > 0:
            return None

        return ''


def use_repl():
    """ interactive input """
    parser = Parser()
    prompt = '>'
    result = ''
    while True:
        print(prompt, end=' ')
        try:
            result = parser.parse(input() + '\n')
            if result is not None:
                if result != '':
                    print(result)
                prompt = '>'
            else:
                prompt = '.'
        except EOFError:
            print()
            break


def use_file(filename):
    """ read from a file """
    parser = Parser()
    with open(filename) as pyfile:
        for line in pyfile:
            parser.parse(line)


if __name__ == '__main__':
    if len(sys.argv) == 1:
        use_repl()
    else:
        use_file(sys.argv[1])
