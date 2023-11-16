from omni.iot.twinmaker.utils.aws_utils import get_aws_client
from omni.iot.twinmaker.utils.twinmaker_utils import convert_data_type
from omni.iot.twinmaker.data_models import DataPoint

class TwinMaker:

    def __init__(self, region, assume_role_arn, workspace_id):
        self._tm_client = get_aws_client('iottwinmaker', region, assume_role_arn)
        self._workspace_id = workspace_id

    def get_property_value_type(self, data_binding):
        entity_result = self._tm_client.get_entity(
            workspaceId=self._workspace_id,
            entityId=data_binding.entity_id
        )
        
        property_type = entity_result['components'][data_binding.component_name]['properties'][data_binding.property_name]\
            ['definition']['dataType']['type']
        
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
            if  data_type != 'stringValue':
                value = float(value)
        
        # TODO: should use the actual data point timestamp
        return DataPoint(end_time, value)
