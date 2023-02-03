from pxr import Usd, UsdGeom, Gf

# Credit to https://github.com/ft-lab/Omniverse_extension_SetOrigin/blob/main/exts/ft_lab.Tools.SetOrigin/ft_lab/Tools/SetOrigin/scripts/TransformUtil.py


# ---------------------------.
# Set Translate.
# ---------------------------.
def TUtil_SetTranslate(prim: Usd.Prim, vector):
    tV = Gf.Vec3f(vector[0], vector[1], vector[2])
    trans = prim.GetAttribute("xformOp:translate").Get()

    if trans is not None:
        # Specify a value for each type.
        if type(trans) == Gf.Vec3f:
            prim.GetAttribute("xformOp:translate").Set(Gf.Vec3f(tV))
        elif type(trans) == Gf.Vec3d:
            prim.GetAttribute("xformOp:translate").Set(Gf.Vec3d(tV))
    else:
        # xformOpOrder is also updated.
        xformAPI = UsdGeom.XformCommonAPI(prim)
        xformAPI.SetTranslate(Gf.Vec3d(tV))


# ---------------------------.
# Set Scale.
# ---------------------------.
def TUtil_SetScale(prim: Usd.Prim, vector):
    sV = Gf.Vec3f(vector[0], vector[1], vector[2])
    scale = prim.GetAttribute("xformOp:scale").Get()

    if scale is not None:
        # Specify a value for each type.
        if type(scale) == Gf.Vec3f:
            prim.GetAttribute("xformOp:scale").Set(Gf.Vec3f(sV))
        elif type(scale) == Gf.Vec3d:
            prim.GetAttribute("xformOp:scale").Set(Gf.Vec3d(sV))
    else:
        # xformOpOrder is also updated.
        xformAPI = UsdGeom.XformCommonAPI(prim)
        xformAPI.SetScale(Gf.Vec3f(sV))


# ---------------------------.
# Set Rotate.
# ---------------------------.
def TUtil_SetRotate(prim: Usd.Prim, vector):
    rV = Gf.Vec3f(vector[0], vector[1], vector[2])
    # Get rotOrder.
    # If rotation does not exist, rotOrder = UsdGeom.XformCommonAPI.RotationOrderXYZ.
    xformAPI = UsdGeom.XformCommonAPI(prim)
    time_code = Usd.TimeCode.Default()
    _, _, _, _, rotOrder = xformAPI.GetXformVectors(time_code)

    # Convert rotOrder to "xformOp:rotateXYZ" etc.
    t = xformAPI.ConvertRotationOrderToOpType(rotOrder)
    rotateAttrName = "xformOp:" + UsdGeom.XformOp.GetOpTypeToken(t)

    # Set rotate.
    rotate = prim.GetAttribute(rotateAttrName).Get()
    if rotate is not None:
        # Specify a value for each type.
        if type(rotate) == Gf.Vec3f:
            prim.GetAttribute(rotateAttrName).Set(Gf.Vec3f(rV))
        elif type(rotate) == Gf.Vec3d:
            prim.GetAttribute(rotateAttrName).Set(Gf.Vec3d(rV))
    else:
        # xformOpOrder is also updated.
        xformAPI.SetRotate(Gf.Vec3f(rV), rotOrder)