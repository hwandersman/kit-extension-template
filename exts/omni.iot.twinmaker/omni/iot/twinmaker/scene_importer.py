import boto3
import json
import omni.kit.asset_converter as converter
import omni.kit.commands
import omni.usd
from pxr import Sdf
from .prim_transform_utils import TUtil_SetTranslate, TUtil_SetRotate, TUtil_SetScale
import os

# 1. Load scene JSON from S3
# 2. Parse JSON for gltf/glb assets to load from S3
# 3. Download and import all assets from S3
# 4. Set transform of assets as defined in the scene JSON

# Can only support loading single model files (no separate textures / .bin files)
class SceneImporter:
    def __init__(self, workspaceId):
        self._workspaceId = workspaceId
        self._region = 'us-east-1'
        self._tmClient = boto3.client('iottwinmaker', self._region)
        self._s3Client = boto3.client('s3', self._region)
        self._sceneJSON = {}

        workspaceResult = self._tmClient.get_workspace(
            workspaceId=self._workspaceId
        )
        workspaceBucketArn = workspaceResult['s3Location']
        # S3 bucket ARN is in the format "arn:aws:s3:::BUCKET_NAME"
        self._workspaceBucket = workspaceBucketArn.split(':::')[1]

    # Load scene JSON of sceneId into memory
    def load_scene(self, sceneId):
        print('Loading scene {}'.format(sceneId))
        # Get scene JSON path in the workspace S3 bucket
        sceneResult = self._tmClient.get_scene(
            workspaceId=self._workspaceId,
            sceneId=sceneId
        )
        sceneLocation = sceneResult['contentLocation']

        # sceneLocation is in the format "s3://BUCKET_NAME/..PATH../SCENE_FILE"
        sceneFile = sceneLocation.split('/')[-1]

        # Get scene JSON from S3
        result = self._s3Client.get_object(
            Bucket=self._workspaceBucket,
            Key=sceneFile
        )
        sceneText = result['Body'].read().decode('utf-8')
        self._sceneJSON = json.loads(sceneText)
        print('Loaded scene {} with {} nodes'.format(sceneId, len(self._sceneJSON['nodes'])))

    def __import_progress_callback(current_step: int, total: int):
        print(f"{current_step} of {total}")

    async def __load_model(self, modelPath):
        print('Loading model from S3: {}'.format(modelPath))
        self._s3Client.download_file(
            self._workspaceBucket,
            modelPath,
            modelPath
        )

        task_manager = converter.get_instance()
        path = '.'
        task = task_manager.create_converter_task(
            path,
            path,
            self.__import_progress_callback
        )
        success = await task.wait_until_finished()
        if not success:
            print('Failed to load file: {}'.format(modelPath))
            print(task.get_status())
            print(task.get_error_message())
        else:
            print('Successfully loaded file at path: {}\\{}'.format(os.getcwd(), modelPath))

    def __get_prim(self, primPath):
        stage = omni.usd.get_context().get_stage()
        # selection = omni.usd.get_context().get_selection()
        # paths = selection.get_selected_prim_paths()

        # prim = None
        # for path in paths:
        #     prim = stage.GetPrimAtPath(path)
        #     break
        # return prim
        return stage.GetPrimAtPath(primPath)

    # Add reference to default World prim in stage
    def __add_model_reference(self, nodeIdx, modelPath):
        node = self._sceneJSON['nodes'][nodeIdx]
        modelName = node['name']

        # Build node path based on parent path
        # Assume 1 parent per child
        if 'parentReferencePath' not in node:
            path = '/World/{}'.format(modelName)
        else:
            path = '{}/{}'.format(node['parentReferencePath'], modelName)

        if 'children' in node:
            for childIdx in node['children']:
                self._sceneJSON['nodes'][childIdx]['parentReferencePath'] = path

        omni.kit.commands.execute(
            'CreateReference',
            usd_context=omni.usd.get_context(),
            path_to=Sdf.Path(path),
            asset_path=modelPath
        )
        return path

    async def import_scene_assets(self):
        print('Importing 3D assets for scene')
        nodes = self._sceneJSON['nodes']
        modelsToLoad = []
        for i in range(len(nodes)):
            node = nodes[i]
            modelPrim = None
            for component in node['components']:
                if 'uri' in component:
                    modelPath = component['uri']
                    modelAlreadyDownloaded = os.path.isfile('{}\\{}'.format(os.getcwd(), modelPath))
                    if not modelAlreadyDownloaded and modelPath not in modelsToLoad:
                        modelsToLoad.append(modelPath)
                        await self.__load_model(modelPath)

                    modelReference = self.__add_model_reference(i, modelPath)
                    modelPrim = self.__get_prim(modelReference)

            if modelPrim is not None:
                transform = node['transform']
                TUtil_SetTranslate(modelPrim, transform['position'])
                TUtil_SetRotate(modelPrim, transform['rotation'])
                TUtil_SetScale(modelPrim, transform['scale'])
