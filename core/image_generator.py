"""
Generador de ilustraciones para el libro de cuentos.

Estrategia de consistencia visual:
- En la primera ilustración, el LLM genera un prompt visual detallado del personaje
  y lo guardamos como "character_visual_prompt" en session_state.
- En las siguientes ilustraciones, reutilizamos ese mismo prompt de personaje
  como ancla, solo cambiando la acción y el escenario.
Esto garantiza que el personaje se vea igual en las 3 ilustraciones.
"""
from providers.base import BaseImageProvider, BaseLLMProvider

# Prompt para la PRIMERA ilustración: extrae descripción visual del personaje
FIRST_ILLUSTRATION_PROMPT = """You are an art director for a children's illustrated storybook.

Extract a precise visual description of the main character from this story fragment,
then write a full image generation prompt for the FIRST illustration.

CHARACTER DESCRIPTION FROM DRAWING ANALYSIS:
{character_description}

STORY SCENE:
{scene_text}

Write ONE image prompt in English with this EXACT structure:

CHARACTER APPEARANCE: [describe every physical detail — body shape, size, colors, face, ears, tail, limbs, distinctive features. Be extremely specific so this character can be reproduced identically in future images]
ACTION: [what is the character doing in this exact scene]
SETTING: [environment, lighting, colors, background elements]
STYLE: children's illustrated storybook, soft watercolor style, warm golden light, whimsical detailed background

Output format: combine all into a single paragraph of 80-110 words. No labels. No explanations. Only the prompt.
"""

# Prompt para ilustraciones SIGUIENTES: reutiliza el prompt de personaje ya establecido
SUBSEQUENT_ILLUSTRATION_PROMPT = """You are an art director for a children's illustrated storybook.

CRITICAL: The main character MUST look IDENTICAL to the first illustration.
Use this EXACT character description — do not change any physical detail:

{character_visual_prompt}

Now write a new image prompt for this new scene:

STORY SCENE:
{scene_text}

Write ONE image prompt in English (80-110 words):
- Start with the EXACT same character description as above (copy it verbatim)
- Then add: what the character is doing in this new scene
- Then add: the new setting (environment, lighting, background)
- End with: children's illustrated storybook, soft watercolor style, warm golden light, whimsical detailed background, SAME CHARACTER as first illustration

Output: single paragraph. No labels. No explanations. Only the prompt.
"""


def build_first_prompt(
    llm_provider: BaseLLMProvider,
    character_description: str,
    scene_text: str,
) -> str:
    """Genera el prompt de la primera ilustración y lo devuelve completo."""
    prompt = FIRST_ILLUSTRATION_PROMPT.format(
        character_description=character_description,
        scene_text=scene_text[:800],
    )
    result = ""
    for chunk in llm_provider.stream_story([{"role": "user", "content": prompt}]):
        result += chunk
    return result.strip().strip('"').strip("'")


def build_subsequent_prompt(
    llm_provider: BaseLLMProvider,
    character_visual_prompt: str,
    scene_text: str,
) -> str:
    """Genera el prompt de una ilustración posterior, anclado al prompt de la primera."""
    prompt = SUBSEQUENT_ILLUSTRATION_PROMPT.format(
        character_visual_prompt=character_visual_prompt,
        scene_text=scene_text[:800],
    )
    result = ""
    for chunk in llm_provider.stream_story([{"role": "user", "content": prompt}]):
        result += chunk
    return result.strip().strip('"').strip("'")


def generate_illustration(
    image_provider: BaseImageProvider,
    character_description: str,
    scene_text: str,
    images_used: int,
    max_images: int,
    llm_provider: BaseLLMProvider | None = None,
    character_visual_prompt: str | None = None,
    user_direction: str | None = None,
) -> tuple[bytes | None, str | None]:
    """
    Genera una ilustración y devuelve (bytes, visual_prompt_usado).
    El visual_prompt_usado debe guardarse en session_state para reutilizarse
    como ancla en las siguientes ilustraciones.

    Args:
        user_direction: Dirección personalizada del usuario para esta escena (opcional)

    Retorna (None, None) si ya se alcanzó el límite de imágenes.
    """
    if images_used >= max_images:
        return None, None

    # Combinar scene_text con user_direction si existe
    full_scene = scene_text
    if user_direction:
        full_scene = f"{scene_text}\n\nUserDirection: {user_direction}"

    if llm_provider is not None:
        if character_visual_prompt:
            # Ilustraciones 2 y 3: ancla al prompt visual de la primera
            final_prompt = build_subsequent_prompt(
                llm_provider, character_visual_prompt, full_scene
            )
        else:
            # Primera ilustración: genera y guarda el prompt visual
            final_prompt = build_first_prompt(
                llm_provider, character_description, full_scene
            )
    else:
        final_prompt = (
            f"{character_description}. Scene: {full_scene[:400]}. "
            "children's illustrated storybook, soft watercolor style, "
            "warm golden light, whimsical detailed background"
        )

    img_bytes = image_provider.generate_image(final_prompt)
    return img_bytes, final_prompt
