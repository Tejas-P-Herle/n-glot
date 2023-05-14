def calc(a, b, opr):
    if opr == "+":
        print("SUM", a+b)
    elif opr == "-":
        print("SUB", a-b)
    elif opr == "*":
        print("MUL", a*b)
    elif opr == "/":
        print("DIV", a/b)


def main():
    a = 1
    b = 2
    opr = "/"
    calc(a, b, opr)


if __name__ == "__main__":
    main()
