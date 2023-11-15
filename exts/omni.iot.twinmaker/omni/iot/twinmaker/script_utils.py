import omni.kit.commands
from pxr import Sdf, Gf
import json
from .constants import ENTITY_ATTR, COMPONENT_ATTR, PROPERTY_ATTR, RULES_KEY, RULE_OP_ATTR, RULE_VAL_ATTR, MAT_COLOR_ATTR, CHANGE_MAT_PATH
import os
import carb.events

# Add reference node to model
# Omni can reference a USD or GLTF/GLB file directly
def add_model_reference(prim_path, model_path):
    omni.kit.commands.execute(
        'CreateReference',
        usd_context=omni.usd.get_context(),
        path_to=Sdf.Path(prim_path),
        asset_path=model_path
    )


def add_prim(prim_path, prim_type):
    omni.kit.commands.execute(
        'CreatePrim',
        prim_type=prim_type,
        prim_path=prim_path
    )
    stage = omni.usd.get_context().get_stage()
    return stage.GetPrimAtPath(prim_path)


# Source: https://github.com/mati-nvidia/developer-office-hours/blob/main/exts/maticodes.doh_2023_01_13/scripts/add_script_component.py
def attach_python_script(prim_path, script_path):
    # Create the Python Scripting Component property
    omni.kit.commands.execute(
        'ApplyScriptingAPICommand',
	    paths=[Sdf.Path(prim_path)]
    )
    omni.kit.commands.execute('RefreshScriptingPropertyWindowCommand')

    # Add your script to the property
    stage = omni.usd.get_context().get_stage()
    prim = stage.GetPrimAtPath(prim_path)
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
        scripts.append(script_path)
        attr.Set(scripts)


def create_and_set_string_attr(prim, attr_name, attr_value):
    attr = prim.CreateAttribute(attr_name, Sdf.ValueTypeNames.String)
    attr.Set(attr_value)

def create_and_set_string_array_attr(prim, attr_name, attr_value):
    set_attr = attr_value if attr_value != '' else 'NONE'
    try:
        string_array_attr = prim.GetAttribute(attr_name)
        string_array = string_array_attr.Get()
        concat_string_array = list(string_array) + [set_attr]
        string_array_attr.Set(concat_string_array)
    except:
        attr = prim.CreateAttribute(attr_name, Sdf.ValueTypeNames.StringArray)
        attr.Set([set_attr])

def reset_attr(prim, attr_name, default_val):
    try:
        attr = prim.GetAttribute(attr_name).Get()
        attr.Set(default_val)
    except:
        pass

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
def attach_data_binding(file_path):
    file = open(file_path)
    stage = omni.usd.get_context().get_stage()
    data = json.load(file)

    model_shader_script_path = os.path.abspath(f'{os.path.abspath(__file__)}\\..\\..\\..\\..\\PythonScripting\\ModelShader.py')

    for data_binding in data:
        prim_path = data_binding['primPath']
        prim = stage.GetPrimAtPath(prim_path)

        # Set entity / component / property path
        create_and_set_string_attr(prim, ENTITY_ATTR, data_binding[ENTITY_ATTR])
        create_and_set_string_attr(prim, COMPONENT_ATTR, data_binding[COMPONENT_ATTR])
        create_and_set_string_attr(prim, PROPERTY_ATTR, data_binding[PROPERTY_ATTR])

        # Set rule attributes in an array in order
        rules_list = data_binding[RULES_KEY]
        # Reset list attributes
        reset_attr(prim, RULE_OP_ATTR, [])
        reset_attr(prim, RULE_VAL_ATTR, [])
        reset_attr(prim, MAT_COLOR_ATTR, [])
        reset_attr(prim, CHANGE_MAT_PATH, [])
        for rule in rules_list:
            create_and_set_string_array_attr(prim, RULE_OP_ATTR, rule[RULE_OP_ATTR])
            create_and_set_string_array_attr(prim, RULE_VAL_ATTR, rule[RULE_VAL_ATTR])
            create_and_set_string_array_attr(prim, MAT_COLOR_ATTR, rule[MAT_COLOR_ATTR])
            create_and_set_string_array_attr(prim, CHANGE_MAT_PATH, rule[CHANGE_MAT_PATH])
                
        # Attach ModelShader script
        attach_python_script(prim_path, model_shader_script_path)
