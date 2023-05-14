# Overload collision


def overloaded_func(a, b="str_b", c="str_c"):
    print("a", a, "b", b, "c", c)

def main():
    overloaded_func("Hi")
    overloaded_func("Hey", "There")
    overloaded_func("How", "Are", "You")
    overloaded_func("str_a", c="str_c_overwrite")
    overloaded_func("str_a", b="str_b_overwrite")
    overloaded_func("str_a", c="str_c_overwrite", b="str_b_overwrite")
    overloaded_func("str_a", b="str_b_overwrite", c="str_c_overwrite")


if __name__ == "__main__":
    main()

