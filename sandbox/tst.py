import itertools

ll = [1,2,3,4,5,6,7,8,9]

def fun(len, num):
    res = [x for x in list(itertools.combinations([1,2,3,4,5,6,7,8,9],len)) if sum(x) == num]

    return res

print(fun(5, 25))
