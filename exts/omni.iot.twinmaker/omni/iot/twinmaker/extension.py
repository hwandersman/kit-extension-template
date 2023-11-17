import os
import asyncio
import json

import omni.ext
import omni.ui as ui
import omni.usd
import carb.events

from omni.services.core import main

from omni.iot.twinmaker.services.api import router as api_router, set_entity_prim_map
from omni.iot.twinmaker.store import DataBindingStore
from omni.iot.twinmaker.scene_importer import SceneImporter
from omni.iot.twinmaker.utils.omni_utils import create_global_config_prim
from omni.iot.twinmaker.utils.script_utils import attach_global_config, attach_data_binding

class MyExtension(omni.ext.IExt):
    def __init__(self) -> None:
        self._router_prefix = '/twinmaker'
        self._initiated = False

    def _get_context(self):
        return omni.usd.get_context()

    def _on_timeline_event(self, e: carb.events.IEvent):
        context = self._get_context()
        if e.type == int(omni.timeline.TimelineEventType.PLAY):
            carb.log_info('timeline changed PLAY')
            context.set_pickable('/', False)
        elif e.type == int(omni.timeline.TimelineEventType.STOP):
            carb.log_info('timeline changed STOP')
            context.set_pickable('/', True)

    def on_startup(self, ext_id):
        carb.log_info('[omni.iot.twinmaker] extension startup')

        timeline_events = omni.timeline.get_timeline_interface().get_timeline_event_stream()
        self.timeline_event_sub = timeline_events.create_subscription_to_pop(self._on_timeline_event)

        # Register router
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
                data_binding_path_string_model = ui.SimpleStringModel(f'{os.path.abspath(__file__)}\\..\\dataBinding.json')

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
                    global_config = {
                        "workspace_id": workspace_string_model.as_string,
                        "role": assume_role_string_model.as_string,
                        "region": region_string_model.as_string
                    }
                    
                    global_logic_prim_path = create_global_config_prim(global_config['region'], global_config['role'], global_config['workspace_id'])
                    attach_global_config(global_logic_prim_path)

                    
                    file = open(data_binding_path_string_model.as_string)
                    data_binding_config = json.load(file)

                    # Assign data bindings to USD nodes
                    attach_data_binding(data_binding_config)

                    entity_prim_map = {}
                    for data_binding in data_binding_config:
                        prim_path = data_binding['primPath']
                        entity_id = data_binding['entityId']
                        entity_prim_map[entity_id] = prim_path
                    set_entity_prim_map(entity_prim_map)

                    DataBindingStore.force_reinit()

                    self._initiated = True

                def on_click_start():
                    if self._initiated:
                        DataBindingStore.get_instance().start_data_fetching()
                    else:
                        carb.log_warn('initiate the extension first!')

                def on_click_stop():
                    if self._initiated:
                        DataBindingStore.get_instance().stop_data_fetching()
                    else:
                        carb.log_warn('initiate the extension first!')

                with ui.HStack():
                    ui.Button('INIT', clicked_fn=on_click_init)
                    ui.Button('START_FETCHING', clicked_fn=on_click_start)
                    ui.Button('STOP_FETCHING', clicked_fn=on_click_stop)
                    ui.Button('IMPORT', clicked_fn=on_click_import)

    def on_shutdown(self):
        carb.log_info('[omni.iot.twinmaker] extension shutdown')

        if self._initiated:
            DataBindingStore.get_instance().stop_data_fetching()
        main.deregister_router(router=api_router, prefix=self._router_prefix)
