# Backend/imageGeneration.py
"""
Text-to-image generation via the Hugging Face Inference API
(Stable Diffusion XL), with local saving and cross-platform image opening.
"""

import io
import os
import sys
import re
from pathlib import Path
from random import randint

import requests
from PIL import Image
from dotenv import dotenv_values

BASE_DIR = Path(__file__).resolve().parent
IMAGES_DIR = BASE_DIR.parent / "Generated_Images"
API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"


def _safe_stub(prompt: str) -> str:
    """Filesystem-safe filename stub derived from the prompt."""
    stub = re.sub(r"[^a-zA-Z0-9_-]", "_", prompt.strip())
    stub = re.sub(r"_+", "_", stub).strip("_")
    return stub[:60] or "image"


def open_images(prompt: str) -> None:
    stub = _safe_stub(prompt)
    if not IMAGES_DIR.exists():
        return

    for file in IMAGES_DIR.iterdir():
        if file.name.startswith(stub):
            try:
                if sys.platform.startswith("win"):
                    os.startfile(str(file))  # type: ignore[attr-defined]
                elif sys.platform == "darwin":
                    os.system(f"open '{file}'")
                else:
                    os.system(f"xdg-open '{file}'")
            except Exception as e:
                print(f"[Warning] Could not auto-open {file}: {e}")


def GenerateImage(prompt: str, print_func=print) -> str:
    prompt = (prompt or "").strip()
    if not prompt:
        return "Image generation failed: no prompt provided."

    try:
        print_func(f"[Image] Generating image for: {prompt}")

        env_vars = dotenv_values(BASE_DIR.parent / ".env")
        api_key = (
            env_vars.get("HUGGINGFACE_API_KEY")
            or env_vars.get("HuggingFaceAPIKey")
            or os.environ.get("HUGGINGFACE_API_KEY")
        )

        if not api_key or api_key == "your_huggingface_key":
            print_func("[Warning] HUGGINGFACE_API_KEY not set or is a placeholder in .env.")
            return "Image generation failed: Hugging Face API key is missing or invalid in your .env file."

        headers = {"Authorization": f"Bearer {api_key}"}

        try:
            response = requests.post(API_URL, headers=headers, json={"inputs": prompt}, timeout=60)
        except requests.RequestException as e:
            print_func(f"[Error] Network error contacting Hugging Face: {e}")
            return f"Image generation failed: network error ({e})"

        content_type = response.headers.get("content-type", "")

        if response.status_code != 200 or "image" not in content_type:
            # Hugging Face returns JSON error bodies (e.g. model loading, rate limit)
            try:
                err = response.json()
                detail = err.get("error", str(err))
            except ValueError:
                detail = response.text[:200]
            print_func(f"[Error] Hugging Face API error ({response.status_code}): {detail}")
            return f"Image generation failed: {detail}"

        try:
            image = Image.open(io.BytesIO(response.content))
        except Exception as e:
            print_func(f"[Error] Failed to decode image response: {e}")
            return "Failed to generate image: response was not a valid image."

        IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        stub = _safe_stub(prompt)
        filename = IMAGES_DIR / f"{stub}_{randint(1000, 9999)}.jpg"
        image.convert("RGB").save(filename, "JPEG")

        print_func(f"[Image] Saved to {filename}")
        open_images(prompt)
        return f"Image generated and saved to {filename}"

    except Exception as e:
        print_func(f"[Error] generating image: {e}")
        return f"Error: {e}"


if __name__ == "__main__":
    print(GenerateImage(input("Describe the image to generate: ")))