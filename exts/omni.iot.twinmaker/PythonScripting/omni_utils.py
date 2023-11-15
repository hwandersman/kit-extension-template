import omni.kit
from pxr import Gf

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
