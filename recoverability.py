from conflict import *
def read_dependencies(schedule):
    read_from = []
    last_write = {}
    commit_index = {}
    for i, op in enumerate(schedule):
        if op.type in ['w' , 'i', 'd']:
            last_write[op.variable] = op.transaction

        elif op.type == 'r':
            if op.variable in last_write:
                writer = last_write[op.variable]
                read_from.append((op.transaction, writer, op.variable, i))

        elif op.type == 'c':
            commit_index[op.transaction] = i
    return read_from, commit_index

s , t = parse_schedule("operations.txt")
pg = precedence_graph(s)
print("Precedence Graph:")
for node, neighbors in pg.items():
    print(f"{node} -> {', '.join(str(n) for n in neighbors)}")
print(has_cycle(pg))
rf , ci = read_dependencies(s)
print("Read-From Relationships:")
for reader, writer, variable, index in rf:
    print(f"Transaction {reader} reads variable {variable} from Transaction {writer} at operation index {index}")
print("Commit Indices:")
for transaction, index in ci.items():   print(f"Transaction {transaction} commits at operation index {index}")  