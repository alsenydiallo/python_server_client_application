from __future__ import print_function
from equation_solver import *
import time
import heapq
import random
import datetime
import sys
import copy


debug = 1
n, m = 0, 0  # grid size
Tx = 0
id = 1  # id for each added tag on the grid
k = 0  # number of tag to be allocated
total_coverage = 0.0  # var holder for the total coverage score of the gride
score_table = set()  # contains precomputed score values
input_filename = ""
output_filename = ""

# ********************************************************************************
# takes a list of points and returns a 2D array [][]
def convert_list_to_grid(p_list):
    grid = [[1] * n for i in range(m)]
    for elem in p_list:
        grid[elem.x][elem.y] = elem.flag
    return grid


# ********************************************************************************
# takes an 2D array [][] and returns a list of points
def convert_grid_to_list(grid, Tx):
    p_list = list()
    id = 0
    for x in range(n):
        for y in range(m):
            p_list.append(Point(x, y, grid[x][y]))

    for p in p_list:
        if p.flag == 0:
            update_c(p_list, p.x, p.y, Tx, n, m)

    for p in p_list:
        if p.flag == 0:
            update_score(p_list, p.x, p.y, Tx)

    return p_list


# ********************************************************************************
# Display the given list
def print_list(myList):
    for p in myList:
        p.display()


# ********************************************************************************
# creates a list containing all coordinate of the grid
def create_list_of_points():
    temp_list = list()
    for x in range(n):
        for y in range(m):
            temp_list.append(Point(x, y, 1))
    return temp_list


# ********************************************************************************
# point possible location of the device based on the signal strengh received
# if device is in a presence of one tag, the location of the device is the tag location
def score_func_case_1(point, tag_list, Tx):
    tag1 = tag_list[0]
    d = point.distance(tag1)
    score = (1 - d / Tx) * 0.9
    return max(score, 0.02)


# ********************************************************************************
# find midpoint coordinate of tag1, tag2 from point source_p
def score_func_case_2_helper(source_p, tag1, tag2, Tx):
    result_list = list()
    new_coords = equation_solver_2(tag1, tag2, source_p)
    if new_coords.__class__ == Point:
        mid_point = midpoint(tag1, tag2)
    else:
        for elem in new_coords:
            x1 = complex(elem[0])
            x2 = complex(elem[1])
            result_list.append(Point(x1.real, x2.real, 0))
        if len(result_list) == 1:
            mid_point = midpoint(result_list[0], result_list[0])
        elif len(result_list) > 1:
            mid_point = midpoint(result_list[0], result_list[1])
        else:
            mid_point = midpoint(tag1, tag2)

    return mid_point


# compute the score for a device that had only receive Tx from 2 tags
# alpha is the max tx range
# d the distance between the device and the tags
# 0.02 is the minimum socre attributed
def score_func_case_2(source_p, tag_list, Tx):
    tag1, tag2 = tag_list[0], tag_list[1]
    mid_point = score_func_case_2_helper(source_p, tag1, tag2, Tx)
    d = source_p.distance(mid_point)
    score = (1 - d / Tx) * 0.9
    return max(score, 0.02)


# ********************************************************************************
# if a device has received more Tx from 3 or more tag. set score to 1 always
def score_func_case_3(point, tag_list, Tx):
    return 1.0


# ********************************************************************************
# first find the number of neighbors tag
# if (1) only one present tag
# if (2) compute score case 2
# if 3 or more, compute score using case 3
def compute_score(point, p_list, Tx):
    score = 0.0
    tag_list = find_tag(point, p_list, Tx, n, m)
    list_len = len(tag_list)

    if list_len == 1:
        score = score_func_case_1(point, tag_list, Tx)
    elif list_len == 2:
        tag1, tag2 = tag_list[0], tag_list[1]
        dist = tag1.distance(tag2)
        look_up_score = score_lookup(dist, score_table)
        if look_up_score == -1:
            score = score_func_case_2(point, tag_list, Tx)
        elif look_up_score > 0:
            score = look_up_score
    elif list_len >= 3:
        score = score_func_case_3(point, tag_list, Tx)

    return score


# ********************************************************************************
# Helper function to calculate coverage for a given Point
def coverage_score(point, p_list, Tx):
    result = compute_score(point, p_list, Tx)
    return result


# Helper function to calculate total coverage for a given grid
def sum_coverage_score(current_list, Tx):
    result = 0.0
    for point in current_list:
        result += point.score

    return result


