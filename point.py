import math


class Point:
    def __init__(self, x, y, flag):
        self.x = x
        self.y = y
        self.flag = flag
        self.nbr_tag = 0.0
        self.id = 0
        self.score = 0.0

    def length(self):
        return math.sqrt(self.x * self.x + self.y * self.y)

    def display(self):
        print("%d %d %d %d %.5f" % (self.x, self.y, self.nbr_tag, self.id, self.score))

    def distance(self, point):
        return math.sqrt(pow((self.x - point.x), 2) + pow((self.y - point.y), 2))

    def toString(self):
        temp = "(" + str(self.x) + " " + str(self.y) + ")"
        return temp

    def equal(self, point):
        if self.x == point.x and self.y == point.y:
            return 0
        else:
            return -1

    def __lt__(self, other):
        return self.nbr_tag < other.nbr_tag

    def minus(self, point):
        return self.x - point.x, self.y - point.y

    def add(self, point):
        return self.x + point.x, self.y + point.y

    def square(self):
        return self.x * self.x, self.y * self.y


def main():
    p1 = Point(3, 2, 1)
    p2 = Point(2, 1, 1)
    dist = p1.distance(p2)
    print(dist)


# this is the standard boilerplate that calls the main() function
if __name__ == '__main__':
    # sys.exit(main(sys.argv)) # used to give a better look to exists
    main()
