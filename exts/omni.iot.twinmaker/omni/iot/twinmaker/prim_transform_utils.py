from pxr import Usd, UsdGeom, Gf
from scipy.spatial.transform import Rotation

# Credit to https://github.com/ft-lab/Omniverse_extension_SetOrigin/blob/main/exts/ft_lab.Tools.SetOrigin/ft_lab/Tools/SetOrigin/scripts/TransformUtil.py


# ---------------------------.
# Set Translate.
# ---------------------------.
def TUtil_SetTranslate(prim: Usd.Prim, vector):
    # Referencing a USD enlarges the model by 100x (translations are 100x) when compared to GLTF/GLB
    tV = Gf.Vec3f(vector[0] * 100, vector[1] * 100, vector[2] * 100)
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
    # OV rotation calculated in quaternions
    # TM scene rotations are in XYZ radians
    rotation = Rotation.from_euler("xyz", vector)
    rotQuat = rotation.as_quat()
    rV = Gf.Quatf(rotQuat[3], rotQuat[0], rotQuat[1], rotQuat[2])
    rot = prim.GetAttribute("xformOp:orient").Get()

    if rot is not None:
        if type(rot) == Gf.Quatf:
            prim.GetAttribute("xformOp:orient").Set(Gf.Quatf(rV))
        elif type(rot) == Gf.Quatd:
            prim.GetAttribute("xformOp:orient").Set(Gf.Quatd(rV))
    else:
        xformAPI = UsdGeom.XformCommonAPI(prim)
        xformAPI.SetRotate(Gf.Quatf(rV))
