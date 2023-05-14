class RootClass:
    n = 10
    class NestMethod:
        class DoubleNestMethod:
            def __init__(self):
                print("Double Nest Method")

        def __init__(self):
            print("Nest in Method")
            def nest_func():
                return 5.5
            q = nest_func()
            r3 = self

    def __init__(self):
        print("MSG FROM ROOT CLASS")

        class InFuncClass:
            def __init__(self):
                print("NEST IN FUNC")

                r2 = self

        ifc = InFuncClass()
        nm = self.NestMethod()
        dnm = self.NestMethod.DoubleNestMethod()
        z = self.n

        r1 = self

        print("Z", z)

def main():
    rc = RootClass()
    dnm = RootClass.NestMethod.DoubleNestMethod()

if __name__ == "__main__":
    main()
