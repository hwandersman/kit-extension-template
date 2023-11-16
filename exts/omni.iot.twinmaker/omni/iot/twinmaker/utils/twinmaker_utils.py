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

def evaluate_rule(rule_expression_list, property_value):
    if property_value is not None:
        i = 0
        for rule in rule_expression_list:
            is_rule_matched = apply_operator(property_value, rule.rule_op, rule.rule_val)
            if is_rule_matched:
                return i
            i += 1
    
    return -1
