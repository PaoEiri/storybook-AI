"""
Implementación de BaseImageProvider usando la Inference API de Hugging Face
(tier gratuito). Usa un modelo de difusión tipo Stable Diffusion.
"""

from huggingface_hub import InferenceClient

from .base import BaseImageProvider

# Modelo gratuito por defecto, buen balance calidad/velocidad para
# ilustración estilo libro infantil.
DEFAULT_MODEL = "stabilityai/stable-diffusion-xl-base-1.0"

CHILDREN_BOOK_STYLE_SUFFIX = (
    ", children's storybook illustration style, soft colors, "
    "whimsical, hand-drawn texture, warm lighting, simple background"
)


class HuggingFaceImageProvider(BaseImageProvider):
    def __init__(self, api_key: str, model: str = DEFAULT_MODEL):
        if not api_key:
            raise ValueError(
                "Falta HF_API_KEY. Consíguelo gratis en "
                "https://huggingface.co/settings/tokens"
            )
        self.client = InferenceClient(model=model, token=api_key)

    def generate_image(self, prompt: str) -> bytes:
        full_prompt = f"{prompt}{CHILDREN_BOOK_STYLE_SUFFIX}"
        image = self.client.text_to_image(full_prompt)

        # InferenceClient devuelve un objeto PIL.Image
        import io
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        return buf.getvalue()
