# Title LollmsComfyUI
# Licence: GPL-3.0
# Author : Paris Neo
# Forked from comfyanonymous's Comfyui nodes system
# check it out : https://github.com/comfyanonymous/ComfyUI
# Here is a copy of the LICENCE https://github.com/comfyanonymous/ComfyUI/blob/main/LICENSE
# All rights are reserved

from pathlib import Path
import sys
from lollms.app import LollmsApplication
from lollms.paths import LollmsPaths
from lollms.config import TypedConfig, ConfigTemplate, BaseConfig
import time
import io
import sys
import requests
import os
import base64
import subprocess
import time
import json
import platform
from dataclasses import dataclass
from PIL import Image, PngImagePlugin
from enum import Enum
from typing import List, Dict, Any
import uuid
from ascii_colors import ASCIIColors, trace_exception
from lollms.paths import LollmsPaths
from lollms.utilities import git_pull, show_yes_no_dialog, run_script_in_env, create_conda_env, run_python_script_in_env, PackageManager
from lollms.tti import LollmsTTI
import subprocess
import shutil
from tqdm import tqdm

if not PackageManager.check_package_installed("websocket"):
    PackageManager.install_or_update("websocket-client")
import websocket
if not PackageManager.check_package_installed("urllib"):
    PackageManager.install_or_update("urllib")
from urllib import request, parse

def verify_comfyui(lollms_paths:LollmsPaths):
    # Clone repository
    root_dir = lollms_paths.personal_path
    shared_folder = root_dir/"shared"
    comfyui_folder = shared_folder / "comfyui"
    return comfyui_folder.exists()

def download_file(url, folder_path, local_filename):
    # Make sure 'folder_path' exists
    folder_path.mkdir(parents=True, exist_ok=True)

    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        total_size = int(r.headers.get('content-length', 0))
        progress_bar = tqdm(total=total_size, unit='B', unit_scale=True)
        with open(folder_path / local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192): 
                f.write(chunk)
                progress_bar.update(len(chunk))
        progress_bar.close()

    return local_filename

