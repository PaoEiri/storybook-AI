"""
Helpers para validar y preparar las imágenes subidas por el usuario
y las generadas por el modelo de imagen.
"""

import io
from PIL import Image

ALLOWED_MIME_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/webp"}
MAX_DIMENSION = 1536  # evita mandar imágenes gigantes a la API de visión


def validate_and_prepare_image(uploaded_file) -> tuple[bytes, str]:
    """
    Recibe un archivo subido (objeto file-like de Streamlit) y devuelve
    una tupla (bytes_normalizados, mime_type) lista para enviar al
    proveedor de LLM con visión.
    """
    image = Image.open(uploaded_file)
    image = image.convert("RGB")

    # Redimensionar si es demasiado grande, para ahorrar tokens/costes
    if max(image.size) > MAX_DIMENSION:
        image.thumbnail((MAX_DIMENSION, MAX_DIMENSION))

    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue(), "image/png"


def bytes_to_pil(image_bytes: bytes) -> Image.Image:
    """Convierte bytes de imagen a un objeto PIL.Image para mostrar en la UI."""
    return Image.open(io.BytesIO(image_bytes))
