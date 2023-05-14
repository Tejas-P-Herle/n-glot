class NameCollisionTest:
    a = 10
    def __init__(self):
        print(self.a)
        self.a = 5.4
        print(self.a)
        b = 10
        b = 9.8
        c = 3.14
        print(c, self.a)

if __name__ == "__main__":
    NameCollisionTest()