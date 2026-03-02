from parser import *
def precedence_graph(schedule):
    graph = {}
    i = 0
    for op in schedule:
        print(f"{i}: Processing operation: {op}")
        if op.type in ['s', 'c', 'a']:
            i = i + 1
            continue
        if op.transaction not in graph:
            graph[op.transaction] = set()
        for other_op in schedule[i+1:]:
            if other_op.type in ['s', 'c', 'a']:
                continue
            if other_op.transaction != op.transaction and other_op.variable == op.variable:
                if (op.type in ['w', 'i' , 'd'] or other_op.type in ['w', 'i', 'd']):
                    graph[op.transaction].add(other_op.transaction)
                    print("Conflict detected between Operation {} and Operation {}".format(op, other_op))
        i = i + 1
    return graph


    