import asyncio
import omni.ext
import omni.ui as ui
import os
from .scene_importer import DEFAULT_ASSUME_ROLE_ARN, SceneImporter
from .script_utils import addPrim, attachPythonScript, createAndSetPrimAttr

WORKSPACE_ATTR = 'workspaceId'
ASSUME_ROLE_ATTR = 'assumeRoleARN'


# Any class derived from `omni.ext.IExt` in top level module (defined in `python.modules` of `extension.toml`) will be
# instantiated when extension gets enabled and `on_startup(ext_id)` will be called. Later when extension gets disabled
# on_shutdown() is called.
class MyExtension(omni.ext.IExt):
    # ext_id is current extension id. It can be used with extension manager to query additional information, like where
    # this extension is located on filesystem.
    def on_startup(self, ext_id):
        print('[omni.iot.twinmaker] extension startup')

        self._window = ui.Window('AWS IoT TwinMaker', width=300, height=300)
        with self._window.frame:
            with ui.VStack():
                # workspaceStringModel = ui.SimpleStringModel('[WORKSPACE_ID]')
                # sceneStringModel = ui.SimpleStringModel('[SCENE_ID]')
                # assumeRoleStringModel = ui.SimpleStringModel(DEFAULT_ASSUME_ROLE_ARN)
                workspaceStringModel = ui.SimpleStringModel('CookieFactory')
                sceneStringModel = ui.SimpleStringModel('CookieFactory')
                assumeRoleStringModel = ui.SimpleStringModel('arn:aws:iam::540844875673:role/CrossAccountTwinMakerAccess')
                ui.Label('Enter your workspaceId')
                ui.StringField(model=workspaceStringModel)
                ui.Label('Enter your sceneId')
                ui.StringField(model=sceneStringModel)
                ui.Label('[Optional] Enter a role to assume')
                ui.StringField(model=assumeRoleStringModel)

                def on_click():
                    # 1. Add Main PythonScripting logic
                    logicPrimPath = '/World/Logic'
                    logicPrim = addPrim(logicPrimPath, 'Xform')
                    # Attach attributes to pass info to python script
                    createAndSetPrimAttr(logicPrim, WORKSPACE_ATTR, workspaceStringModel.as_string)
                    createAndSetPrimAttr(logicPrim, ASSUME_ROLE_ATTR, assumeRoleStringModel.as_string)
                    # Attach python script
                    scriptPath = os.path.abspath(f'{os.path.abspath(__file__)}\\..\\..\\..\\..\\PythonScripting\\Main.py')
                    attachPythonScript(logicPrimPath, scriptPath)

                    # 2. Import TwinMaker scene
                    sceneImporter = SceneImporter(workspaceStringModel.as_string, assumeRoleStringModel.as_string)
                    sceneImporter.load_scene(sceneStringModel.as_string)
                    asyncio.ensure_future(sceneImporter.import_scene_assets())

                with ui.HStack():
                    ui.Button('IMPORT', clicked_fn=on_click)

    def on_shutdown(self):
        print('[omni.iot.twinmaker] extension shutdown')
