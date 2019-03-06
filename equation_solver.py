from point import *
import numpy as np
import random
import datetime
from sympy.core.symbol import symbols
from sympy.solvers.solveset import nonlinsolve


# ********************************************************************************
# return a random number between 0.4-1.0
# this relative number mimic the tag received signal strength
def relative_error():
    seed = datetime.datetime.now().time()
    random.seed(seed)
    return random.uniform(0.9, 1)


# ********************************************************************************
def midpoint(p1, p2):
    new_x = (p1.x + p2.x) / 2
    new_y = (p1.y + p2.y) / 2
    return Point(new_x, new_y, 1)


# ********************************************************************************
def contains_point(p_list, point):
    for p in p_list:
        if p.equal(point) == 0:
            if p.flag == 0:
                return p
    return -1


# given a location (x,y) find tags around location
def find_tag(point, p_list, Tx, n, m):
    i, j = point.x, point.y
    if i < 0 or j < 0 or i >= n or j >= m:
        return list()

    tag_list = list()
    for x in range(i - Tx, i + Tx + 1):
        for y in range(j - Tx, j + Tx + 1):
            if (x != i) or (y != j):
                if 0 <= x < n and 0 <= y < m:
                    p = Point(x, y, 1)
                    dist = point.distance(p)
                    if dist <= Tx:
                        p = contains_point(p_list, p)
                        if p != -1:
                            tag_list.append(p)
    return tag_list


# ********************************************************************************
# Update the value of c for each point covered by the new added tag by adding +1
def mark_point_used(myList, tag):
    for p in myList:
        if p.equal(tag) == 0:
            p.flag = 0


def increase_c(myList, i, j):
    temp = Point(i, j, 1)
    for p in myList:
        if p.equal(temp) == 0:
            p.nbr_tag += 1


def update_c(myList, i, j, Tx, n, m):
    tag = Point(i, j, 0)
    mark_point_used(myList, tag)
    Tx = int(Tx)
    for x in range(i - Tx, i + Tx + 1):
        for y in range(j - Tx, j + Tx + 1):
            if 0 <= x < n and 0 <= y < m:
                p = Point(x, y, 1)
                dist = tag.distance(p)
                if dist <= Tx:
                    increase_c(myList, x, y)
    return myList


# ********************************************************************************
# Update the value of c for each point covered by the new added tag by adding -1
def unmark_point_used(myList, tag):
    for p in myList:
        if p.equal(tag) == 0:
            p.flag = 1
            p.id = 0


def decrease_c(myList, x, y):
    temp = Point(x, y, 1)
    for p in myList:
        if p.equal(temp) == 0:
            p.nbr_tag -= 1


def reverse_c(myList, i, j, Tx, n, m):
    tag = Point(i, j, 1)
    unmark_point_used(myList, tag)
    Tx = int(Tx)
    for x in range(i - Tx, i + Tx + 1):
        for y in range(j - Tx, j + Tx + 1):
            if 0 <= x < n and 0 <= y < m:
                p = Point(x, y, 1)
                dist = tag.distance(p)
                if dist <= Tx:
                    decrease_c(myList, x, y)
    return myList


# ********************************************************************************
# a : tag1
# b : tag2
# c : tag3
# d : possible location of the device based on the signal strengh received
def compute_matrix(a, b, c, d):
    err = relative_error()
    a_d = d.distance(a)
    b_d = d.distance(b)
    c_d = d.distance(c)

    try:
        m1 = np.matrix([[2 * (a.x - c.x), 2 * (a.y - c.y)],
                        [2 * (b.x - c.x), 2 * (b.y - c.y)]])

        m1_i = np.linalg.inv(m1)

        p1 = (a.x * a.x) - (c.x * c.x) + (a.y * a.y) - (c.y * c.y) + (c_d * c_d) - (a_d * a_d)
        p2 = (b.x * b.x) - (c.x * c.x) + (b.y * b.y) - (c.y * c.y) + (c_d * c_d) - (b_d * b_d)

        m2 = np.matrix([[p1],
                        [p2]])
        result = m1_i.dot(m2)
    except Exception as e:
        return Point(-1, -1, 0)

    return Point(result[0], result[1], 1)


# ********************************************************************************
# a is tag1
# b is tag2
# d possible location of the device based on the signal strengh received
# solve a system of quadratic equation using fsolve from python spicy pckg
def equation_solver_2(a, b, d):
    err = relative_error()
    a_d = d.distance(a)
    b_d = d.distance(b)

    x, y = symbols('x, y', real=True)
    f1 = pow((x - a.x), 2) + pow((y - a.y), 2) - pow(a_d, 2)
    f2 = pow((x - b.x), 2) + pow((y - b.y), 2) - pow(b_d, 2)

    try:
        result = nonlinsolve([f1, f2], [x, y])
    except Exception as e:
        return Point(-1, -1, 0)

    return result


# ********************************************************************************
def main():
    n, m = 10, 10
    a = Point(6, 10, 0)
    b = Point(49, 10, 0)
    c = Point(5, 10, 0)
    d = Point(10, 7, 1)

    result = compute_matrix(a, b, c, d)
    result.display()
    # grid_location_status = [[0] * n for i in range(m)]
    # list = find_tag(3, 3, grid_location_status, 2, n, m)
    #
    # for elem in list:
    #     elem.display()

    # result = equation_solver_2(a, b, d)
    # print(result)
    # for elem in result:
    #     x1 = complex(elem[0])
    #     x2 = complex(elem[1])
    #     print(x1.real, x2.real)

    # temp_list = list()
    # for i in range(n):
    #     for j in range(m):
    #         temp_list.append(Point(i, j, 1))
    #
    # update_c(temp_list, 3,3, 1.5, n, m)


# this is the standard boilerplate that calls the main() function
if __name__ == '__main__':
    # sys.exit(main(sys.argv)) # used to give a better look to exists
    main()
