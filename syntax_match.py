from dataclasses import dataclass, field
from meta_lexer import Token, TokenType, apply_lexer

class SupplierEnd(Exception):
    pass

DEBUG_PRINTS = False

class TokenSupplier:
    def __init__(self, tokens, idx):
        self.tokens = tokens
        self.idx = idx

    def copy(self):
        return TokenSupplier(self.tokens, self.idx)

    def save_state(self, other):
        self.idx = other.idx
        if DEBUG_PRINTS:
            print(f"[Supp statechange save {self.idx}]")

    def eof(self):
        return self.idx >= len(self.tokens)
        
    def cur(self):
        if self.eof():
            raise SupplierEnd
        return self.tokens[self.idx]

    def get_cur(self):
        c = self.cur()
        self.next()
        return c

    def next(self):
        self.idx += 1
        if DEBUG_PRINTS:
            print(f"[Supp statechange next {self.idx}]")

    class SupplierSaver:
        def __init__(self, supplier):
            self.supplier = supplier
            self.copy = supplier.copy()
            self.produced = False

        def __enter__(self):
            return self.copy

        def set_produce(self):
            self.produced = True

        def __exit__(self, *args, **kwargs):
            if self.produced:
                self.supplier.save_state (self.copy)

    

@dataclass
class AbstractMatcher:
    value_consumer: None = field(repr=False)
    
    def match(self, supplier):
        #with TokenSupplier.SupplierSaver(supplier) as copy:
        copy = supplier.copy()
        original = copy.copy()
        try:
            if DEBUG_PRINTS:
                print(f'Try match in {self} at {copy.idx}')
            for value in self.inner_match(copy):
                if DEBUG_PRINTS:
                    print(f'Match ok {value} in {self} at {copy.idx}')
                supplier.save_state(copy)
                if self.value_consumer:
                    yield self.value_consumer.apply(value)
                else:                    
                    yield value
                #copy = original.copy()
        except SupplierEnd:
            pass
        except:
            raise

        #return False

@dataclass
class TypeMatcher(AbstractMatcher):
    _type: TokenType

    def inner_match(self, supplier):
        cur = supplier.cur()
        supplier.next()
        if cur._type == self._type:
            yield cur

@dataclass
class ValueMatcher(AbstractMatcher):
    value: str

    def inner_match(self, supplier):
        cur = supplier.cur()
        supplier.next()
        if cur.s == self.value:
            yield cur

@dataclass
class TypeValueMatcher(AbstractMatcher):
    _type: TokenType
    value: str

    def inner_match(self, supplier):
        cur = supplier.cur()
        supplier.next()
        if cur._type == self._type and cur.s == self.value:
            yield cur

@dataclass
class OrMatcher(AbstractMatcher):
    matchers: None

    def inner_match(self, supplier):
        #origin
        for matcher in self.matchers:
            sup = supplier.copy()
            for value in matcher.match(supplier):
                yield value


@dataclass
class RepeatMatcher(AbstractMatcher):
    matcher: None
    N_min: int
    N_max: int

    def _match_helper(self, supplier, cur_N):
        if self.N_max != -1 and cur_N >= self.N_max:
            return
        for value in self.matcher.match(supplier):
            if DEBUG_PRINTS:
                print("Repeat", cur_N, supplier.idx, value)
            sup = supplier #.copy()
            yield [value]
            for tail in self._match_helper(sup, cur_N + 1):
                yield [value] + tail

    def inner_match_choosy(self, supplier):
        if self.N_min == 0:
            yield []
        for full_match in self._match_helper(supplier, 0):
            if len(full_match) >= self.N_min:
                yield full_match

    #greedy
    def inner_match(self, supplier):
        ans = []
        if self.N_min == 0:
            ans.append(([], supplier.copy()))
        for full_match in self._match_helper(supplier, 0):
            if len(full_match) >= self.N_min:
                ans.append((full_match, supplier.copy()))
        for value, sup in reversed(ans):
            supplier.save_state(sup)
            yield value

@dataclass
class SequenceMatcher(AbstractMatcher):
    matchers: None

    def _match_helper(self, supplier, cur_N):
        if DEBUG_PRINTS:
            print("Seq", cur_N, supplier.idx, len(self.matchers))
        if len(self.matchers) == cur_N:
            yield []
            return

        for value in self.matchers[cur_N].match(supplier):
            sup = supplier#.copy()
            if DEBUG_PRINTS:
                print("Inner Seq", cur_N, supplier.idx, value)
            for tail in self._match_helper(sup, cur_N + 1):
                yield [value] + tail

    def inner_match(self, supplier):
        for full_match in self._match_helper(supplier, 0):
            yield full_match

@dataclass
class EndMatcher(AbstractMatcher):
    def inner_match(self, supplier):
        if supplier.eof():
            yield None

def value_pretty(a):
    if a is None:
        return a
    elif isinstance(a, list):
        return [value_pretty(v) for v in a]
    elif isinstance(a, Token):
        return f'{a._type.name}:[{a.s}]'
    else:
        return a

if __name__ == "__main__":
    plu = TypeValueMatcher(None,TokenType.OPERATOR, '+')
    slash = TypeValueMatcher(None,TokenType.OPERATOR, '/')
    iden = TypeMatcher(None,TokenType.IDENTIFIER)
    space = RepeatMatcher(None, TypeMatcher(None,TokenType.SPACE), 0, 1)
    end = EndMatcher(None)
    slash_group = SequenceMatcher(None,[slash, plu, slash])
    ope = OrMatcher(None,[slash_group, plu])
    part = SequenceMatcher(None,[iden, ope])
    rep_part = RepeatMatcher(None,part,1, -1)
    total = SequenceMatcher(None,[rep_part, iden, end])
    rep_op = RepeatMatcher(None, TypeMatcher(None,TokenType.OPERATOR), 1, -1)
    
    init = 'A/+/B+C'
    s = None
    while True:
        #s = input('>>> ')
        if not s:
            s = init
            print('>>>', s)

        tokens = apply_lexer(s)
        print('Tokens', tokens)
        supp = TokenSupplier(tokens, 0)

        n_res = 0
        out = []
        for ans in total.match(supp):
            print(f"\n\tRESULT {len(out)} - ", ans)
            out.append(ans)

        print('\nRESULTS:')
        for i, ans in enumerate(out):
            print(f'\tNICE {i} - ', value_pretty(ans))

        print(f'\tNumber matches {len(out)}')
        
        s = input('>>> ')
        if s == 'exit':
            break
