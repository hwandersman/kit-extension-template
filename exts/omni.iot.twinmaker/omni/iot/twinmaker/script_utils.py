import omni.kit.commands
from pxr import Sdf
import json
from .constants import ENTITY_ATTR, COMPONENT_ATTR, PROPERTY_ATTR, RULE_OP_ATTR, RULE_VAL_ATTR, MAT_COLOR_ATTR, CHANGE_MAT_PATH
import os

# Add reference node to model
# Omni can reference a USD or GLTF/GLB file directly
def addModelReference(primPath, modelPath):
    omni.kit.commands.execute(
        'CreateReference',
        usd_context=omni.usd.get_context(),
        path_to=Sdf.Path(primPath),
        asset_path=modelPath
    )


def addPrim(primPath, primType):
    omni.kit.commands.execute(
        'CreatePrim',
        prim_type=primType,
        prim_path=primPath
    )
    stage = omni.usd.get_context().get_stage()
    return stage.GetPrimAtPath(primPath)


# Source: https://github.com/mati-nvidia/developer-office-hours/blob/main/exts/maticodes.doh_2023_01_13/scripts/add_script_component.py
def attachPythonScript(primPath, scriptPath):
    # Create the Python Scripting Component property
    omni.kit.commands.execute(
        'ApplyScriptingAPICommand',
	    paths=[Sdf.Path(primPath)]
    )
    omni.kit.commands.execute('RefreshScriptingPropertyWindowCommand')

    # Add your script to the property
    stage = omni.usd.get_context().get_stage()
    prim = stage.GetPrimAtPath(primPath)
    attr = prim.GetAttribute('omni:scripting:scripts')
    scripts = attr.Get()
    # Property with no script paths returns None
    if scripts is None:
        scripts = []
    else:
        # Property with scripts paths returns VtArray.
        # Convert to list to make it easier to work with.
        scripts = list(scripts)

    if len(scripts) != 1:
        scripts.append(scriptPath)
        attr.Set(scripts)


def createAndSetPrimAttr(prim, attrName, attrValue):
    attr = prim.CreateAttribute(attrName, Sdf.ValueTypeNames.String)
    attr.Set(attrValue)

# Attach attributes to prims with entity/component/property path, rule expression, and material to change
# Expected schema from JSON file:
# [{
#   primPath: /World/prim/path
#   entityId: <>
#   componentName: <>
#   propertyName: <>
#   ruleOperator: <>
#   ruleValue: <>
#   ruleMaterialPath: /World/material/path
# }]
def attachDataBinding(filePath):
    file = open(filePath)
    stage = omni.usd.get_context().get_stage()
    data = json.load(file)

    modelShaderScriptPath = os.path.abspath(f'{os.path.abspath(__file__)}\\..\\..\\..\\..\\PythonScripting\\ModelShader.py')

    for dataBinding in data:
        primPath = dataBinding['primPath']
        prim = stage.GetPrimAtPath(primPath)
        createAndSetPrimAttr(prim, ENTITY_ATTR, dataBinding[ENTITY_ATTR])
        createAndSetPrimAttr(prim, COMPONENT_ATTR, dataBinding[COMPONENT_ATTR])
        createAndSetPrimAttr(prim, PROPERTY_ATTR, dataBinding[PROPERTY_ATTR])
        createAndSetPrimAttr(prim, RULE_OP_ATTR, dataBinding[RULE_OP_ATTR])
        createAndSetPrimAttr(prim, RULE_VAL_ATTR, dataBinding[RULE_VAL_ATTR])
        createAndSetPrimAttr(prim, MAT_COLOR_ATTR, dataBinding[MAT_COLOR_ATTR])
        createAndSetPrimAttr(prim, CHANGE_MAT_PATH, dataBinding[CHANGE_MAT_PATH])
        attachPythonScript(primPath, modelShaderScriptPath)
