class DataPoint:
    def __init__(self, timestamp, value) -> None:
        self.timestamp = timestamp
        self.value = value
    
    def __repr__(self) -> str:
        return f'DataPoint([{self.timestamp}]: {self.value})'


class DataBinding:
    def __init__(self, entity_id, component_name, property_name):
        self._entity_id = entity_id
        self._component_name = component_name
        self._property_name = property_name

    @property
    def entity_id(self):
        return self._entity_id
    
    @property
    def component_name(self):
        return self._component_name
    
    @property
    def property_name(self):
        return self._property_name
    
    def __repr__(self):
        return f"DataBinding({self._entity_id}, {self._component_name}, {self._property_name})"

    def __eq__(self, other):
        return self.__repr__() == other.__repr__()
    
    def __hash__(self) -> int:
        return hash(self.__repr__())

    
class RuleExpression:
    def __init__(self, rule_prop, rule_op, rule_val):
        self._rule_prop = rule_prop
        self._rule_op = rule_op
        self._rule_val = rule_val

    @property
    def rule_prop(self):
        return self._rule_prop
    
    @property
    def rule_op(self):
        return self._rule_op
    
    @property
    def rule_val(self):
        return self._rule_val
    
    def __repr__(self):
        return f"RuleExpression({self._rule_prop}, {self._rule_op}, {self._rule_val})"

    def __eq__(self, other):
        return self.__repr__() == other.__repr__()
    
    def __hash__(self) -> int:
        return hash(self.__repr__())

