import boto3
import json
import omni.kit.asset_converter as converter
import omni.kit.commands
import omni.usd
from pxr import Sdf
from .script_utils import addModelReference, addPrim
from .prim_transform_utils import TUtil_SetTranslate, TUtil_SetRotateQuat, TUtil_SetScale
from .tag import Tag
import os
import uuid


DEFAULT_ASSUME_ROLE_ARN = '[ASSUME_ROLE_ARN]'

# 1. Load scene JSON from S3
# 2. Parse JSON for gltf/glb assets to load from S3
# 3. Download and import all assets from S3
# 4. Set transform of assets as defined in the scene JSON
# Can only support loading single model files (no separate textures / .bin files)


class SceneImporter:
    def __init__(self, workspaceId, assumeRoleARN=DEFAULT_ASSUME_ROLE_ARN):
        self._workspaceId = workspaceId
        self._region = 'us-east-1'

        self._tmClient = self.__getAWSClient('iottwinmaker', assumeRoleARN)
        self._s3Client = self.__getAWSClient('s3', assumeRoleARN)

        self._sceneJSON = {}

        workspaceResult = self._tmClient.get_workspace(
            workspaceId=self._workspaceId
        )
        workspaceBucketArn = workspaceResult['s3Location']
        # S3 bucket ARN is in the format "arn:aws:s3:::BUCKET_NAME"
        self._workspaceBucket = workspaceBucketArn.split(':::')[1]

    def __getAWSClient(self, serviceName, assumeRoleARN):
        if assumeRoleARN == DEFAULT_ASSUME_ROLE_ARN:
            return boto3.client(serviceName, self._region)

        stsClient = boto3.client('sts')
        response = stsClient.assume_role(
            RoleArn=assumeRoleARN,
            RoleSessionName=f'nvidia-ov-session{uuid.uuid1()}',
            DurationSeconds=1800
        )
        newSession = boto3.Session(
            aws_access_key_id=response['Credentials']['AccessKeyId'],
            aws_secret_access_key=response['Credentials']['SecretAccessKey'],
            aws_session_token=response['Credentials']['SessionToken']
        )
        return newSession.client(serviceName, self._region)

    # Load scene JSON of sceneId into memory
    def load_scene(self, sceneId):
        print(f'Loading scene {sceneId}')
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
        nodeLen = len(self._sceneJSON['nodes'])
        print(f'Loaded scene {sceneId} with {nodeLen} nodes')

    def __import_progress_callback(current_step: int, total: int):
        print(f"{current_step} of {total}")

    # Download 3D model from S3
    async def __load_model(self, modelPath):
        modelAlreadyDownloaded = os.path.isfile(modelPath)
        if not modelAlreadyDownloaded:
            print(f'Loading model from S3: {modelPath}')
            self._s3Client.download_file(
                self._workspaceBucket,
                modelPath,
                modelPath
            )

    def __convert_file_name(self, filePath, format):
        fileName = filePath.split('.')[-2]
        return f'{os.getcwd()}\\{fileName}.{format}'

    # Convert model to USD
    async def __convert_to_usd(self, modelPath):
        task_manager = converter.get_instance()
        outputPath = self.__convert_file_name(modelPath, 'usd')
        modelAlreadyImported = os.path.isfile(outputPath)
        if modelAlreadyImported:
            return outputPath

        task = task_manager.create_converter_task(
            modelPath,
            outputPath,
            self.__import_progress_callback
        )
        success = await task.wait_until_finished()
        if not success:
            print(f'Failed to load file: {modelPath}')
            print(task.get_status())
            print(task.get_error_message())
            return None
        else:
            print(f'Successfully imported file at path: {outputPath}')
            return outputPath

    # Get prim at a given path
    def __get_prim(self, primPath):
        if primPath is None:
            return None
        stage = omni.usd.get_context().get_stage()
        return stage.GetPrimAtPath(primPath)

    # Build hierarchy of USD based on scene JSON hierarchy
    def __generate_reference_path(self, nodeIdx):
        if nodeIdx >= len(self._sceneJSON['nodes']):
            return None

        nodes = self._sceneJSON['nodes']
        node = nodes[nodeIdx]
        modelName = node['name']

        # Build node path based on parent path
        # Assume 1 parent per child
        if 'parent' not in node:
            # Root node
            path = f'/World/{modelName}'
        else:
            # Child node
            parentReferencePath = nodes[node['parent']]['referencePath']
            path = f'{parentReferencePath}/{modelName}'

        if 'children' in node:
            for childIdx in node['children']:
                # Set pointer to parent in children for future reference
                self._sceneJSON['nodes'][childIdx]['parent'] = nodeIdx

        node['referencePath'] = path
        return path

    async def import_scene_assets(self):
        print('Importing 3D assets for scene')
        nodes = self._sceneJSON['nodes']
        # Add empty transform as a parent of all tags
        addPrim('/World/Tags', 'Xform')
        for i in range(len(nodes)):
            node = nodes[i]
            modelPrim = None
            for component in node['components']:
                if 'uri' in component:
                    modelPath = component['uri']
                    # 1. Load model from S3
                    await self.__load_model(modelPath)
                    # 2. Convert model to USD
                    usdFilePath = await self.__convert_to_usd(modelPath)
                    # 3. Add reference to local USD in stage hierarchy
                    primPath = self.__generate_reference_path(i)
                    addModelReference(primPath, usdFilePath)
                    # 4. Get reference prim to transform it
                    modelPrim = self.__get_prim(primPath)
                elif 'valueDataBinding' in component and component['type'] == 'Tag':
                    parentNode = nodes[node['parent']]
                    # Assuming parent is parsed before child, get the name of the model the tag is attached to
                    primName = parentNode['name']
                    primPath = f'/World/Tags/{primName}'
                    tag = Tag(component['valueDataBinding']['dataBindingContext'], primPath)
                    tag.setTransform(parentNode['transform'], node['transform'])

            if modelPrim is not None:
                transform = node['transform']
                TUtil_SetTranslate(modelPrim, transform['position'])
                TUtil_SetRotateQuat(modelPrim, transform['rotation'])
                TUtil_SetScale(modelPrim, transform['scale'])
            # Add empty transform
            elif 'children' in node:
                primPath = self.__generate_reference_path(i)
                addPrim(primPath, 'Xform')
