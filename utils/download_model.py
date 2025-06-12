# utils/download_model.py

import os
import requests
from tqdm import tqdm

def download_model_from_huggingface(model_url, save_path):
    if not os.path.exists(save_path):
        print(f"Downloading model from {model_url}")
        response = requests.get(model_url, stream=True)
        total = int(response.headers.get('content-length', 0))

        with open(save_path, 'wb') as file, tqdm(
            desc="Downloading",
            total=total,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for data in response.iter_content(chunk_size=1024):
                size = file.write(data)
                bar.update(size)
    else:
        print(f"Model already exists at {save_path}")
