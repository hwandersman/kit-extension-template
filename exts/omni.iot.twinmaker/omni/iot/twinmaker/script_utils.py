import omni.kit.commands
from pxr import Sdf


# Add reference node to model
# Omni can reference a USD or GLTF/GLB file directly
def addModelReference(primPath, modelPath):
    omni.kit.commands.execute(
        'CreateReference',
        usd_context=omni.usd.get_context(),
        path_to=Sdf.Path(primPath),
        asset_path=modelPath
    )


def addPrim(primPath, primType, attributes=None):
    if attributes is not None:
        omni.kit.commands.execute(
            'CreatePrim',
            prim_type=primType,
            prim_path=primPath,
            attributes=attributes
        )
    else:
        omni.kit.commands.execute(
            'CreatePrim',
            prim_type=primType,
            prim_path=primPath
        )


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
    scripts.append(scriptPath)
    attr.Set(scripts)