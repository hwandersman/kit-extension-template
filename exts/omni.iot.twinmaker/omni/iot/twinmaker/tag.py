import omni.kit.commands
import os
from pxr import Sdf

from omni.iot.twinmaker.utils.omni_utils import add_prim, create_and_set_prim_attr
from omni.iot.twinmaker.utils.script_utils import attach_python_script
from omni.iot.twinmaker.utils.prim_transform_utils import TUtil_SetTranslate, TUtil_SetScale

ENTITY_ATTR = 'entityId'
COMPONENT_ATTR = 'componentName'
PROPERTY_ATTR = 'propertyName'


class Tag:
    def __init__(self, dataBindingContext, primPath):
        # Create prim to reference in this object
        add_prim(primPath, 'Sphere')

        self._entityId = dataBindingContext['entityId']
        self._componentName = dataBindingContext['componentName']
        self._propertyName = dataBindingContext['propertyName']
        self._primPath = primPath

        # # Attach python script and attributes to reference in that script
        self.__attach_prim_attrs()
        self.__attach_clickable_script()

    def __get_prim(self):
        stage = omni.usd.get_context().get_stage()
        return stage.GetPrimAtPath(self._primPath)

    def __attach_prim_attrs(self):
        prim = self.__get_prim()
        create_and_set_prim_attr(prim, ENTITY_ATTR, self._entityId)
        create_and_set_prim_attr(prim, COMPONENT_ATTR, self._componentName)
        create_and_set_prim_attr(prim, PROPERTY_ATTR, self._propertyName)

    def __attach_clickable_script(self):
        script_path = os.path.abspath(f'{os.path.abspath(__file__)}\\..\\scripting\\Clickable.py')
        attach_python_script(self._primPath, script_path)

    def set_transform(self, parent_transform, transform):
        prim = self.__get_prim()

        # Set tag offset position
        parent_translate = parent_transform['position']
        translate = transform['position']
        position = [
            parent_translate[0] + translate[0],
            parent_translate[1] + translate[1],
            parent_translate[2] + translate[2]
        ]
        TUtil_SetTranslate(prim, position)
        # Sphere at scale 1 is too small
        TUtil_SetScale(prim, [40, 40, 40])