# ********************************************************************************
def update_score(p_list, i, j, Tx):
    total_diff_score = 0.0
    Tx = int(Tx)
    for x in range(i - Tx, i + Tx + 1):
        for y in range(j - Tx, j + Tx + 1):
            if x >= 0 and x < n and y >= 0 and y < m:
                p = Point(x, y, 1)
                score = coverage_score(p, p_list, Tx)
                total_diff_score += assign_score(p, p_list, score)
    return total_diff_score


# ********************************************************************************
def assign_score(point, p_list, score):
    diff_score = 0.0
    for p in p_list:
        if p.equal(point) == 0:
            diff_score = abs(score - p.score)
            p.score = score
            return diff_score
    return diff_score


# ********************************************************************************
def set_id(p_list, x, y):
    global id
    point = Point(x, y, 1)
    for p in p_list:
        if p.equal(point) == 0:
            p.id = id
    id += 1


# ********************************************************************************
# return -1 if it doesn't have the element
# other return the score if element exists
def return_point_id(p_list, point):
    for p in p_list:
        if p.equal(point) == 0:
            return p.id
    return 0


# ********************************************************************************
# return -1 if it doesn't have the element
# other return the score if element exists
def score_lookup(dist, set_elt):
    if len(set_elt) == 0: return -1
    for elt in set_elt:
        d, s = elt
        if d == dist:
            return s
    return -1


# ********************************************************************************
# display the statistic information of the grid
# takes as an input a list of point
def grid_stat(list, Tx):
    mydict = dict()
    for elem in list:
        key = elem.nbr_tag
        mydict[key] = mydict.get(key, 0) + 1

    max_cov_poss = n * m
    max_cov_perc = (total_coverage * 100) / max_cov_poss

    print("\n    Grid statistic")
    print("\n*******************************")
    print("Gride size = %dx%d \tTx = %d\n" % (n, m, Tx))
    print("Max Coverage Possible: %f" % max_cov_poss)
    print("Grid Total Coverage: %.5f" % total_coverage)
    print("Grid Coverage Percentage:  %.3f" % max_cov_perc)
    print("\nCoverage break down:")
    for key, value in mydict.items():
        print("(%d): %d" % (key, value))


# ********************************************************************************

def allocate_tag(nbr_tag, Tx):
    global debug
    global total_coverage
    temp_total_c = 0.0
    p_list = create_list_of_points()
    current_list = list()
    current_list_score = 0
    best_list = list()
    best_list_score = 0

    # Array to keep track of which point have already been used, default value is 1
    grid_location_status = [[1] * n for i in range(m)]
    # print_grid(grid_location_status)

    # Beginning of the loop for algorithm
    for tag in range(0, nbr_tag):
        temp_x = -1
        temp_y = -1
        for x in range(0, n):
            for y in range(0, m):
                current_list = copy.deepcopy(p_list)  # need to reset the list to the original state
                # if state of the point is not used
                if grid_location_status[x][y] == 1:
                    # add the new tantative point and calculate new score
                    current_list = update_c(current_list, x, y, Tx, n, m)
                    diff = update_score(current_list, x, y, Tx)
                    current_list_score = total_coverage + diff

                    if current_list_score > best_list_score:
                        best_list_score = current_list_score
                        best_list = copy.deepcopy(current_list)
                        temp_x = x
                        temp_y = y
                        # if(debug == 1): print("new best score: %.5f\n" %best_list_score)
                        temp_total_c = diff
                    else:
                        current_list = reverse_c(current_list, x, y, Tx, n, m)
                        diff = update_score(current_list, x, y, Tx)

        # mark off the location where the new tag was added, so that it will not be used again
        total_coverage += temp_total_c
        grid_location_status[temp_x][temp_y] = 0
        set_id(best_list, temp_x, temp_y)
        p_list = copy.deepcopy(best_list)
        if debug == 1: print("total_coverage score %f" % total_coverage)
        if debug == 1: print_grid_2(grid_location_status, p_list)

    write_grid_to_file(output_filename, grid_location_status, p_list, Tx)
    return grid_location_status, p_list


