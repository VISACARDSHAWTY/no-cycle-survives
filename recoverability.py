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

def analyze_schedule(content: str) -> dict:
    parse_result = parse_schedule_from_text(content)
    if parse_result[0] is None:
        return {"error": parse_result[2]}

    schedule, transactions, _ = parse_result

    pg = precedence_graph(schedule)
    has_cyc = has_cycle(pg)

    rf, wa, aa, ci, fi = read_dependencies(schedule)
    serial_result = {
        "title": "Serializability (Conflict Serializability)",
        "graph": "\n".join(f"T{node} → {', '.join(f'T{n}' for n in neighbors)}"
                           for node, neighbors in sorted(pg.items())),
        "cycle": "Has cycle: YES (not conflict serializable)" if has_cyc else "Has cycle: NO ✓ (conflict serializable)",
        "status": "fail" if has_cyc else "pass"
    }
    rec_ok, rec_msg = is_recoverable(rf, ci)
    recoverable_result = {
        "title": "Recoverability",
        "status": "pass" if rec_ok else "fail",
        "message": rec_msg
    }
    aca_ok, aca_msg = is_aca(rf, ci)
    aca_result = {
        "title": "ACA (Avoid Cascading Aborts)",
        "status": "pass" if aca_ok else "fail",
        "message": aca_msg
    }
    strict_ok, strict_msg = is_strict(rf, wa, fi)
    strict_result = {
        "title": "Strict Schedule",
        "status": "pass" if strict_ok else "fail",
        "message": strict_msg
    }
    rig_ok, rig_msg = is_rigorous(aa, fi)
    rigorous_result = {
        "title": "Rigorous Schedule",
        "status": "pass" if rig_ok else "fail",
        "message": rig_msg
    }
    log_lines = []
    if rf:
        log_lines.append("Read-from dependencies:")
        for r, w, v, idx in rf:
            log_lines.append(f"  T{r} reads {v} from T{w} (op {idx})")
    if wa:
        log_lines.append("\nWrite-after dependencies:")
        for w, pw, v, idx in wa:
            log_lines.append(f"  T{w} writes {v} after T{pw} (op {idx})")
    if aa:
        log_lines.append("\nAccess-after dependencies:")
        for t, pt, v, idx in aa:
            log_lines.append(f"  T{t} accesses {v} after T{pt} (op {idx})")

    console_log = "\n".join(log_lines) if log_lines else "No dependency relationships detected."

    return {
        "error": None,
        "serializability": serial_result,
        "recoverability": recoverable_result,
        "aca": aca_result,
        "strict": strict_result,
        "rigorous": rigorous_result,
        "console": console_log,
        "read_from": rf,
        "write_after": wa,
        "access_after": aa,
        "commit_indices": ci,
        "precedence_graph": pg,
    }


if __name__ == "__main__":
    try:
        with open("operations.txt", "r", encoding="utf-8") as f:
            content = f.read()
        print(analyze_schedule(content))
    except FileNotFoundError:
        print("operations.txt not found - GUI will still work with any .txt file")

