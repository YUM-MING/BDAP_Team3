# utils/download_model.py

import os
import requests

def download_model_from_huggingface(model_url: str, save_path: str):
    """Hugging Face URL에서 모델 파일을 다운로드합니다."""
    if os.path.exists(save_path):
        print(f"✅ 이미 모델이 존재합니다: {save_path}")
        return

    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    print(f"📥 모델 다운로드 시작: {model_url}")

    with requests.get(model_url, stream=True) as r:
        r.raise_for_status()
        with open(save_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    print(f"✅ 모델 다운로드 완료: {save_path}")
