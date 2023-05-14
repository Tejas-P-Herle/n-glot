PI = 3.14


class Test:
    attr = "attr_val"
    def __init__(self, pos, kw="a"):
        self.testing_attr = True
        print("POS", pos)
        def state_upper_check():
            return 1
        s = self.attr
        r, n, d = 1, 2, 3

    def do_(self, arg):
        print("ARG", arg)

class Test2:
    def dont(self, arg):
        print("NOT ARG", arg)

def func():
    a = 2.0
    def confuser():
        return "a"
    return a

def func2():
    q = func()
    return 3

def rand_func(string, f=func2()):
    if True:
        print("String:", string, "f:", f)

def main():
    c, a, b = 30, 1.5 + 2 +\
        3 + 4\
        + 5 + 6, func()
    [e, f, g] = [2/0.3, 3, 4]
    e += 1
    e **= 3
    print("E", e)
    h = c/3.14
    # Comment Check
    j = c*h/2

    k = 2
    k = 1/3

    m = 3+2/1
    def name():
        testing = True
        def nest():
            return 1
    rand_func("a")
    q = Test(1)
    print("hi", 3+2/1, c, "there")
    print("Hello World");print("Another Statment")
    print("HI")
    return


if __name__ == "__main__":
    rand_func("HI", 4)
    rand_func("HELLO AGAIN")
    a = 3_1
    main()
