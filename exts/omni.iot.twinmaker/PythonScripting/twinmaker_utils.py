def date_to_iso(time):
    return f'{time.isoformat()}Z'

def convert_data_type(property_type):
    if property_type == 'STRING':
        return 'stringValue'
    elif property_type == 'DOUBLE':
        return 'doubleValue'
    elif property_type == 'BOOLEAN':
        return 'booleanValue'
    elif property_type == 'INTEGER':
        return 'integerValue'
    elif property_type == 'LONG':
        return 'longValue'
    else:
        raise Exception('Unsupported data type')

def apply_operator(left, op, right):
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