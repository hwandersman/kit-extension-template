import boto3
import omni.usd
import uuid
from datetime import datetime, timedelta
from omni.kit.scripting import BehaviorScript
from pxr import Gf

from omni.iot.twinmaker.Main import get_state, get_executor
from omni.iot.twinmaker.constants import WORKSPACE_ATTR, ASSUME_ROLE_ATTR, ENTITY_ATTR, COMPONENT_ATTR, PROPERTY_ATTR, DEFAULT_ASSUME_ROLE_ARN, REGION_ATTR


def date_to_iso(time):
    return f'{time.isoformat()}Z'


class Clickable(BehaviorScript):
    def on_init(self):
        self.__init_data_binding()

        self._runningTime = 0

        self._tmClient = self.__getAWSClient('iottwinmaker')

        self._defaultColor = self.prim.GetAttribute('primvars:displayColor').Get()
        self._highlightColor = [Gf.Vec3f(1, 0, 0)] # red
        self._isAlarmActive = False
        self._changedHighlight = False

        self.__init_data_binding()

        print(f"{__class__.__name__}.on_init()->{self.prim_path}")

    # Get attributes from prim with property data binding
    def __init_data_binding(self):
        # Get shared attributes from Logic object
        logicPrimPath = '/World/Logic'
        stage = omni.usd.get_context().get_stage()
        logicPrim = stage.GetPrimAtPath(logicPrimPath)
        self._workspaceId = logicPrim.GetAttribute(WORKSPACE_ATTR).Get()
        self._assumeRoleARN = logicPrim.GetAttribute(ASSUME_ROLE_ATTR).Get()
        self._region = logicPrim.GetAttribute(REGION_ATTR)

        # Data binding attributes are on current prim
        self._entityId = self.prim.GetAttribute(ENTITY_ATTR).Get()
        self._componentName = self.prim.GetAttribute(COMPONENT_ATTR).Get()
        self._propertyName = self.prim.GetAttribute(PROPERTY_ATTR).Get()

    # TODO: Duplicate logic moved to shared location
    def __getAWSClient(self, serviceName):
        if self._assumeRoleARN == DEFAULT_ASSUME_ROLE_ARN:
            return boto3.client(serviceName, self._region)

        stsClient = boto3.client('sts')
        response = stsClient.assume_role(
            RoleArn=self._assumeRoleARN,
            RoleSessionName=f'nvidia-ov-session-{uuid.uuid1()}',
            DurationSeconds=1800
        )
        newSession = boto3.Session(
            aws_access_key_id=response['Credentials']['AccessKeyId'],
            aws_secret_access_key=response['Credentials']['SecretAccessKey'],
            aws_session_token=response['Credentials']['SessionToken']
        )
        return newSession.client(serviceName, self._region)

    def setAlarmStatus(self, startTime, endTime):
        result = self._tmClient.get_property_value_history(
            workspaceId=self._workspaceId,
            entityId=self._entityId,
            componentName=self._componentName,
            selectedProperties=[self._propertyName],
            orderByTime='DESCENDING',
            startTime=startTime,
            endTime=endTime
        )
        values = result['propertyValues']
        if len(values) > 0 and len(values[0]['values']) > 0:
            value = values[0]['values'][0]['value']['stringValue']
            print(value)
            if value == 'ACTIVE':
                self._isAlarmActive = True
            else:
                self._isAlarmActive = False

    def set_highlight(self, shouldHighlight: bool):
        if shouldHighlight:
            self.prim.GetAttribute('primvars:displayColor').Set(self._highlightColor)
            self._changedHighlight = False
        # Only change to default color once
        elif not self._changedHighlight:
            if not self._defaultColor:
                defaultColor = [Gf.Vec3f(0, 0, 1)] # blue
                self.prim.GetAttribute('primvars:displayColor').Set(defaultColor)
            else:
                self.prim.GetAttribute('primvars:displayColor').Set(self._defaultColor)
            self._changedHighlight = True

    def is_prim_selected(self):
        return self.selection.is_prim_path_selected(self.prim_path.__str__())

    # def on_destroy(self):
        # print(f"{__class__.__name__}.on_destroy()->{self.prim_path}")

    # def on_play(self):
        # print(f"{__class__.__name__}.on_play()->{self.prim_path}")

    def on_pause(self):
        self._runningTime = 0
        # print(f"{__class__.__name__}.on_pause()->{self.prim_path}")

    def on_stop(self):
        self._runningTime = 0
        # print(f"{__class__.__name__}.on_stop()->{self.prim_path}")

    def on_update(self, current_time: float, delta_time: float):
        state = get_state()
        executor = get_executor()
        # Fetch data approx every 10 seconds
        frequency = 10

        # This script is sometimes initialized before Main.py
        if state is None:
            pass

        if state.is_play:
            if round(self._runningTime, 2) % frequency == 0:
                endTime = datetime.now()
                startTime = endTime - timedelta(minutes=1)
                # Fetch alarm status in background process
                executor.submit(self.setAlarmStatus, date_to_iso(startTime), date_to_iso(endTime))
            self.set_highlight(self._isAlarmActive)
            self._runningTime = self._runningTime + delta_time
        else:
            self.set_highlight(False)
