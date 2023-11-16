import omni.kit
from pxr import Gf

from omni.iot.twinmaker.constants import ENTITY_ATTR, COMPONENT_ATTR, PROPERTY_ATTR, \
    RULE_OP_ATTR, RULE_VAL_ATTR, WORKSPACE_ATTR, ASSUME_ROLE_ATTR, REGION_ATTR
from omni.iot.twinmaker.data_models import DataBinding, RuleExpression

from omni.iot.twinmaker.utils.script_utils import add_prim, create_and_set_prim_attr

GLOBAL_LOGIC_PRIM_PATH = '/World/Logic'

def hex_to_vec_3(hex):
    hexVal = hex
    if 'X' or 'x' in hex:
        hexVal = hex[2:]
    rgb = tuple(int(hexVal[i:i+2], 16) for i in (0, 2, 4))
    return Gf.Vec3f(rgb[0]/255, rgb[1]/255, rgb[2]/255)

def get_all_prim_children(prim, children):
    prim_children = prim.GetChildren()

    if len(prim_children) == 0:
        return [prim]

    new_children = children
    for child in prim_children:
        new_children = new_children + get_all_prim_children(child, children)
    
    return new_children

def bind_material_command(prim_path, material_path):
    omni.kit.commands.execute(
        "BindMaterialCommand",
        prim_path=prim_path,
        material_path=material_path,
        strength=['strongerThanDescendants']
    )

def get_data_binding_from_prim(prim):
    entity_id = prim.GetAttribute(ENTITY_ATTR).Get()
    component_name = prim.GetAttribute(COMPONENT_ATTR).Get()
    property_name = prim.GetAttribute(PROPERTY_ATTR).Get()
    data_binding = DataBinding(entity_id, component_name, property_name)
    return data_binding

def get_rule_exp_list_from_prim(prim):
    property_name = prim.GetAttribute(PROPERTY_ATTR).Get()
    rule_op_list = prim.GetAttribute(RULE_OP_ATTR).Get()
    rule_val_list = prim.GetAttribute(RULE_VAL_ATTR).Get()
    rule_len = len(rule_op_list)
    rule_expression_list = []
    for i in range(rule_len):
        rule_expression_list.append(RuleExpression(property_name, rule_op_list[i], rule_val_list[i]))
    rule_expression_list = rule_expression_list
    return rule_expression_list

def get_global_config():
    stage = omni.usd.get_context().get_stage()
    logic_prim = stage.GetPrimAtPath(GLOBAL_LOGIC_PRIM_PATH)
    
    if not logic_prim:
        return None
    
    workspace_id = logic_prim.GetAttribute(WORKSPACE_ATTR).Get()
    assume_role_arn = logic_prim.GetAttribute(ASSUME_ROLE_ATTR).Get()
    region = logic_prim.GetAttribute(REGION_ATTR).Get()

    return {
        'region': region, 
        'role': assume_role_arn, 
        'workspace_id': workspace_id
    }

def create_global_config_prim(region, role, workspace):
    logicPrim = add_prim(GLOBAL_LOGIC_PRIM_PATH, 'Xform')
    create_and_set_prim_attr(logicPrim, WORKSPACE_ATTR, workspace)
    create_and_set_prim_attr(logicPrim, ASSUME_ROLE_ATTR, role)
    create_and_set_prim_attr(logicPrim, REGION_ATTR, region)
    return GLOBAL_LOGIC_PRIM_PATH
