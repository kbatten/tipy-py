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
    input = raw_input


class Token(object):
    """ basic token, holds identifier along with human readable strings """
    def __init__(self, ident, string=None):
        self.ident = ident
        if string is None:
            self.string = str(self.ident)
        else:
            self.string = string
        self.value = None

    def with_value(self, value):
        """ return a new token like self but with a specific value """
        new_token = Token(self.ident, self.string)
        new_token.value = value
        return new_token

    def __repr__(self):
        if self.value is None:
            return '(' + str(self.string) + ')'
        else:
            return '(' + str(self.string) + ', ' + str(self.value) + ')'


class Lexer(object):
    """ convert input line into a stream of tokens """

    # tokens
    nothing = Token(0)

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
    delimiters = ['(', ')', '[', ']', '{', '}', ',', ':', '.', ';', '=']

    def __init__(self):
        self.indent = [0]

    def lex(self, line):
        """ lexagraphically analyze a line and emit tokens """

        line += '\n'

        tokens = []

        # INDENT

        # get indent level
        indent = 0
        while line[0] == ' ':
            indent += 1
            line = line[1:]

        # if new indent is larger, push it and generate indent token
        if indent > self.indent[0]:
            self.indent.insert(0, indent)
            tokens.append(Lexer.indent)

        # if new indent is smaller, pop off the stack till we match
        while indent < self.indent[0]:
            self.indent = self.indent[1:]
            tokens.append(Lexer.dedent)
        # make sure the new indent level matched
        if self.indent[0] != indent:
            raise IndentationError('unindent does not match any outer'
                                   'indentation level')

        while True:
            # WHITESPACE
            while line[0] == ' ':
                line = line[1:]

            # NEWLINE
            if line[0] == '\n':
                tokens.append(Lexer.newline)
                break

            # COMMENT
            elif line[0] == '#':
                tokens.append(Lexer.newline)
                break

            # IDENTIFIERS and KEYWORDS
            elif line[0] in 'abcdefghijklmnopqrstuvwxyz' \
                    'ABCDEFGHIJKLMNOPQRSTUVWXYZ_':
                identifier = ''
                while line[0] in 'abcdefghijklmnopqrstuvwxyz' \
                        'ABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789':
                    char = line[0]
                    line = line[1:]
                    identifier += char
                if identifier in Lexer.keywords:
                    tokens.append(Lexer.keyword.with_value(identifier))
                else:
                    tokens.append(Lexer.identifier.with_value(identifier))

            # LITERALS

            # shortstring
            elif line[0] == '\'' or line[0] == '"':
                quote_char = line[0]
                line = line[1:]
                string = ''
                while line[0] != quote_char and line[0] != '\n':
                    char = line[0]
                    line = line[1:]
                    string += char
                if line[0] == quote_char:
                    # if previous token was also a literal string, concatinate
                    token_prev = Lexer.nothing
                    if len(tokens) > 0:
                        token_prev = tokens[-1]
                    if token_prev.ident == Lexer.literal_string.ident:
                        string = token_prev.value + string
                        tokens = tokens[:-1]
                    tokens.append(Lexer.literal_string.with_value(string))
                    line = line[1:]
                else:
                    raise SyntaxError('EOL while scanning string literal')

            # integer or floating point
            elif (len(line) >= 2 and line[0] == '.' and
                  line[1] in '0123456789') or \
                    line[0] in '0123456789':
                string = ''
                token = Lexer.literal_integer
                while line[0] in '0123456789.':
                    char = line[0]
                    line = line[1:]
                    string += char
                    if token.ident == Lexer.literal_integer.ident and \
                            char == '.':
                        token = Lexer.literal_float
                    elif char == '.':
                        raise SyntaxError('invalid syntax')
                tokens.append(token.with_value(string))

            # OPERATORS
            elif (len(line) >= 2 and line[:2] in Lexer.operators) or \
                    line[0] in Lexer.operators:
                if len(line) >= 2 and line[:2] in Lexer.operators:
                    tokens.append(Lexer.operator.with_value(line[:2]))
                    line = line[2:]
                elif line[0] in Lexer.operators:
                    tokens.append(Lexer.operator.with_value(line[0]))
                    line = line[1:]
                else:
                    raise SyntaxError('invalid syntax')

            # DELIMITERS
            elif line[0] in Lexer.delimiters:
                tokens.append(Lexer.delimiter.with_value(line[0]))
                line = line[1:]

            else:
                raise SyntaxError('invalid syntax')

        return tokens


class Parser(object):
    """ lex and evaluate input lines """

    def __init__(self):
        self.lexer = Lexer()

    def parse(self, line):
        """ parse tokens line by line """

        for token in self.lexer.lex(line):
            print(repr(token))
        return "<output>"


def main():
    """ entry point """
    parser = Parser()
    ans = ""
    while True:
        try:
            if ans is not None:
                print("> ", end='')
            else:
                print(". ", end='')
            ans = parser.parse(input())
        except EOFError:
            print()
            break
        if ans is not None:
            print(ans, end='\n')

if __name__ == '__main__':
    main()
