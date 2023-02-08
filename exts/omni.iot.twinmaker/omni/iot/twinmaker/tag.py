import omni.kit.commands
import os
from pxr import Sdf
from .script_utils import addPrim, attachPythonScript
from .prim_transform_utils import TUtil_SetTranslate, TUtil_SetScale

ENTITY_ATTR = 'entityId'
COMPONENT_ATTR = 'componentName'
PROPERTY_ATTR = 'propertyName'


class Tag:
    def __init__(self, dataBindingContext, primPath):
        # Create prim to reference in this object
        addPrim(primPath, 'Sphere')

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

    def __create_prim_attrs(self):
        prim = self.__get_prim()
        omni.kit.commands.execute(
            "CreateUsdAttributeCommand",
            prim=prim,
            attr_name=ENTITY_ATTR,
            attr_type=Sdf.ValueTypeNames.String
        )
        omni.kit.commands.execute(
            "CreateUsdAttributeCommand",
            prim=prim,
            attr_name=COMPONENT_ATTR,
            attr_type=Sdf.ValueTypeNames.String
        )
        omni.kit.commands.execute(
            "CreateUsdAttributeCommand",
            prim=prim,
            attr_name=PROPERTY_ATTR,
            attr_type=Sdf.ValueTypeNames.String
        )

    def __attach_prim_attrs(self):
        # 1. Create attributes for each ID
        self.__create_prim_attrs()

        # 2. Set attributes with each ID value
        prim = self.__get_prim()
        entityAttr = prim.GetAttribute(ENTITY_ATTR)
        entityAttr.Set(self._entityId)
        componentAttr = prim.GetAttribute(COMPONENT_ATTR)
        componentAttr.Set(self._componentName)
        propertyAttr = prim.GetAttribute(PROPERTY_ATTR)
        propertyAttr.Set(self._propertyName)

    def __attach_clickable_script(self):
        scriptPath = os.path.abspath(f'{os.path.abspath(__file__)}\\..\\..\\..\\..\\PythonScripting\\Clickable.py')
        attachPythonScript(self._primPath, scriptPath)

    def setTransform(self, parentTransform, transform):
        prim = self.__get_prim()

        # Set tag offset position
        parentTranslate = parentTransform['position']
        translate = transform['position']
        position = [
            parentTranslate[0] + translate[0],
            parentTranslate[1] + translate[1],
            parentTranslate[2] + translate[2]
        ]
        TUtil_SetTranslate(prim, position)
        # Sphere at scale 1 is too small
        TUtil_SetScale(prim, [40, 40, 40])
