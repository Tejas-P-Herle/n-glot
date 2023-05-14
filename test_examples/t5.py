def list_ret():
    return [0x1, 3.14, 0b100, 5, 0o10, 2_2]

def main():
    a = [2, 4, 5]
    print(a)
    b = list_ret()
    print(b)

if __name__ == "__main__":
    main()