def install_comfyui(lollms_app:LollmsApplication):
    root_dir = lollms_app.lollms_paths.personal_path
    shared_folder = root_dir/"shared"
    comfyui_folder = shared_folder / "comfyui"
    if comfyui_folder.exists():
        if show_yes_no_dialog("warning!","I have detected that there is a previous installation of stable diffusion.\nShould I remove it and continue installing?"):
            shutil.rmtree(comfyui_folder)
        elif show_yes_no_dialog("warning!","Continue installation?"):
            ASCIIColors.cyan("Installing comfyui conda environment with python 3.10")
            create_conda_env("comfyui","3.10")
            ASCIIColors.cyan("Done")
            return
        else:
            return

    subprocess.run(["git", "clone", "https://github.com/ParisNeo/ComfyUI.git", str(comfyui_folder)])
    subprocess.run(["git", "clone", "https://github.com/ParisNeo/ComfyUI-Manager.git", str(comfyui_folder/"custom_nodes/ComfyUI-Manager")])    
    subprocess.run(["git", "clone", "https://github.com/AlekPet/ComfyUI_Custom_Nodes_AlekPet.git", str(comfyui_folder/"custom_nodes/ComfyUI_Custom_Nodes_AlekPet")])
    subprocess.run(["git", "clone", "https://github.com/ParisNeo/lollms_nodes_suite.git", str(comfyui_folder/"custom_nodes/lollms_nodes_suite")])


    subprocess.run(["git", "clone", "https://github.com/jags111/efficiency-nodes-comfyui.git", str(comfyui_folder/"custom_nodes/efficiency-nodes-comfyui")]) 
    subprocess.run(["git", "clone", "https://github.com/Kosinkadink/ComfyUI-Advanced-ControlNet.git", str(comfyui_folder/"custom_nodes/ComfyUI-Advanced-ControlNet")]) 
    subprocess.run(["git", "clone", "https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git", str(comfyui_folder/"custom_nodes/ComfyUI-VideoHelperSuite")]) 
    subprocess.run(["git", "clone", "https://github.com/LykosAI/ComfyUI-Inference-Core-Nodes.git", str(comfyui_folder/"custom_nodes/ComfyUI-Inference-Core-Nodes")]) 
    subprocess.run(["git", "clone", "https://github.com/Fannovel16/comfyui_controlnet_aux.git", str(comfyui_folder/"custom_nodes/comfyui_controlnet_aux")]) 
    subprocess.run(["git", "clone", "https://github.com/Kosinkadink/ComfyUI-AnimateDiff-Evolved.git", str(comfyui_folder/"custom_nodes/ComfyUI-AnimateDiff-Evolved")]) 

    if show_yes_no_dialog("warning!","You will need to install an image generation model.\nDo you want to install an image model from civitai?\nI suggest Juggernaut XL.\nIt is a very good model.\nyou can always install more models afterwards in your comfyui folder/models.checkpoints"):
        download_file("https://civitai.com/api/download/models/357609", comfyui_folder/"models/checkpoints","Juggernaut_XL.safetensors")

    if show_yes_no_dialog("warning!","Do you want to install a video model from hugging face?\nIsuggest SVD XL."):
        download_file("https://huggingface.co/stabilityai/stable-video-diffusion-img2vid-xt/blob/main/svd_xt.safetensors", comfyui_folder/"models/checkpoints","svd_xt.safetensors")

    if show_yes_no_dialog("warning!","Do you want to install all control net models?"):
        (comfyui_folder/"models/controlnet").mkdir(parents=True, exist_ok=True)        
        download_file("https://huggingface.co/thibaud/controlnet-openpose-sdxl-1.0/resolve/main/OpenPoseXL2.safetensors", comfyui_folder/"models/controlnet","OpenPoseXL2.safetensors")
        download_file("https://huggingface.co/diffusers/controlnet-depth-sdxl-1.0/resolve/main/diffusion_pytorch_model.safetensors", comfyui_folder/"models/controlnet","DepthMap_XL.safetensors")


    if show_yes_no_dialog("warning!","Do you want to install all animation models?"):
        (comfyui_folder/"models/animatediff_models").mkdir(parents=True, exist_ok=True)
        download_file("https://huggingface.co/guoyww/animatediff/resolve/cd71ae134a27ec6008b968d6419952b0c0494cf2/mm_sdxl_v10_beta.ckpt", comfyui_folder/"models/animatediff_models","mm_sdxl_v10_beta.ckpt")
        
    
    create_conda_env("comfyui","3.10")
    if lollms_app.config.hardware_mode in ["nvidia", "nvidia-tensorcores"]:
        run_python_script_in_env("comfyui", "-m pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu121")
    if lollms_app.config.hardware_mode in ["amd", "amd-noavx"]:
        run_python_script_in_env("comfyui", "-m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm5.7")
    elif lollms_app.config.hardware_mode in ["cpu", "cpu-noavx"]:
        run_python_script_in_env("comfyui", "-m pip install --pre torch torchvision torchaudio")
    run_python_script_in_env("comfyui", f"-m pip install -r {comfyui_folder}/requirements.txt")
    
    lollms_app.comfyui = LollmsComfyUI(lollms_app)
    ASCIIColors.green("Comfyui installed successfully")
    lollms_app.HideBlockingMessage()

def upgrade_comfyui(lollms_app:LollmsApplication):
    root_dir = lollms_app.lollms_paths.personal_path
    shared_folder = root_dir/"shared"
    comfyui_folder = shared_folder / "comfyui"
    if not comfyui_folder.exists():
        lollms_app.InfoMessage("Comfyui is not installed, install it first")
        return

    subprocess.run(["git", "pull", str(comfyui_folder)])
    subprocess.run(["git", "pull", str(comfyui_folder/"custom_nodes/ComfyUI-Manager")])
    subprocess.run(["git",  "pull", str(comfyui_folder/"custom_nodes/efficiency-nodes-comfyui")])
    ASCIIColors.success("DONE")


def get_comfyui(lollms_paths:LollmsPaths):
    root_dir = lollms_paths.personal_path
    shared_folder = root_dir/"shared"
    comfyui_folder = shared_folder / "comfyui"
    comfyui_script_path = comfyui_folder / "main.py"
    git_pull(comfyui_folder)
    
    if comfyui_script_path.exists():
        ASCIIColors.success("comfyui found.")
        ASCIIColors.success("Loading source file...",end="")
        # use importlib to load the module from the file path
        from lollms.services.comfyui.lollms_comfyui import LollmsComfyUI
        ASCIIColors.success("ok")
        return LollmsComfyUI

