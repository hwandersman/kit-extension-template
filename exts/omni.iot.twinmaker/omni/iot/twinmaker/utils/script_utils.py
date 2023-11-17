import os
import carb
from pxr import Sdf

import omni.kit.commands

from omni.iot.twinmaker.utils.omni_utils import get_prim, create_and_set_prim_attr, create_and_set_prim_array_attr
from omni.iot.twinmaker.constants import ENTITY_ATTR, COMPONENT_ATTR, PROPERTY_ATTR, RULE_OP_ATTR, \
    RULE_VAL_ATTR, MAT_COLOR_ATTR, CHANGE_MAT_PATH, RULES_KEY, BOUNDS_KEY, BOUND_MIN, BOUND_MAX, WIDGET_KEY

# Source: https://github.com/mati-nvidia/developer-office-hours/blob/main/exts/maticodes.doh_2023_01_13/scripts/add_script_component.py
def attach_python_script(primPath, scriptPath):
    carb.log_info('attaching to: ' + primPath + ', with script: ' + scriptPath)
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

def reset_attr(prim, attr_name, default_val):
    try:
        attr = prim.GetAttribute(attr_name).Get()
        attr.Set(default_val)
    except:
        pass

def get_json_field(data, field_name):
    try:
        return data[field_name]
    except:
        return None


# Attach attributes to prims with entity/component/property path, rule expression, and material to change
# Expected schema from JSON file:
# [{
#   "primPath": <REQUIRED>
#   "entityId": <REQUIRED>
#   "componentName": <REQUIRED>
#   "propertyName": <REQUIRED>
#   "widget": <REQUIRED> (ModelShader | ModelScaler | MotionIndicator)
#   "rule": [{ // optional list of rules
#       "ruleOperator": <REQUIRED>, // within a rule, these fields are required
#       "ruleValue": <REQUIRED>,
#       "colorHex": <OPTIONAL>,
#       "changeMaterialPath": <OPTIONAL>
#   }],
#   "dataBounds": { // optional
#       "minBound": <REQUIRED>,
#       "maxBound": <REQUIRED>
#   }
# }]
def attach_data_binding(data_binding_config):
    for data_binding in data_binding_config:
        prim_path = data_binding['primPath']
        prim = get_prim(prim_path)
        
        # Set entity / component / property path
        create_and_set_prim_attr(prim, ENTITY_ATTR, data_binding[ENTITY_ATTR])
        create_and_set_prim_attr(prim, COMPONENT_ATTR, data_binding[COMPONENT_ATTR])
        create_and_set_prim_attr(prim, PROPERTY_ATTR, data_binding[PROPERTY_ATTR])

        widget = data_binding[WIDGET_KEY]

        if widget == 'ModelShader':
            # Set rule attributes in an array in order
            rules_list = data_binding[RULES_KEY]
            if len(rules_list) > 0:
                model_shader_script_path = os.path.abspath(f'{os.path.abspath(__file__)}\\..\\..\\scripting\\ModelShader.py')
                # Reset list attributes
                reset_attr(prim, RULE_OP_ATTR, [])
                reset_attr(prim, RULE_VAL_ATTR, [])
                reset_attr(prim, MAT_COLOR_ATTR, [])
                reset_attr(prim, CHANGE_MAT_PATH, [])

                for rule in rules_list:
                    create_and_set_prim_array_attr(prim, RULE_OP_ATTR, rule[RULE_OP_ATTR])
                    create_and_set_prim_array_attr(prim, RULE_VAL_ATTR, rule[RULE_VAL_ATTR])
                    create_and_set_prim_array_attr(prim, MAT_COLOR_ATTR, get_json_field(rule, MAT_COLOR_ATTR))
                    create_and_set_prim_array_attr(prim, CHANGE_MAT_PATH, get_json_field(rule, CHANGE_MAT_PATH))
                # Attach ModelShader script
                attach_python_script(prim_path, model_shader_script_path)

        elif widget == 'ModelScaler' or widget == 'MotionIndicator':
            model_scaler_script_path = os.path.abspath(f'{os.path.abspath(__file__)}\\..\\..\\scripting\\ModelScaler.py')
            motion_indicator_script_path = os.path.abspath(f'{os.path.abspath(__file__)}\\..\\..\\scripting\\MotionIndicator.py')
            # Set bounds attributes
            bounds = data_binding[BOUNDS_KEY]
            create_and_set_prim_attr(prim, BOUND_MIN, bounds[BOUND_MIN])
            create_and_set_prim_attr(prim, BOUND_MAX, bounds[BOUND_MAX])
            # Attach script
            script = model_scaler_script_path if widget == 'ModelScaler' else motion_indicator_script_path
            attach_python_script(prim_path, script)


def attach_global_config(prim_path):
    scriptPath = os.path.abspath(f'{os.path.abspath(__file__)}\\..\\..\\scripting\\Main.py')
    attach_python_script(prim_path, scriptPath)