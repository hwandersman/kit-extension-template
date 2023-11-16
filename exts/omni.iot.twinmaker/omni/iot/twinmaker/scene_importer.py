import os
import json

import omni.kit.asset_converter as converter
import omni.kit.commands
import omni.usd

from omni.iot.twinmaker.utils.script_utils import add_model_reference, add_prim
from omni.iot.twinmaker.utils.prim_transform_utils import TUtil_SetTranslate, TUtil_SetRotateQuat, TUtil_SetScale
from omni.iot.twinmaker.utils.aws_utils import get_aws_client
from omni.iot.twinmaker.tag import Tag

DEFAULT_ASSUME_ROLE_ARN = '[ASSUME_ROLE_ARN]'

# 1. Load scene JSON from S3
# 2. Parse JSON for gltf/glb assets to load from S3
# 3. Download and import all assets from S3
# 4. Set transform of assets as defined in the scene JSON
# Can only support loading single model files (no separate textures / .bin files)


class SceneImporter:
    def __init__(self, workspace_id, region, assume_role_arn=DEFAULT_ASSUME_ROLE_ARN):
        self._workspace_id = workspace_id

        self._tm_client = get_aws_client('iottwinmaker', region, assume_role_arn)
        self._s3_client = get_aws_client('s3', region, assume_role_arn)

        self._scene_json = {}

        workspace_result = self._tm_client.get_workspace(
            workspaceId=self._workspace_id
        )
        workspace_bucket_arn = workspace_result['s3Location']
        # S3 bucket ARN is in the format "arn:aws:s3:::BUCKET_NAME"
        self._workspace_bucket = workspace_bucket_arn.split(':::')[1]

    # Load scene JSON of sceneId into memory
    def load_scene(self, scene_id):
        print(f'Loading scene {scene_id}')
        # Get scene JSON path in the workspace S3 bucket
        scene_result = self._tm_client.get_scene(
            workspaceId=self._workspace_id,
            sceneId=scene_id
        )
        scene_location = scene_result['contentLocation']

        # sceneLocation is in the format "s3://BUCKET_NAME/..PATH../SCENE_FILE"
        scene_file = scene_location.split('/')[-1]

        # Get scene JSON from S3
        result = self._s3_client.get_object(
            Bucket=self._workspace_bucket,
            Key=scene_file
        )
        scene_text = result['Body'].read().decode('utf-8')
        self._scene_json = json.loads(scene_text)
        node_len = len(self._scene_json['nodes'])
        print(f'Loaded scene {scene_id} with {node_len} nodes')

    def __import_progress_callback(self, current_step: int, total: int):
        print(f"{current_step} of {total}")

    # Download 3D model from S3
    async def __load_model(self, model_path):
        model_already_downloaded = os.path.isfile(model_path)
        if not model_already_downloaded:
            print(f'Loading model from S3: {model_path}')
            self._s3_client.download_file(
                self._workspace_bucket,
                model_path,
                model_path
            )

    def __convert_file_name(self, file_path, file_format):
        file_name = file_path.split('.')[-2]
        return f'{os.getcwd()}\\{file_name}.{file_format}'

    # Convert model to USD
    async def __convert_to_usd(self, model_path):
        task_manager = converter.get_instance()
        output_path = self.__convert_file_name(model_path, 'usd')
        model_already_imported = os.path.isfile(output_path)
        if model_already_imported:
            return output_path

        task = task_manager.create_converter_task(
            model_path,
            output_path,
            self.__import_progress_callback
        )
        success = await task.wait_until_finished()
        if not success:
            print(f'Failed to load file: {model_path}')
            print(task.get_status())
            print(task.get_error_message())
            return None
        else:
            print(f'Successfully imported file at path: {output_path}')
            return output_path

    # Get prim at a given path
    def __get_prim(self, prim_path):
        if prim_path is None:
            return None
        stage = omni.usd.get_context().get_stage()
        return stage.GetPrimAtPath(prim_path)

    # Build hierarchy of USD based on scene JSON hierarchy
    def __generate_reference_path(self, node_idx):
        if node_idx >= len(self._scene_json['nodes']):
            return None

        nodes = self._scene_json['nodes']
        node = nodes[node_idx]
        model_name = node['name']

        # Build node path based on parent path
        # Assume 1 parent per child
        if 'parent' not in node:
            # Root node
            path = f'/World/{model_name}'
        else:
            # Child node
            parent_reference_path = nodes[node['parent']]['referencePath']
            path = f'{parent_reference_path}/{model_name}'

        if 'children' in node:
            for childIdx in node['children']:
                # Set pointer to parent in children for future reference
                self._scene_json['nodes'][childIdx]['parent'] = node_idx

        node['referencePath'] = path
        return path

    async def import_scene_assets(self):
        print('Importing 3D assets for scene')
        nodes = self._scene_json['nodes']
        # Add empty transform as a parent of all tags
        add_prim('/World/Tags', 'Xform')
        for i in range(len(nodes)):
            node = nodes[i]
            model_prim = None
            for component in node['components']:
                if 'uri' in component:
                    model_path = component['uri']
                    # 1. Load model from S3
                    await self.__load_model(model_path)
                    # 2. Convert model to USD
                    usd_file_path = await self.__convert_to_usd(model_path)
                    # 3. Add reference to local USD in stage hierarchy
                    prim_path = self.__generate_reference_path(i)
                    add_model_reference(prim_path, usd_file_path)
                    # 4. Get reference prim to transform it
                    model_prim = self.__get_prim(prim_path)
                elif 'valueDataBinding' in component and component['type'] == 'Tag':
                    parent_node = nodes[node['parent']]
                    # Assuming parent is parsed before child, get the name of the model the tag is attached to
                    prim_name = parent_node['name']
                    prim_path = f'/World/Tags/{prim_name}'
                    tag = Tag(component['valueDataBinding']['dataBindingContext'], prim_path)
                    tag.set_transform(parent_node['transform'], node['transform'])

            if model_prim is not None:
                transform = node['transform']
                TUtil_SetTranslate(model_prim, transform['position'])
                TUtil_SetRotateQuat(model_prim, transform['rotation'])
                TUtil_SetScale(model_prim, transform['scale'])
            # Add empty transform
            elif 'children' in node:
                prim_path = self.__generate_reference_path(i)
                add_prim(prim_path, 'Xform')
