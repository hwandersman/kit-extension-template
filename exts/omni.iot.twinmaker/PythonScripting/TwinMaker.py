from .aws_utils import getAWSClient
from .twinmaker_utils import convertDataType, applyOperator

class DataBinding:
    def __init__(self, entityId, componentName, propertyName):
        self._entityId = entityId
        self._componentName = componentName
        self._propertyName = propertyName

    @property
    def entityId(self):
        return self._entityId
    
    @property
    def componentName(self):
        return self._componentName
    
    @property
    def propertyName(self):
        return self._propertyName
    
class RuleExpression:
    def __init__(self, ruleProp, ruleOp, ruleVal):
        self._ruleProp = ruleProp
        self._ruleOp = ruleOp
        self._ruleVal = ruleVal

    @property
    def ruleProp(self):
        return self._ruleProp
    
    @property
    def ruleOp(self):
        return self._ruleOp
    
    @property
    def ruleVal(self):
        return self._ruleVal

class TwinMaker:
    def __init__(self, region, assumeRoleARN, workspaceId):
        self._tmClient = getAWSClient('iottwinmaker', region, assumeRoleARN)
        self._workspaceId = workspaceId

    def getPropertyValueType(self, dataBinding):
        entityResult = self._tmClient.get_entity(
            workspaceId=self._workspaceId,
            entityId=dataBinding.entityId
        )
        type = entityResult['components'][dataBinding.componentName]['properties'][dataBinding.propertyName]['definition']['dataType']['type']
        return convertDataType(type)

    def getLatestPropertyValue(self, dataBinding, dataType, startTime, endTime):
        result = self._tmClient.get_property_value_history(
            workspaceId=self._workspaceId,
            entityId=dataBinding.entityId,
            componentName=dataBinding.componentName,
            selectedProperties=[dataBinding.propertyName],
            orderByTime='DESCENDING',
            startTime=startTime,
            endTime=endTime
        )
        values = result['propertyValues']
        value = None
        if len(values) > 0 and len(values[0]['values']) > 0:
            value = values[0]['values'][0]['value'][dataType]
            print('Property value: ', value)
        
        return value

    def matchRule(self, dataBinding, dataType, startTime, endTime, ruleExpression):
        isRuleMatched = False
        if (ruleExpression.ruleProp == dataBinding.propertyName):
            value = self.getLatestPropertyValue(dataBinding, dataType, startTime, endTime)
            if value != None:
                isRuleMatched = applyOperator(value, ruleExpression.ruleOp, ruleExpression.ruleVal)
        return isRuleMatched