# ********************************************************************************
# reads in tag location from file and returns a 2D array grid
def read_grid_from_file(filepath):
    global n, m
    global Tx
    global total_coverage
    global k
    p_list = list()
    f = open(filepath, "r")
    contents = f.readlines()

    header = contents[0]
    arg = header.split()
    n, m, k, Tx = int(arg[0]), int(arg[1]), int(arg[2]), int(arg[3])
    grid_location_status = [[1] * n for i in range(m)]

    precompute_score(Tx)

    for i in range(1, len(contents)):
        line = contents[i]
        tag_info = line.split()
        x, y, flag, id = int(tag_info[0]), int(tag_info[1]), int(tag_info[2]), int(tag_info[3])
        grid_location_status[x][y] = flag
        p = Point(x, y, flag)
        p.id = id
        p_list.append(p)

    # for i in range(1, k):
    #     for p in p_list:
    #         if(p.id == i):
    #             p_list = update_c(p_list, p.x, p.y, Tx, n, m)
    #             diff = update_score(p_list, p.x, p.y, Tx)
    #             total_coverage += diff

    for p in p_list:
        if p.flag == 0:
            p_list = update_c(p_list, p.x, p.y, Tx, n, m)
            diff = update_score(p_list, p.x, p.y, Tx)
            total_coverage += diff
    f.close()

    return grid_location_status, p_list


# ********************************************************************************
# writes tag allocation grid on to profided filepath
def write_grid_to_file(filepath, grid_location_status, p_list, Tx):
    f = open(filepath, "w+")
    f.write("%d %d %d %d\n" % (n, m, k, Tx))
    for x in range(n):
        for y in range(m):
            point = Point(x, y, 1)
            f.write("%d %d %d %d\n" % (x, y, grid_location_status[x][y], return_point_id(p_list, point)))
    f.close()


# ********************************************************************************
# this version of print grid works for a 2D array arr[][]
# out put looks like
# .  0  .  .  .
# .  .  0  .  .
# .  .  .  0  .
# .  .  .  .  0
def print_grid(grid):
    delim = '.'
    print("\nGrid state")
    print("----------")
    for x in range(n):
        print()
        for y in range(m):
            if grid[x][y] == 0:
                # print('0', sep=' ')
                sys.stdout.write('%2d ' % (grid[x][y]))
            else:
                # print('.', sep=' ')
                sys.stdout.write('%2s ' % (delim))
    print()


# this version of print grid works for a a list of points
# This version also allowed to print tag ID, which denote order
# in which the tags were allocated on the grid
# out put looks like
# .  1  .  .  .
# .  .  2  .  .
# .  .  .  3  .
# .  .  .  .  5
def print_grid_2(grid, p_list):
    delim = '.'
    print("\nGrid state")
    print("----------")
    for x in range(n):
        print()
        for y in range(m):
            if grid[x][y] == 0:
                p = Point(x, y, 1)
                sys.stdout.write('%2d ' % (return_point_id(p_list, p)))
            else:
                sys.stdout.write('%2s ' %delim)
    print()


# ********************************************************************************
# This function precompute the score value for some repeating special cases
# and stores the precomputed data onto a file
def precompute_score(Tx):
    i = int(n / 2)
    j = int(m / 2)
    origin = Point(i, j, 1)
    p_list = create_list_of_points()

    for p in p_list:
        if p.x == i and p.y == j:
            update_c(p_list, p.x, p.y, Tx, n, m)

    interested_list_p = list()
    for x in range(i - Tx, i + Tx + 1):
        for y in range(j - Tx, j + Tx + 1):
            if (x != i) or (y != j):
                if 0 <= x < n and 0 <= y < m:
                    p1 = Point(x, y, 1)
                    dist = p1.distance(origin)
                    if dist <= Tx:
                        interested_list_p.append(p1)

    precomputed_score_list = set()
    for p1 in interested_list_p:
        for p2 in interested_list_p:
            if p1.equal(p2) == -1:
                if p1.distance(origin) <= Tx and p2.distance(origin) <= Tx:
                    dist = p1.distance(p2)
                    if score_lookup(dist, precomputed_score_list) == -1:
                        score = score_func_case_2(origin, (p1, p2), Tx)
                        myTuple = dist, score
                        precomputed_score_list.add(myTuple)

    f = open("score_table.txt", "w+")
    for p in precomputed_score_list:
        d, s = p
        f.write("%.5f %.5f\n" % (d, s))
    f.close()
    return precomputed_score_list


