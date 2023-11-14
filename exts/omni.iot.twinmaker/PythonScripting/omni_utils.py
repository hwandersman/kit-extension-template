from pxr import Gf

def hexToVec3(hex):
    hexVal = hex
    if 'X' or 'x' in hex:
        hexVal = hex[2:]
    rgb = tuple(int(hexVal[i:i+2], 16) for i in (0, 2, 4))
    return Gf.Vec3f(rgb[0]/255, rgb[1]/255, rgb[2]/255)

def getAllPrimChildren(prim, children):
    primChildren = prim.GetChildren()

    if len(primChildren) == 0:
        return [prim]

    newChildren = children
    for child in primChildren:
        newChildren = newChildren + getAllPrimChildren(child, children)
    
    return newChildren

def bindMaterialCommand(primPath, materialPath):
    omni.kit.commands.execute(
        "BindMaterialCommand",
        prim_path=primPath,
        material_path=materialPath,
        strength=['weakerThanDescendants']
    )
