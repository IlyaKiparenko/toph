from dataclasses import dataclass
from enum import Enum

from test_framework import Tester

class TokenType(Enum):
    SPACE = 1
    NUMBER = 2
    IDENTIFIER = 3
    STRING = 4
    OPERATOR = 5

@dataclass
class TextPos:
    idx: int
    end_idx: int
    file: str = '.'

@dataclass
class Token:
    _type: TokenType
    s: str
    pos: TextPos


class Parser:
    def __init__(self, s):
        self.s = s
        self.cur_pos = 0
        self.tokens = []
        self.build_operator_map()

    def parse(self):
        while self.pos() < self.size():
            self.consume()

    def add_token(self, tok: Token):
        self.tokens.append(tok)

    def pos(self):
        return self.cur_pos

    def size(self):
        return len(self.s)

    def advance(self):
        self.cur_pos += 1
    
    def advance_until(self, fun):
        
        while self.pos() < self.size() and fun(self.cur()):
            self.advance()

    def error(self, msg): 
        context = 20
        near = self.s[max(0, self.cur_pos - context):
                      self.cur_pos + context]
        raise ValueError (f'Lexer error at {self.pos()} near {near} msg {msg}')
    
    def cur(self):
        if self.pos() >= len(self.s):
            self.error("End of file")
        return self.s[self.pos()]

    def peek(self):
        if self.pos() >= len(self.s):
            return None
        return self.cur()

    # works on list of chars
    def assume(self, chars):
        if self.cur() not in chars:
            self.error(f"Assumed {chars} but got {self.cur()}")

    class TokenManager:
        def __init__(self, parser):
            self.parser = parser
            self.ok = False

        def __enter__(self):
            self.start = self.parser.pos()
            return self

        def add_value(self, _type, value=None):
            self.ok = True
            self._type = _type
            self.value = value

        def __exit__(self, *args, **kwargs):
            if not self.ok:
                self.parser.error(f'Bad token finish {self.start}')
            value = self.value
            pos = self.parser.pos()
            s = self.parser.s[self.start:pos]
            if value is not None:
                s = str(value)
            text_pos = TextPos(self.start, pos) # file
            token = Token(_type = self._type,
                          s = s, pos = text_pos)

            self.parser.add_token(token)
                          
            
    def consume_space(self):
        spaces = ' \t\r\n'
        self.assume(spaces)
        with self.TokenManager(self) as tm:
            fun = lambda c: c in spaces
            self.advance_until(fun)
            tm.add_value(TokenType.SPACE)
        
    def consume_string(self):
        self.assume('\'"')
        _open = self.cur()
        res = ''

        escapes = { 'n' : '\n', 't': '\t', 'r': '' }
        with self.TokenManager(self) as tm:
            closed = False
            while self.pos() < self.size():
                self.advance()
                c = self.cur()
                if c == '\\':
                    self.advance()
                    c = self.cur()
                    if c in escapes:
                        c = escapes[c]
                    res += c
                    continue
                if c == _open:
                    self.advance()
                    closed = True
                    break
                res += c
            if not closed:
                self.error("Unclosed string")
            tm.add_value(TokenType.STRING, res)

    def consume_number(self):
        start = self.pos()
        if not self.cur().isdigit():
            error("Bad number assume")
            
        with self.TokenManager(self) as tm:
            fun = lambda c: c.isdigit()
            self.advance_until(fun)
            if self.cur() == '.':
                self.advance()
                self.advance_until(fun)
            tm.add_value(TokenType.NUMBER)

    def consume_identifier(self):
        if not self.cur().isalpha():
            error("Bad identifier assume")
        with self.TokenManager(self) as tm:
            fun = lambda c: c.isalnum() or c == '_'
            self.advance_until(fun)
            tm.add_value(TokenType.IDENTIFIER)

    def build_operator_map(self):
        ops = [
            '++', '--', '**',
            '->', '//', '+=',
            '-=', '/=', '*=',
            '%=', '>>', '<<',
            '&&', '||']

        self.operators = ops
            
    def consume_operator(self):
        c = self.cur()
        with self.TokenManager(self) as tm:
            self.advance()
            p = self.peek()
            if p is not None:
                lp = c + p
                if lp in self.operators:
                    self.advance()
            tm.add_value(TokenType.OPERATOR)
            
    def consume(self):
        c = self.cur()
        if c.isdigit():
            self.consume_number()
        elif c.isalpha():
            self.consume_identifier()
        elif c in '\'"':
            self.consume_string()
        elif c in ' \t\r\n':
            self.consume_space()
        else:
            self.consume_operator()

def apply_lexer(s):
    p = Parser(s)
    p.parse()
    return p.tokens


def do_test():
    @dataclass
    class LexerTest:
        name: str
        s: str
        expect_n: int
        check_type: list

        def check(self, tester):
            p = Parser(self.s)
            p.parse()
            tokens = p.tokens

            if tester.test_compare (len(tokens), self.expect_n):
                return False

            return tester.run_subcheckers(self.check_type, tokens)

    @dataclass
    class CheckType:
        idx: int
        _type: TokenType

        def check(self, tester, tokens):
            return not tester.test_compare(tokens[self.idx]._type, self._type)

    @dataclass
    class CheckValue:
        idx: int
        value: str

        def check(self, tester, tokens):
            return not tester.test_compare(tokens[self.idx].s, self.value)
        
    tests = [
        LexerTest ('single_indentifier',
                   'aa0_5b', 1, [CheckType(0, TokenType.IDENTIFIER),
                                 CheckValue(0, 'aa0_5b')]),
        LexerTest ('single_string_double',
                   r'''"''\t'\q\j'\\\""''', 1, [CheckType(0, TokenType.STRING),
                                                CheckValue(0, r"""''	'qj'\"""")]),
        LexerTest ('single_string_single',
                   "'axaxaxa0_\\\\'", 1, [CheckType(0, TokenType.STRING),
                                          CheckValue(0, 'axaxaxa0_\\')]),
        LexerTest ('single_number',
                   '100.88', 1, [CheckType(0, TokenType.NUMBER),
                                 CheckValue(0, '100.88')]),
        LexerTest ('single_space',
                   ' \t', 1, [CheckType(0, TokenType.SPACE),
                              CheckValue(0, ' \t')]),
        LexerTest ('single_operator',
                   '+=', 1, [CheckType(0, TokenType.OPERATOR),
                            CheckValue(0, '+=')]),
        LexerTest ('complex',
                   'a[10] += "Hello"', 8, []),
    ]

    Tester().run(tests)
    
if __name__ == "__main__":
    do_test()
