from .aws_utils import get_aws_client
from .twinmaker_utils import convert_data_type
import carb.events

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

class TwinMaker:
    def __init__(self, region, assume_role_arn, workspace_id):
        self._tm_client = get_aws_client('iottwinmaker', region, assume_role_arn)
        self._workspace_id = workspace_id

    def get_property_value_type(self, data_binding):
        entity_result = self._tm_client.get_entity(
            workspaceId=self._workspace_id,
            entityId=data_binding.entity_id
        )
        property_type = entity_result['components'][data_binding.component_name]['properties'][data_binding.property_name]['definition']['dataType']['type']
        return convert_data_type(property_type)

    def get_latest_property_value(self, data_binding, data_type, start_time, end_time):
        result = self._tm_client.get_property_value_history(
            workspaceId=self._workspace_id,
            entityId=data_binding.entity_id,
            componentName=data_binding.component_name,
            selectedProperties=[data_binding.property_name],
            orderByTime='DESCENDING',
            startTime=start_time,
            endTime=end_time
        )
        values = result['propertyValues']
        value = None
        if len(values) > 0 and len(values[0]['values']) > 0:
            value = values[0]['values'][0]['value'][data_type]
            print_value = f'Entity/component/property: {data_binding.entity_id}/{data_binding.component_name}/{data_binding.property_name} Time: {end_time} Property value: {value}'
            carb.log_info(print_value)
        
        return value
