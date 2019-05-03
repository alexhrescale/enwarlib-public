'''
Rudimentary parser logic. This is designed for fishing out bash variables and
little else. If you need more extensive parsing capability, you should use
https://github.com/idank/bashlex

The reason for the ad-hoc parser is because bashlex does not currently handle
arithmetic expressions.

The parser does not use recursive descent, and does not understand the difference
between `cat` in `$(cat mouse)` and `$((cat + mouse))`.

In bash, `$(cat mouse)` will invariably invoke the shell command `cat mouse`.
Whereas in `$$(cat + mouse))`, `cat` is expected to be a variable just like
`mouse`. In addition, `$((cat + mouse))` is equivalent to `$(($cat + $mouse))`.

The parser here is unable to handle positional arguments, so in the cat mouse
example above, both will be extracted as variables regardless of $() or $(()).
'''

import re


class ExpressionType:
    ARITHMETIC_COMMAND = 'ARITHMETIC_COMMAND'
    COMMAND_SUBSTITUTION = 'COMMAND_SUBSTITUTION'
    VARIABLE_NAME = 'VARIABLE_NAME'
    ANY = 'ANY'


class NestedExpressionMatcher:

    def __init__(self,
                 open_pattern,
                 close_pattern,
                 type=ExpressionType.ANY):
        self.p_open = re.compile(open_pattern)
        self.p_close = re.compile(close_pattern)
        self.type = type
        self.current_match = None

    def update_match(self, pattern, expr):
        self.current_match = pattern.match(expr)
        return self.current_match

    def matches_open(self, expr):
        return self.update_match(self.p_open, expr)

    def matches_close(self, expr):
        return self.update_match(self.p_close, expr)


class Token:
    def __init__(self, type, value):
        self.type = type
        self.value = value


class CharBuffer:
    buf = None  # list
    tokens = None  # list
    matcher_stack = None  # list
    detected_variables = None  # list

    def __init__(self):
        self.buf = []
        self.tokens = []
        self.matcher_stack = []
        self.detected_variables = []

    def is_variable_directly_substituted(self):
        if self.matcher_stack and \
                self.matcher_stack[-1].type == \
                ExpressionType.VARIABLE_NAME:
            return True
        for matcher in self.matcher_stack:
            if matcher.type == ExpressionType.ARITHMETIC_COMMAND:
                return True

    def extract_variable(self, expr):
        base_pattern = r'[_a-zA-Z]+[_a-zA-Z0-9]*'
        if self.is_variable_directly_substituted():
            var_pattern = '.*?{}?({})'.format(re.escape(r'$'), base_pattern)
        else:
            var_pattern = '.*?{}({})'.format(re.escape(r'$'), base_pattern)
        maybe_match = re.match(var_pattern, expr)
        if maybe_match:
            return maybe_match.group(1)

    def flush(self):
        if self.buf:
            if self.tokens and self.tokens[-1].type == \
                    ExpressionType.COMMAND_SUBSTITUTION:
                token_type = ExpressionType.ANY
            elif self.matcher_stack:
                token_type = self.matcher_stack[-1].type
            else:
                token_type = ExpressionType.ANY

            tok = Token(
                token_type,
                ''.join(self.buf),
            )
            self.tokens.append(tok)
            self.buf = []

            maybe_variable = self.extract_variable(tok.value)
            if maybe_variable:
                self.detected_variables.append(maybe_variable)

    def push(self, ch):
        self.buf.append(ch)


class BashExpressionParser:

    def __init__(self, expr=None):
        self._buffer = None
        if expr:
            self.parse(expr)

    def parse(self, expr):
        self._buffer = CharBuffer()
        _rq = re.escape
        matchers = []
        for expr_matcher in \
                [
                    NestedExpressionMatcher(
                        _rq(r'$(('), _rq(r'))'),
                        ExpressionType.ARITHMETIC_COMMAND),
                    NestedExpressionMatcher(_rq(r'[['), _rq(r']]')),
                    NestedExpressionMatcher(
                        _rq(r'`'), _rq(r'`'),
                        ExpressionType.COMMAND_SUBSTITUTION),
                    NestedExpressionMatcher(
                        _rq(r'$('), _rq(r')'),
                        ExpressionType.COMMAND_SUBSTITUTION),
                    NestedExpressionMatcher(
                        _rq(r'${'), _rq(r'}'),
                        ExpressionType.VARIABLE_NAME),
                ] + [
                    NestedExpressionMatcher(_rq(pair[0]), _rq(pair[1]))
                    for pair in '{} [] () ""'.split()
                ]:
            matchers.append(expr_matcher)
        matchers.sort(key=lambda m: -len(m.p_open.pattern))

        idx = 0
        while idx < len(expr):
            shift = 1
            is_matched = False
            fragment = expr[idx:]

            maybe_token_boundary = re.match(r'(?::|-|;|/|\s)+', fragment)
            if maybe_token_boundary:
                self._buffer.flush()
                shift = len(maybe_token_boundary.group(0))
                is_matched = True

            if self._buffer.matcher_stack:
                if self._buffer.matcher_stack[-1].matches_close(fragment):
                    self._buffer.flush()
                    shift += len(
                        self._buffer.matcher_stack[-1]
                            .current_match
                            .group(0)
                    ) - 1
                    self._buffer.matcher_stack.pop()
                    is_matched = True
            if not is_matched:
                for matcher in matchers:
                    if matcher.matches_open(fragment):
                        self._buffer.flush()
                        self._buffer.matcher_stack.append(matcher)
                        token = matcher.current_match.group(0)
                        shift += len(token) - 1
                        is_matched = True
                        break
            if not is_matched:
                token = expr[idx]
                self._buffer.push(token)
            idx += shift
        self._buffer.flush()

    def get_variables(self):
        if not self._buffer:
            return None
        return self._buffer.detected_variables
