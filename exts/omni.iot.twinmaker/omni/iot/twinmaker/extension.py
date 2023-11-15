import asyncio
import omni.ext
import omni.ui as ui
import omni.usd
import os
import carb.events
from pxr import Sdf
from .scene_importer import DEFAULT_ASSUME_ROLE_ARN, SceneImporter
from .script_utils import add_prim, attach_python_script, create_and_set_string_attr, attach_data_binding
from .constants import WORKSPACE_ATTR, ASSUME_ROLE_ATTR, REGION_ATTR, ENTITY_ATTR

from omni.services.core import main
from .services.api import router as api_router


# Any class derived from `omni.ext.IExt` in top level module (defined in `python.modules` of `extension.toml`) will be
# instantiated when extension gets enabled and `on_startup(ext_id)` will be called. Later when extension gets disabled
# on_shutdown() is called.
class MyExtension(omni.ext.IExt):
    def __init__(self) -> None:
        self._router_prefix = '/twinmaker'

    def _get_context(self):
        return omni.usd.get_context()

    def _on_stage_event(self, e: carb.events.IEvent):
        if e.type == int(omni.usd.StageEventType.SELECTION_CHANGED):
            carb.log_info('selection changed ' + str(e))
            usd_context = self._get_context()
            stage = usd_context.get_stage()
            prim_paths = usd_context.get_selection().get_selected_prim_paths()
            carb.log_info('selected prim paths ' + str(prim_paths))
            
            if not prim_paths:
                # This turns off the manipulator when everything is deselected
                self._select_entity(None)
                return

            prim = stage.GetPrimAtPath(prim_paths[0])
            val = prim.GetAttribute(ENTITY_ATTR).Get()
            carb.log_info(f'{ENTITY_ATTR} {val}')

    def _on_timeline_event(self, e: carb.events.IEvent):
        context = self._get_context()
        if e.type == int(omni.timeline.TimelineEventType.PLAY):
            carb.log_info('timeline changed PLAY')
            context.set_pickable('/', False)
            context.set_pickable('/World/Selectable', True)
        elif e.type == int(omni.timeline.TimelineEventType.STOP):
            carb.log_info('timeline changed STOP')
            context.set_pickable('/', True)

    def _select_entity(self, entity_id):
        pass

    # ext_id is current extension id. It can be used with extension manager to query additional information, like where
    # this extension is located on filesystem.
    def on_startup(self, ext_id):
        carb.log_info('[omni.iot.twinmaker] extension startup')

        # Register router
        context = self._get_context()
        self.stage_event_sub = (
            context
            .get_stage_event_stream()
            .create_subscription_to_pop(self._on_stage_event, name='TwinMaker Subscription')
        )
        
        timeline_events = omni.timeline.get_timeline_interface().get_timeline_event_stream()
        self.timeline_event_sub = timeline_events.create_subscription_to_pop(self._on_timeline_event)

        main.register_router(router=api_router, prefix=self._router_prefix, tags=['TwinMaker'])

        # Setup config window
        self._window = ui.Window('AWS IoT TwinMaker', width=300, height=300)
        with self._window.frame:
            with ui.VStack():
                # workspace_string_model = ui.SimpleStringModel('[WORKSPACE_ID]')
                # scene_string_model = ui.SimpleStringModel('[SCENE_ID]')
                # assume_role_string_model = ui.SimpleStringModel(DEFAULT_ASSUME_ROLE_ARN)
                # regionStringModel = ui.SimpleStringModel('[REGION]')
                # dataBindingPathStringModel = ui.SimpleStringModel('[PATH_TO_DATA_BINDING_FILE]')
                workspace_string_model = ui.SimpleStringModel('AmazonWarehouse')
                scene_string_model = ui.SimpleStringModel('OmniverseTest')
                assume_role_string_model = ui.SimpleStringModel('arn:aws:iam::612335474273:role/CrossAccountTwinMakerAccess')
                region_string_model = ui.SimpleStringModel('us-west-2')
                data_binding_path_string_model = ui.SimpleStringModel(f'{os.path.abspath(__file__)}\\..\\..\\..\\..\\dataBinding.json')
                ui.Label('Enter your workspaceId')
                ui.StringField(model=workspace_string_model)
                ui.Label('Enter your sceneId')
                ui.StringField(model=scene_string_model)
                ui.Label('[Optional] Enter a role to assume')
                ui.StringField(model=assume_role_string_model)
                ui.Label('Enter the region')
                ui.StringField(model=region_string_model)
                ui.Label('Enter the path to USD data binding')
                ui.StringField(model=data_binding_path_string_model)

                # Import TwinMaker scene
                def on_click_import():
                    scene_importer = SceneImporter(workspace_string_model.as_string, region_string_model.as_string, assume_role_string_model.as_string)
                    scene_importer.load_scene(scene_string_model.as_string)
                    asyncio.ensure_future(scene_importer.import_scene_assets())

                # Add Main PythonScripting logic
                # TODO: Use event system to order script initialization
                def on_click_init():
                    logic_prim_path = '/World/Logic'
                    logic_prim = add_prim(logic_prim_path, 'Xform')
                    # Attach attributes to pass info to python script
                    create_and_set_string_attr(logic_prim, WORKSPACE_ATTR, workspace_string_model.as_string)
                    create_and_set_string_attr(logic_prim, ASSUME_ROLE_ATTR, assume_role_string_model.as_string)
                    create_and_set_string_attr(logic_prim, REGION_ATTR, region_string_model.as_string)
                    # Attach python script
                    script_path = os.path.abspath(f'{os.path.abspath(__file__)}\\..\\..\\..\\..\\PythonScripting\\Main.py')
                    attach_python_script(logic_prim_path, script_path)
                    # Assign data bindings to USD nodes
                    attach_data_binding(data_binding_path_string_model.as_string)

                with ui.HStack():
                    ui.Button('INIT', clicked_fn=on_click_init)
                    ui.Button('IMPORT', clicked_fn=on_click_import)

    def on_shutdown(self):
        carb.log_info('[omni.iot.twinmaker] extension shutdown')

        main.deregister_router(router=api_router, prefix=self._router_prefix)
