from conflict import *
from parser import parse_schedule_from_text
from visualization import visualize_precedence_graph
def read_dependencies(schedule):
    read_from = []
    write_after = []
    access_after = []
    
    last_write = {}
    last_access = {}
    write_history = {} 
    commit_index = {}
    finish_index = {}
    aborted = set()
    
    for i, op in enumerate(schedule):
        if op.type in ['r', 'w', 'i', 'd']:
            if op.variable in last_access:
                prev_tx = last_access[op.variable]
                if prev_tx != op.transaction:
                    access_after.append((op.transaction, prev_tx, op.variable, i))
            last_access[op.variable] = op.transaction

        if op.type in ['w', 'i', 'd']:
            if op.variable not in write_history:
                write_history[op.variable] = []

            if op.variable in last_write:
                prev_writer = last_write[op.variable]
                if prev_writer != op.transaction and prev_writer != None:
                    write_after.append((op.transaction, prev_writer, op.variable, i))
                    print((op.transaction, prev_writer, op.variable, i))

            write_history[op.variable].append(op.transaction)
            last_write[op.variable] = op.transaction

        elif op.type == 'r':
            if op.variable in last_write:
                writer = last_write[op.variable]
                if writer != op.transaction and writer != None:
                    read_from.append((op.transaction, writer, op.variable, i))

        elif op.type == 'c':
            commit_index[op.transaction] = i
            finish_index[op.transaction] = i

        elif op.type == 'a':
            finish_index[op.transaction] = i
            aborted.add(op.transaction)

            for var, history in write_history.items():
                if history and history[-1] == op.transaction:
                    while history and history[-1] in aborted:
                        history.pop()
                    last_write[var] = history[-1] if history else None

    return read_from, write_after, access_after, commit_index, finish_index

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

def is_rigorous(access_after, finish_index):

    for tx, prev_tx, var, op_i in access_after:
        if prev_tx not in finish_index:
            return False, f"{tx} accesses {var} but previous access by {prev_tx} never finishes"

        if finish_index[prev_tx] > op_i:
            return False, f"{tx} accesses {var} before {prev_tx} finishes (commit/abort)"

    return True, "All accesses occur after previous transactions finish"

def perform_analysis(content: str) -> str:
    parse_result = parse_schedule_from_text(content)
    if parse_result[0] is None:
        return parse_result[2]  # error message

    schedule, transactions, _ = parse_result

    result = []

    pg = precedence_graph(schedule)
    result.append("Precedence Graph:")
    for node, neighbors in pg.items():
        result.append(f"{node} -> {', '.join(str(n) for n in neighbors)}")
    result.append(f"Has Cycle: {has_cycle(pg)}")

    rf , wa , aa , ci , fi = read_dependencies(schedule)
    result.append("Read-From Relationships:")
    for reader, writer, variable, index in rf:
        result.append(f"Transaction {reader} reads variable {variable} from Transaction {writer} at operation index {index}")
    result.append("Commit Indices:")
    for transaction, index in ci.items():   
        result.append(f"Transaction {transaction} commits at operation index {index}")  

    result.append("\nRecoverability Check:")
    recoverable, message = is_recoverable(rf, ci)
    result.append(message)     

    result.append("\nACA Check:")
    aca, message = is_aca(rf, ci)
    result.append(message)

    result.append("\nStrict Schedule Check:")
    strict, message = is_strict(rf , wa, fi)
    result.append(message)

    result.append("\nRigorous Schedule Check:")
    rigorous, message = is_rigorous(aa, fi) 
    result.append(message)

    return "\n".join(result)


if __name__ == "__main__":
    try:
        with open("operations.txt", "r", encoding="utf-8") as f:
            content = f.read()
        print(perform_analysis(content))
    except FileNotFoundError:
        print("operations.txt not found - GUI will still work with any .txt file")

