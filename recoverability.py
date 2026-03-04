from conflict import *
def read_dependencies(schedule):
    read_from = []
    write_after = []
    last_write = {}
    commit_index = {}
    finish_index = {}
    
    for i, op in enumerate(schedule):
        if op.type in ['w' , 'i', 'd']:
            if op.variable in last_write:
                if last_write[op.variable] != op.transaction:
                    prev_writer = last_write[op.variable]
                    write_after.append((op.transaction, prev_writer, op.variable, i))
            last_write[op.variable] = op.transaction
            
        elif op.type == 'r':
            if op.variable in last_write:
                if last_write[op.variable] != op.transaction:
                    writer = last_write[op.variable]
                    read_from.append((op.transaction, writer, op.variable, i))

        elif op.type == 'c':
            commit_index[op.transaction] = i
            finish_index[op.transaction] = i
        elif op.type == 'a':
            finish_index[op.transaction] = i
        
    return read_from, write_after, commit_index ,finish_index

def is_recoverable(read_from, commit_index):
    for reader, writer, var, read_i in read_from:
            if writer not in commit_index:
                return False, f"{reader} commits but {writer} never commits (read {var})"
            if commit_index[reader] < commit_index[writer]:
                return False, f"{reader} commits before {writer} (read {var})"
    return True, "All commit orders valid"

def is_aca(read_from, commit_index):
    for reader, writer, var, read_i in read_from:
        if writer not in commit_index:
            return False, f"{reader} reads {var} but {writer} never commits"
        if commit_index[writer] > read_i:
            return False, f"{reader} reads {var} before {writer} commits"

    return True, "All reads are from committed transactions"

def is_strict(write_after , finish_index):
    for writer, prev_writer, var, write_i in write_after:
        if prev_writer not in finish_index:
            return False, f"{writer} writes {var} but previous writer {prev_writer} never finishes"
        if finish_index[prev_writer] > write_i:
            return False, f"{writer} writes {var} before previous writer {prev_writer} finishes"

    return True, "All writes are after previous writers have finished"

def is_strict(read_from, write_after, finish_index):
    for writer, prev_writer, var, write_i in write_after:
        if prev_writer not in finish_index:
            return False, f"{writer} writes {var} but previous writer {prev_writer} never finishes"
        if finish_index[prev_writer] > write_i:
            return False, f"{writer} writes {var} before previous writer {prev_writer} finishes (commit/abort)"
 
    for reader, writer, var, read_i in read_from:
        if writer not in finish_index:
            return False, f"{reader} reads {var} but writer {writer} never finishes"
        if finish_index[writer] > read_i:
            return False, f"{reader} reads {var} before writer {writer} finishes (commit/abort)"

    return True, "All reads and writes respect strict schedule rules"
s , t = parse_schedule("operations.txt")
pg = precedence_graph(s)
print("Precedence Graph:")
for node, neighbors in pg.items():
    print(f"{node} -> {', '.join(str(n) for n in neighbors)}")
print(has_cycle(pg))
rf , wa , ci , fi = read_dependencies(s)
print("Read-From Relationships:")
for reader, writer, variable, index in rf:
    print(f"Transaction {reader} reads variable {variable} from Transaction {writer} at operation index {index}")
print("Commit Indices:")
for transaction, index in ci.items():   print(f"Transaction {transaction} commits at operation index {index}")  
print("\nRecoverability Check:")
recoverable, message = is_recoverable(rf, ci)
print(message)     
print("\nACA Check:")
aca, message = is_aca(rf, ci)
print(message)
print("\nStrict Schedule Check:")
strict, message = is_strict(rf , wa, fi)
print(message)