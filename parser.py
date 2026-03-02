import sys

class Operation:
    def __init__(self , type , transaction , variable):
        self.type = type
        self.transaction = transaction
        if type != 's' or type != 'c' or type != 'a':
            self.variable = variable
        else:
            self.variable = None
    
    def __str__(self):
        if self.variable:
            return f"{self.type}({self.transaction}, {self.variable})"
        else:
            return f"{self.type}({self.transaction})"
    
    def __repr__(self):
        return self.__str__()


def parse_operations(file_path):
    operations = []
    op_map = {
        "START": 's',
        "READ": 'r',
        "WRITE": 'w',
        "INCREMENT": 'i',
        "DECREMENT": 'd',
        "COMMIT": 'c',
        "ABORT": 'a'
    }

    with open(file_path, 'r') as file:
        started = set()
        done = set()
        for line in file:
            line = line.strip()
            if not line:
                continue

            matched = False
            for op_name, op_code in op_map.items():
                if line.startswith(f"{op_name}(") and line.endswith(")"):
                    content = line[len(op_name)+1:-1].split(',')
                    try:
                        transaction = int(content[0].strip())
                        variable = content[1].strip() if len(content) > 1 else None
                        if op_code == 's':
                            if transaction in started:
                                print(f"ERROR! Transaction {transaction} already started: {line}")
                                return -1
                            elif transaction in done:
                                print(f"ERROR! Transaction {transaction} already completed: {line}")
                                return -1
                            started.add(transaction)
                        else:
                            if transaction in done:
                                print(f"ERROR! Transaction {transaction} already completed: {line}")
                                return -1
                            if transaction not in started:
                                print(f"ERROR! Transaction {transaction} has not been started: {line}")
                                return -1
                            if op_code in ['c', 'a']:
                                done.add(transaction)
                                started.discard(transaction)
                        operations.append(Operation(op_code, transaction, variable))
                        matched = True
                    except (ValueError, IndexError):
                        print(f"ERROR! Invalid {op_name} operation format: {line}")
                        return -1
                    break
            if not matched:
                print(f"ERROR! Unrecognized operation format: {line}")
                return -1
    if started:
        print(f"ERROR! Transactions not completed: {', '.join(map(str, started))}")
        return -1
    return operations

parsed_operations = parse_operations('operations.txt')
print("Parsed Operations:")
print(parsed_operations)

