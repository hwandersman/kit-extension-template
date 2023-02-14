# AWS IoT TwinMaker Extension

Use this extension in your Omniverse app to import your IoT TwinMaker scene and 3D assets.

## AWS IoT TwinMaker Background

AWS IoT TwinMaker enables users to build digital twin applications for monitoring real industrial workflows. You can build interactive dashboards for engineers on the plant floor to help monitor the live and historical health of their systems. These dashboards feature a 3D scene to connect a virtual replica of your building or machine to real IoT data. AWS IoT TwinMaker supports 3D assets in the glTF format, which is a 3D file format that enables efficient transmission and loading of 3D models in applications. The [glTF](https://github.com/KhronosGroup/glTF) format minimizes the size of 3D assets and the runtime processing needed to unpack and use them.

However, the browser is limited for rendering high fidelity, dense, and complex scenes. Omniverse has a rich suite of features to enhance your IoT TwinMaker scene. This includes animation, physics simulation, and a more powerful rendering engine.

## Getting Started

### Add this extension to your *Omniverse App*

1. In the *Omniverse App* open extension manager: *Window* &rarr; *Extensions*.
2. In the *Extension Manager Window* open a settings page, with a small gear button in the top left bar.
3. In the settings page there is a list of *Extension Search Paths*. Add this repo as another search path: `git://github.com/hwandersman/kit-extension-template.git?branch=main&dir=exts`
4. Now you can find `omni.iot.twinmaker` extension in the top left search bar. Select and enable it.
5. A window will pop up. Drag it into a tab on your app.

### Using the extension

#### Prerequisites:
* Create an IoT TwinMaker workspace and scene ([docs](https://docs.aws.amazon.com/iot-twinmaker/latest/guide/twinmaker-gs.html))
    * This demo depends on data live streaming to your IoT TwinMaker properties
* AWS credentials configured in your machine's environment with permissions for S3 and IoT TwinMaker
    * [Credentials configuration basics](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html)
* Update the botocore build in your Omniverse dependency cache. The latest Omniverse apps (2022.3) don't have IoT TwinMaker in botocore.
    * Install the latest `botocore` version (>1.29.70) on your machine:
    ```bash
    pip install botocore
    pip show botocore
    ```
    * My botocore is found at `$HOME\AppData\Local\Programs\Python\Python311\Lib\site-packages`
    * Copy and overwrite `botocore` and `botocore-[VERSION].dist-info` folders from your Python build to the Omniverse app pip_prebundle
        * Omniverse app path: `$HOME\AppData\Local\ov\pkg\[App]\kit\extscore\omni.kit.pip_archive\pip_prebundle`
        * For example, my version of Omniverse Create, `[App]` is `create-2022.3.1`

#### Import your IoT TwinMaker scene
1. Enter a workspaceId
2. Enter a sceneId
3. [Optional] Enter the ARN of an IAM role to assume
    a. If you want to use the permissions of another role in your account
    b. If you want to access the workspace and scene of another account ([cross account access](https://docs.aws.amazon.com/IAM/latest/UserGuide/tutorial_cross-account-with-roles.html))
4. Click the "INIT" button
    a. This will add an empty prim called "Logic" to your scene with the script "PythonScripting/Main.py" attached
    b. You must click this button first to ensure the IoT TwinMaker context is loaded for your scene
5. Click the "IMPORT" button
    a. Extension will load your scene JSON
    b. Extension will download and convert the scene assets to USD
    c. Extension will set up the scene hierarchy in the currently loaded USD stage
6. After the scene loads click the "Play" button to see Tag widgets change color based on IoT data streaming in your IoT TwinMaker account