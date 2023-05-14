def fact(n):
    if n == 0:
        return 1
    return n * fact(n-1)


def main():
    n = 10
    print(fact(n))


if __name__ == "__main__":
    main()

