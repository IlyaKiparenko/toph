
class Tester:
    def __init__(self):
        pass

    def run(self, tests):
        good = 0
        for test in tests:
            self.cur_test = test
            ok = False
            try:
                res = test.check(self)
                if res:
                    ok = True
                    good += 1
            except Exception as e:
                self.test_fail(e)
                raise e
            if ok:
                print(f"[PASS] {self.cur_test.name}")
            
        print(f"Total PASSED {good}, FAILED {len(tests) - good}")

    def run_subcheckers(self, checkers, *args):
        if not checkers:
            return True
        for checker in checkers:
            if not checker.check(self, *args):
                return False
        return True

    def test_fail(self, msg):
        print(f"[FAIL] {self.cur_test.name} ", msg)
        #raise ValueError()

    def test_compare(self, actual, expected):
        if actual == expected:
            return False
        self.test_fail (f"Expected {expected} got {actual}")
        return True    
