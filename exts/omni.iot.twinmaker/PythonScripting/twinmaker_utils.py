def date_to_iso(time):
    return f'{time.isoformat()}Z'

def convertDataType(type):
    if type == 'STRING':
        return 'stringValue'
    elif type == 'DOUBLE':
        return 'doubleValue'
    elif type == 'BOOLEAN':
        return 'booleanValue'
    elif type == 'INTEGER':
        return 'integerValue'
    elif type == 'LONG':
        return 'longValue'
    else:
        raise Exception('Unsupported data type')

def applyOperator(left, op, right):
    if op == '==':
        return left == right
    elif op == '>':
        return left > right
    elif op == '<':
        return left < right
    elif op == '>=':
        return left >= right
    elif op == '<=':
        return left <= right
    else:
        raise Exception('Unsupported rule operator')