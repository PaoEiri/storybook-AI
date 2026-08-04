"""
Implementación de BaseImageProvider usando la Inference API de Hugging Face
(tier gratuito). Usa un modelo de difusión tipo Stable Diffusion.
"""

from huggingface_hub import InferenceClient

from .base import BaseImageProvider
from prompts.loader import load_prompt

# Modelo gratuito por defecto, buen balance calidad/velocidad para
# ilustración estilo libro infantil.
DEFAULT_MODEL = "stabilityai/stable-diffusion-xl-base-1.0"


class HuggingFaceImageProvider(BaseImageProvider):
    def __init__(self, api_key: str, model: str = DEFAULT_MODEL):
        if not api_key:
            raise ValueError(
                "Falta HF_API_KEY. Consíguelo gratis en "
                "https://huggingface.co/settings/tokens"
            )
        self.client = InferenceClient(model=model, token=api_key)

    def generate_image(self, prompt: str) -> bytes:
        full_prompt = f"{prompt}, {load_prompt('illustration_style.txt')}"
        image = self.client.text_to_image(full_prompt)

        # InferenceClient devuelve un objeto PIL.Image
        import io
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        return buf.getvalue()
