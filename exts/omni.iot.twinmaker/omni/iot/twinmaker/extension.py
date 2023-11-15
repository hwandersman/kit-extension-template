import asyncio
import omni.ext
import omni.ui as ui
import os
import carb.events
from .scene_importer import DEFAULT_ASSUME_ROLE_ARN, SceneImporter
from .script_utils import addPrim, attachPythonScript, createAndSetPrimAttr, attachDataBinding
from .constants import WORKSPACE_ATTR, ASSUME_ROLE_ATTR, REGION_ATTR


# Any class derived from `omni.ext.IExt` in top level module (defined in `python.modules` of `extension.toml`) will be
# instantiated when extension gets enabled and `on_startup(ext_id)` will be called. Later when extension gets disabled
# on_shutdown() is called.
class MyExtension(omni.ext.IExt):
    # ext_id is current extension id. It can be used with extension manager to query additional information, like where
    # this extension is located on filesystem.
    def on_startup(self, ext_id):
        carb.log_info('[omni.iot.twinmaker] extension startup')

        self._window = ui.Window('AWS IoT TwinMaker', width=300, height=300)
        with self._window.frame:
            with ui.VStack():
                # workspaceStringModel = ui.SimpleStringModel('[WORKSPACE_ID]')
                # sceneStringModel = ui.SimpleStringModel('[SCENE_ID]')
                # assumeRoleStringModel = ui.SimpleStringModel(DEFAULT_ASSUME_ROLE_ARN)
                # regionStringModel = ui.SimpleStringModel('[REGION]')
                # dataBindingPathStringModel = ui.SimpleStringModel('[PATH_TO_DATA_BINDING_FILE]')
                workspaceStringModel = ui.SimpleStringModel('AmazonWarehouse')
                sceneStringModel = ui.SimpleStringModel('OmniverseTest')
                assumeRoleStringModel = ui.SimpleStringModel('arn:aws:iam::612335474273:role/CrossAccountTwinMakerAccess')
                regionStringModel = ui.SimpleStringModel('us-west-2')
                dataBindingPathStringModel = ui.SimpleStringModel(f'{os.path.abspath(__file__)}\\..\\..\\..\\..\\dataBinding.json')
                ui.Label('Enter your workspaceId')
                ui.StringField(model=workspaceStringModel)
                ui.Label('Enter your sceneId')
                ui.StringField(model=sceneStringModel)
                ui.Label('[Optional] Enter a role to assume')
                ui.StringField(model=assumeRoleStringModel)
                ui.Label('Enter the region')
                ui.StringField(model=regionStringModel)
                ui.Label('Enter the path to USD data binding')
                ui.StringField(model=dataBindingPathStringModel)

                # Import TwinMaker scene
                def on_click_import():
                    sceneImporter = SceneImporter(workspaceStringModel.as_string, regionStringModel.as_string, assumeRoleStringModel.as_string)
                    sceneImporter.load_scene(sceneStringModel.as_string)
                    asyncio.ensure_future(sceneImporter.import_scene_assets())

                # Add Main PythonScripting logic
                # TODO: Use event system to order script initialization
                def on_click_init():
                    logicPrimPath = '/World/Logic'
                    logicPrim = addPrim(logicPrimPath, 'Xform')
                    # Attach attributes to pass info to python script
                    createAndSetPrimAttr(logicPrim, WORKSPACE_ATTR, workspaceStringModel.as_string)
                    createAndSetPrimAttr(logicPrim, ASSUME_ROLE_ATTR, assumeRoleStringModel.as_string)
                    createAndSetPrimAttr(logicPrim, REGION_ATTR, regionStringModel.as_string)
                    # Attach python script
                    scriptPath = os.path.abspath(f'{os.path.abspath(__file__)}\\..\\..\\..\\..\\PythonScripting\\Main.py')
                    attachPythonScript(logicPrimPath, scriptPath)
                    # Assign data bindings to USD nodes
                    attachDataBinding(dataBindingPathStringModel.as_string)

                with ui.HStack():
                    ui.Button('INIT', clicked_fn=on_click_init)
                    ui.Button('IMPORT', clicked_fn=on_click_import)

    def on_shutdown(self):
        carb.log_info('[omni.iot.twinmaker] extension shutdown')