# ********************************************************************************
# Predict location of device with the given grid layout
# tag_location_list: contains the location of all deployed tag on the gride
# signal_received_at: the location at which the tag reflected signal was read from
def predict_location(tag_location_list, signal_received_at, tx=None, myN=None, myM=None):
    global Tx
    global n
    global m
    location = Point(0, 0, 1)
    error = 0.0
    if tx is None: Tx = getTX()
    else: Tx = tx

    if myN is None: n = myN
    if myM is None: m = myM

    tag_list = find_tag(signal_received_at, tag_location_list, Tx, n, m)
    list_len = len(tag_list)

    if list_len == 1:
        location = tag_list[0]
    elif list_len == 2:
        tag_heap = heap_of_tags(tag_list, signal_received_at)
        k1, tag1 = heapq.heappop(tag_heap)
        k2, tag2 = heapq.heappop(tag_heap)
        # print("case2")
        # tag1.display()
        # tag2.display()
        location = score_func_case_2_helper(signal_received_at, tag1, tag2, Tx)
    elif list_len >= 3:
        tag_heap = heap_of_tags(tag_list, signal_received_at)
        k1, tag1 = heapq.heappop(tag_heap)
        k2, tag2 = heapq.heappop(tag_heap)
        k3, tag3 = heapq.heappop(tag_heap)
        # print("case3")
        # tag1.display()
        # tag2.display()
        # tag3.display()
        location = compute_matrix(tag1, tag2, tag3, signal_received_at)

    return location


# sort the received signal of tag from device by distance
def heap_of_tags(tag_list, signal_received_at):
    h = []
    i = 1
    for tag in tag_list:
        key = tag.distance(signal_received_at)
        heapq.heappush(h, (key, tag))
        i += 1
    return h


# ********************************************************************************
def suggest_point():
    x = int(random.uniform(0, n))
    y = int(random.uniform(0, m))
    return Point(x, y, 1)


def run_predict_location(tag_location_list, sample_points):
    global input_filename

    if input_filename == "":
        input_filename = output_filename

    points_f_name = input_filename + ".points"
    log_f_name = input_filename + ".log"

    points_f = open(points_f_name, "a+")
    log_f = open(log_f_name, "a+")

    while sample_points > 0:
        sugg_p = suggest_point()
        print("suggested location -> %.1f %.1f" % (sugg_p.y, sugg_p.x))
        device_predicted_loc = predict_location(tag_location_list, sugg_p)
        print("computed location -> %.1f %.1f" % (device_predicted_loc.y, device_predicted_loc.x))

        d = sugg_p.distance(device_predicted_loc)
        points_f.write(
            "%.1f %.1f;%.1f %.1f;%.7f\n" % (sugg_p.y, sugg_p.x, device_predicted_loc.y, device_predicted_loc.x, d))
        if (d > 3):
            print("d > 3 (dist=%.5f) writing to log ..." % d)
            log_f.write(
                "%.1f %.1f;%.1f %.1f;%.7f\n" % (sugg_p.y, sugg_p.x, device_predicted_loc.y, device_predicted_loc.x, d))

        print()
        sample_points -= 1
        time.sleep(1)
    points_f.close()
    points_f.close()

def getTX():
    return Tx
def setTx(tx):
    Tx = tx
# ********************************************************************************
def main():
    global n, m
    global Tx
    global k
    global score_table
    global input_filename, output_filename

    seed = datetime.datetime.now().time()
    random.seed(seed)

    nbr_runs = 200
    Ir = 1
    At = 360
    Ac = 360

    start = time.time()

    if len(sys.argv) == 6:
        print("Allocating tags on grid ...")
        n, m = int(sys.argv[1]), int(sys.argv[2])
        k = int(sys.argv[3])
        Tx = int(sys.argv[4])
        output_filename = sys.argv[5]
        score_table = precompute_score(Tx)
        tag_location_grid, tag_location_list = allocate_tag(k, Tx)
        grid_stat(tag_location_list, Tx)
        print_grid_2(tag_location_grid, tag_location_list)
        # print_list(tag_location_list)
        # run_predict_location(tag_location_list, nbr_runs)
    elif len(sys.argv) == 2:
        print("Reading tags coordinate from file ...")
        input_filename = sys.argv[1]
        tag_location_grid, tag_location_list = read_grid_from_file(input_filename)
        grid_stat(tag_location_list, Tx)
        print_grid_2(tag_location_grid, tag_location_list)
        # print_list(tag_location_list)
        # run_predict_location(tag_location_list, nbr_runs)
    else:
        print("Option 1: >> python coverage_greedy_enhanced.py 20 20 k Tx filename.out [To run allocate tag algorithm]")
        print("Option 2: >> python coverage_greedy_enhanced.py filename.in  [To read allocated tag from a file]")

    end = time.time()
    print("\nTime elapsed: %.5f" % (end - start))


# this is the standard boilerplate that calls the main() function
if __name__ == '__main__':
    # sys.exit(main(sys.argv)) # used to give a better look to exists
    main()
