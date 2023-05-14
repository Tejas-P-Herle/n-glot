
class Cls:
    class Nest:
        attr = 1
        def __init__(self):
            print("ATTR")
    def run(self):
        print(self)
        self.Nest.attr = 3
        nest = self.Nest()
        nest.attr = 5

        return self.Nest.attr


def main():
    pass


if __name__ == "__main__":
    print("HI")
    cls = Cls()
    status = cls.run()
    print("Status:", status)
    main()
