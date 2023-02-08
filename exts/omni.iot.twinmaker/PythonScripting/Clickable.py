import boto3
from datetime import datetime, timedelta
from omni.kit.scripting import BehaviorScript
from pxr import Gf

from .Main import get_state

ENTITY_ATTR = 'entityId'
COMPONENT_ATTR = 'componentName'
PROPERTY_ATTR = 'propertyName'


def date_to_iso(time):
    return f'{time.isoformat()}Z'


class Clickable(BehaviorScript):
    def on_init(self):
        self._runningTime = 0

        self._workspaceId = 'CookieFactory'
        self._region = 'us-east-1'
        self._tmClient = boto3.client('iottwinmaker', self._region)

        self._defaultColor = self.prim.GetAttribute('primvars:displayColor').Get()
        self._highlightColor = [Gf.Vec3f(1, 0, 0)] # red
        self._isAlarmActive = False
        self._changedHighlight = False

        self.__init_data_binding()

        # print(f"{__class__.__name__}.on_init()->{self.prim_path}")

    # Get attributes from prim with property data binding
    def __init_data_binding(self):
        self._entityId = self.prim.GetAttribute(ENTITY_ATTR).Get()
        self._componentName = self.prim.GetAttribute(COMPONENT_ATTR).Get()
        self._propertyName = self.prim.GetAttribute(PROPERTY_ATTR).Get()

    # TODO: Investigate running TwinMaker APIs in a background process
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
        print(f'{self.prim_path} GetPropertyValueHistory length: {len(values)}')
        if len(values) > 0 and len(values[0]) > 0:
            if values[0]['values'][0]['stringValue'] == 'ACTIVE':
                self._isAlarmActive = True

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
        # Fetch data approx every 5 seconds
        frequency = 10
        if state.is_play:
            if round(self._runningTime, 2) % frequency == 0:
                endTime = datetime.now()
                startTime = endTime - timedelta(minutes=1)
                # TODO: Fix long load times that cause OV to be unresponsive
                # self.setAlarmStatus(date_to_iso(startTime), date_to_iso(endTime))
            self.set_highlight(self._isAlarmActive)
            self._runningTime = self._runningTime + delta_time
        else:
            self.set_highlight(False)