class LollmsComfyUI(LollmsTTI):
    has_controlnet = False
    def __init__(
                    self, 
                    app:LollmsApplication, 
                    wm = "Artbot", 
                    max_retries=50,
                    comfyui_base_url=None,
                    share=False,
                    wait_for_service=True
                    ):
        if comfyui_base_url=="" or comfyui_base_url=="http://127.0.0.1:8188/":
            comfyui_base_url = None
        # Get the current directory
        lollms_paths = app.lollms_paths
        self.app = app
        root_dir = lollms_paths.personal_path
        
        self.wm = wm
        # Store the path to the script
        if comfyui_base_url is None:
            self.comfyui_base_url = "http://127.0.0.1:8188/"
            if not verify_comfyui(lollms_paths):
                install_comfyui(app.lollms_paths)
        else:
            self.comfyui_base_url = comfyui_base_url

        self.comfyui_url = self.comfyui_base_url+"/comfyuiapi/v1"
        shared_folder = root_dir/"shared"
        self.comfyui_folder = shared_folder / "comfyui"
        self.output_dir = root_dir / "outputs/comfyui"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        ASCIIColors.red(" _      ____  _      _      __  __  _____  _____                 __             _ ")
        ASCIIColors.red("| |    / __ \| |    | |    |  \/  |/ ____|/ ____|               / _|           (_)")
        ASCIIColors.red("| |   | |  | | |    | |    | \  / | (___ | |     ___  _ __ ___ | |_ _   _ _   _ _ ")
        ASCIIColors.red("| |   | |  | | |    | |    | |\/| |\___ \| |    / _ \| '_ ` _ \|  _| | | | | | | |")
        ASCIIColors.red("| |___| |__| | |____| |____| |  | |____) | |___| (_) | | | | | | | | |_| | |_| | |")
        ASCIIColors.red("|______\____/|______|______|_|  |_|_____/ \_____\___/|_| |_| |_|_|  \__, |\__,_|_|")
        ASCIIColors.red("                                     ______                         __/ |         ")
        ASCIIColors.red("                                    |______|                       |___/          ")

        ASCIIColors.red(" Forked from comfyanonymous's Comfyui nodes system")
        ASCIIColors.red(" Integration in lollms by ParisNeo")

        if not self.wait_for_service(1,False) and comfyui_base_url is None:
            ASCIIColors.info("Loading lollms_comfyui")
            if platform.system() == "Windows":
                ASCIIColors.info("Running on windows")
                script_path = self.comfyui_folder / "main.py"

                if share:
                    run_python_script_in_env("comfyui", str(script_path), cwd=self.comfyui_folder, wait=False)
                    # subprocess.Popen("conda activate " + str(script_path) +" --share", cwd=self.comfyui_folder)
                else:
                    run_python_script_in_env("comfyui", str(script_path), cwd=self.comfyui_folder, wait=False)
                    # subprocess.Popen(script_path, cwd=self.comfyui_folder)
            else:
                ASCIIColors.info("Running on linux/MacOs")
                script_path = str(self.comfyui_folder / "lollms_comfyui.sh")
                ASCIIColors.info(f"launcher path: {script_path}")
                ASCIIColors.info(f"comfyui path: {self.comfyui_folder}")

                if share:
                    run_script_in_env("comfyui","bash " + script_path +" --share", cwd=self.comfyui_folder)
                    # subprocess.Popen("conda activate " + str(script_path) +" --share", cwd=self.comfyui_folder)
                else:
                    run_script_in_env("comfyui","bash " + script_path, cwd=self.comfyui_folder)
                ASCIIColors.info("Process done")
                ASCIIColors.success("Launching Comfyui succeeded")

        # Wait until the service is available at http://127.0.0.1:8188//
        if wait_for_service:
            self.wait_for_service(max_retries=max_retries)
        else:
            ASCIIColors.warning("We are not waiting for the SD service to be up.\nThis means that you may need to wait a bit before you can use it.")


    def wait_for_service(self, max_retries = 50, show_warning=True):
        url = f"{self.comfyui_base_url}"
        # Adjust this value as needed
        retries = 0

        while retries < max_retries or max_retries<0:
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    print("Service is available.")
                    if self.app is not None:
                        self.app.success("Comfyui Service is now available.")
                    return True
            except requests.exceptions.RequestException:
                pass

            retries += 1
            time.sleep(1)
        if show_warning:
            print("Service did not become available within the given time.")
            if self.app is not None:
                self.app.error("Comfyui Service did not become available within the given time.")
        return False
            
    def paint(
                self,
                positive_prompt,
                negative_prompt,
                sampler_name="",
                seed=-1,
                scale=7.5,
                steps=20,
                img2img_denoising_strength=0.9,
                width=512,
                height=512,
                restore_faces=True,
                output_path=None
                ):
        client_id = str(uuid.uuid4())

        def queue_prompt(prompt):
            p = {"prompt": prompt, "client_id": client_id}
            data = json.dumps(p).encode('utf-8')
            req =  request.Request("http://{}/prompt".format(self.comfyui_base_url), data=data)
            return json.loads(request.urlopen(req).read())

        def get_image(filename, subfolder, folder_type):
            data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
            url_values = parse.urlencode(data)
            with request.urlopen("http://{}/view?{}".format(self.comfyui_base_url, url_values)) as response:
                return response.read()

        def get_history(prompt_id):
            with request.urlopen("http://{}/history/{}".format(self.comfyui_base_url, prompt_id)) as response:
                return json.loads(response.read())

        def get_images(ws, prompt):
            prompt_id = queue_prompt(prompt)['prompt_id']
            output_images = {}
            while True:
                out = ws.recv()
                if isinstance(out, str):
                    message = json.loads(out)
                    if message['type'] == 'executing':
                        data = message['data']
                        if data['node'] is None and data['prompt_id'] == prompt_id:
                            break #Execution is done
                else:
                    continue #previews are binary data

            history = get_history(prompt_id)[prompt_id]
            for o in history['outputs']:
                for node_id in history['outputs']:
                    node_output = history['outputs'][node_id]
                    if 'images' in node_output:
                        images_output = []
                        for image in node_output['images']:
                            image_data = get_image(image['filename'], image['subfolder'], image['type'])
                            images_output.append(image_data)
                    output_images[node_id] = images_output

            return output_images

        prompt_text = """
        {
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "cfg": 8,
                    "denoise": 1,
                    "latent_image": [
                        "5",
                        0
                    ],
                    "model": [
                        "4",
                        0
                    ],
                    "negative": [
                        "7",
                        0
                    ],
                    "positive": [
                        "6",
                        0
                    ],
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "seed": 8566257,
                    "steps": 20
                }
            },
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {
                    """+f"""
                    "ckpt_name": "{self.app.config.comfyui_model}"
                    """+"""
                }
            },
            "5": {
                "class_type": "EmptyLatentImage",
                "inputs": {
                    "batch_size": 1,
                    "height": 512,
                    "width": 512
                }
            },
            "6": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "clip": [
                        "4",
                        1
                    ],"""+f"""
                    "text": "{positive_prompt}"
                    """+"""
                }
            },
            "7": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "clip": [
                        "4",
                        1
                    ],"""+f"""
                    "text": "{negative_prompt}"
                    """+"""
                }
            },
            "8": {
                "class_type": "VAEDecode",
                "inputs": {
                    "samples": [
                        "3",
                        0
                    ],
                    "vae": [
                        "4",
                        2
                    ]
                }
            },
            "9": {
                "class_type": "SaveImage",
                "inputs": {
                    "filename_prefix": "ComfyUI",
                    "images": [
                        "8",
                        0
                    ]
                }
            }
        }
        """

        prompt = json.loads(prompt_text)
        #set the text prompt for our positive CLIPTextEncode
        prompt["6"]["inputs"]["text"] = "masterpiece best quality man"

        #set the seed for our KSampler node
        prompt["3"]["inputs"]["seed"] = 5

        ws = websocket.WebSocket()
        ws.connect("ws://{}/ws?clientId={}".format(self.comfyui_base_url, client_id))
        images = get_images(ws, prompt)
        return None
    
    def paint_from_images(self, positive_prompt: str, 
                            images: List[str], 
                            negative_prompt: str = "",
                            sampler_name="",
                            seed=-1,
                            scale=7.5,
                            steps=20,
                            img2img_denoising_strength=0.9,
                            width=512,
                            height=512,
                            restore_faces=True,
                            output_path=None
                            ) -> List[Dict[str, str]]:
        return None
    
