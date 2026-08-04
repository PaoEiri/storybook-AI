"""
Aplicación principal: cuento interactivo generado a partir de un dibujo.
UI estilo cuaderno encuadernado con dos páginas: imagen izquierda, texto derecha.
"""

import os
import base64
import io
from dotenv import load_dotenv
import streamlit as st

from providers.factory import get_llm_provider, get_image_provider
from core.character_analyzer import analyze_character
from core.context_manager import ContextManager
from core.checkpoint_controller import CheckpointController
from core import story_generator, image_generator
from utils.image_utils import validate_and_prepare_image, bytes_to_pil
from utils.stream_utils import render_stream_and_collect

load_dotenv()

def _page_r(chapter, text, placeholder=False):
    td = f'<div class="story-placeholder">{text}</div>' if placeholder else f'<div class="story-text">{text}</div>'
    return f'<div class="page-right-shell"><div class="chapter-label">📖 {chapter}</div>{td}</div>'


def _page_l(inner):
    return f'<div class="page-left-shell">{inner}</div>'

MAX_TURNS = int(os.getenv("MAX_TURNS", 3))
MAX_IMAGES = int(os.getenv("MAX_IMAGES", 3))

st.set_page_config(
    page_title="Cuentos Mágicos IA",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -----------------------------------------------------------------------
# CSS — estilo cuaderno
# -----------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Caveat:wght@400;600;700&family=Lora:ital,wght@0,400;0,600;1,400&display=swap');

/* ── Fondo app: madera oscura de librería ── */
html, body, [data-testid="stAppViewContainer"] {
    #background: #2B1A0E !important;
    font-family: 'Lora', Georgia, serif;
}
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stSidebar"] { display: none; }
.block-container { padding: 1.5rem 2rem 2rem !important; max-width: 1200px !important; }

/* ── LIBRO DE CUENTOS ── */
.notebook {
    display: flex;
    min-height: 600px;
    position: relative;
    /* Sombra de libro sobre mesa */
    filter: drop-shadow(0 12px 32px rgba(0,0,0,0.6)) drop-shadow(0 4px 8px rgba(0,0,0,0.4));
}

/* Contenedor para streaming (sin pseudo-elementos) */
.notebook-stream {
            gap:0.1rem !important ;
    display: flex;
    min-height: 600px;
    position: relative;
    filter: drop-shadow(0 12px 32px rgba(0,0,0,0.6)) drop-shadow(0 4px 8px rgba(0,0,0,0.4));
    background: linear-gradient(to right, #6B4020, #8B5A2B);
    border-radius: 2px;
    padding-left: 1px;
}

/* Lomo del libro (borde izquierdo decorativo) */
.notebook::before {
    content: '';
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 18px;
    background: linear-gradient(to right, #5C3310, #8B5A2B, #6B4020);
    border-radius: 3px 0 0 3px;
    border-top: 2px solid #A07830;
    border-bottom: 2px solid #A07830;
    z-index: 10;
    pointer-events: none;
    box-shadow: inset -3px 0 6px rgba(0,0,0,0.3);
}

/* Línea de unión entre páginas */
.notebook::after {
    content: '';
    position: absolute;
    left: 50%;
    top: 0; bottom: 0;
    width: 4px;
    transform: translateX(-50%);
    background: linear-gradient(to right, rgba(0,0,0,0.15), rgba(0,0,0,0.05), rgba(0,0,0,0.15));
    z-index: 9;
    pointer-events: none;
}

/* Página izquierda — imagen */
.page-left {
    width: 50%;
    background: linear-gradient(108deg, #F5ECD8 0%, #FBF5E6 50%, #FDF8EE 100%);
    padding: 2.5rem 2rem 2.5rem 2.8rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    border-top: 2px solid #C8A050;
    border-bottom: 2px solid #C8A050;
    border-left: 18px solid transparent; /* espacio para el lomo */
    position: relative;
    min-height: 60px;
    box-shadow: inset -8px 0 16px rgba(0,0,0,0.08);
}

/* Contenedor izquierda para streaming en columnas */
.page-left-shell {
    width: 100%;
    background: linear-gradient(108deg, #F5ECD8 0%, #FBF5E6 50%, #FDF8EE 100%);
    padding: 2.5rem 2rem 2.5rem 2.8rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    border-top: 2px solid #C8A050;
    border-bottom: 2px solid #C8A050;
    border-left: 20px solid #6B4020;
    position: relative;
    min-height: 620px;
    box-shadow: inset -8px 0 16px rgba(0,0,0,0.08);
}
/* Borde decorativo interior */
.page-left::before {
    content: '';
    position: absolute;
    inset: 12px 12px 12px 18px;
    border: 1px solid rgba(180,140,60,0.2);
    pointer-events: none;
}
.page-left::after { display: none; }
.page-left-shell::before { display: none; }
.page-left-shell::after { display: none; }

/* Página derecha — texto */
.page-right {
    width: 50%;
   gap:0.1rem !important ;
    min-height: 600px;
    background: linear-gradient(252deg, #F2E8D0 0%, #FAF3E4 50%, #FDF8EE 100%);
    padding: 2.5rem 2.5rem 2rem 2rem;
    position: relative;
    display: flex;
    flex-direction: column;
    border-top: 2px solid #C8A050;
    border-bottom: 2px solid #C8A050;
    border-right: 2px solid #C8A050;
    border-radius: 0 4px 4px 0;
    box-shadow: inset 6px 0 14px rgba(0,0,0,0.06),
                4px 0 20px rgba(0,0,0,0.3);
    overflow: hidden;
    align-self: stretch;
}

/* Contenedor derecha para streaming en columnas */
.page-right-shell {
    width: 100%;
    
    min-height: 580px;
    background: linear-gradient(252deg, #F2E8D0 0%, #FAF3E4 50%, #FDF8EE 100%);
    padding: 2.5rem 2.5rem 2rem 2rem;
    position: relative;
    display: flex;
    flex-direction: column;
    border-top: 2px solid #C8A050;
    border-bottom: 2px solid #C8A050;
    border-right: 2px solid #C8A050;
    border-radius: 0 4px 4px 0;
    box-shadow: inset 6px 0 14px rgba(0,0,0,0.06),
                4px 0 20px rgba(0,0,0,0.3),
                inset -2px 0 0 rgba(0,0,0,0.05);
    overflow: hidden;
    align-self: stretch;
              left: -14px !important ;
}
/* Borde decorativo interior */
.page-right::before {
    content: '';
    position: absolute;
    inset: 12px;
    border: 1px solid rgba(180,140,60,0.2);
    pointer-events: none;
}
.page-right::after { display: none; }
.page-right-shell::before { display: none; }
.page-right-shell::after { display: none; }

/* Texto y encabezados del libro */
.chapter-label {
    font-family: 'Caveat', cursive;
    font-size: 0.9rem;
    color: #A08040;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    margin-bottom: 0.6rem;
}
.story-placeholder {
    font-family: 'Lora', serif;
    font-size: 1rem;
    color: #A08040;
    font-style: italic;
}
.story-page-body {
    position: relative;
    z-index: 1;
}
.page-number {
    font-family: 'Lora', serif;
    font-size: 0.75rem;
    color: #A08040;
    text-align: center;
    font-style: italic;
    margin-top: auto;
    padding-top: 0.8rem;
}
.upload-card {
    background: rgba(253,248,238,0.6);
    border: 2px dashed #C8A050;
    border-radius: 8px;
    padding: 2rem;
    text-align: center;
    margin-bottom: 1rem;
    position: relative;
    z-index: 1;
}
.upload-title {
    font-family: 'Caveat', cursive;
    font-size: 1.4rem;
    color: #6B5744;
    margin-bottom: 0.5rem;
}
.upload-subtitle {
    font-family: 'Lora', serif;
    font-size: 0.9rem;
    color: #D4B896;
}
.welcome-card {
    font-family: 'Caveat', cursive;
    font-size: 1.3rem;
    color: #D4B896;
    padding-top: 2rem;
    text-align: center;
    position: relative;
    z-index: 1;
}
.welcome-icon {
    font-size: 3rem;
}
.choice-card {
    position: relative;
    z-index: 1;
}
.choice-title {
    font-family: 'Caveat', cursive;
    font-size: 1.5rem;
    color: #2C1810;
    margin-bottom: 0.8rem;
    font-weight: 700;
}
.choice-subtitle {
    font-family: 'Lora', serif;
    font-size: 0.95rem;
    color: #6B5744;
    margin-bottom: 1rem;
}
.helper-text {
    text-align: center;
    color: #D4B896;
    font-size: 0.85rem;
    margin: 0.4rem 0;
}
.completion-title {
    font-family: 'Caveat', cursive;
    font-size: 1.6rem;
    color: #E8724A;
    font-weight: 700;
    margin-bottom: 0.8rem;
}

/* Título del libro */
.notebook-title {
    font-family: 'Lora', serif;
    font-size: 2rem;
    font-weight: 700;
    color: #D4A853;
    text-align: center;
    margin-bottom: 1.2rem;
    letter-spacing: 0.04em;
    text-shadow: 0 2px 8px rgba(0,0,0,0.5);
}

/* Ornamento de capítulo */
.chapter-ornament {
    font-family: 'Lora', serif;
    font-size: 0.65rem;
    color: #A08040;
    letter-spacing: 0.3em;
    text-transform: uppercase;
    text-align: center;
    margin-bottom: 0.3rem;
    position: relative;
    z-index: 1;
}

/* Imagen del dibujo/ilustración */
.drawing-frame {
    border: 3px solid #D4C8A8;
            gap:    0.1rem !important ;
    border-radius: 6px;
    overflow: hidden;
    box-shadow: 2px 3px 10px rgba(0,0,0,0.15);
    background: inherit;
    position: relative;
    z-index: 1;
    min-height: 580px;
    width: 100%;


}
.drawing-frame img { width: 100%; display: block;   }

.drawing-caption {
    font-family: 'Caveat', cursive;
    font-size: 1.1rem;
    color: #6B5744;
    text-align: center;
    margin-top: 0.8rem;
    position: relative;
    z-index: 1;
}

/* Texto de la historia */
.story-text {
    font-family: 'Lora', serif;
    font-size: 1.05rem;
    line-height: 2.0rem;
    color: #2C1810;
    position: relative;
    z-index: 1;
    flex: 1;
    width: 100%;
    background: inherit;
    display: block;
}
.story-text p { margin-bottom: 0.6rem; }

/* Zona de decisión */
.decision-zone {
    margin-top: 1.2rem;
    padding-top: 1rem;
    border-top: 1px dashed #B8A898;
    position: relative;
    z-index: 1;
    background: inherit;
}
.decision-label {
    font-family: 'Caveat', cursive;
    font-size: 1.2rem;
    color: #6B5744;
    margin-bottom: 0.6rem;
    font-weight: 600;
}

/* Upload zone */
.upload-zone {
    background: rgba(253,248,238,0.6);
    border: 2px dashed #C8A050;
    border-radius: 8px;
    padding: 2rem;
    text-align: center;
    margin-bottom: 1rem;
    position: relative;
    z-index: 1;
}

/* Botones principales */
.stButton > button {
    font-family: 'Caveat', cursive !important;
    font-size: 1.1rem !important;
    font-weight: 600 !important;
    border-radius: 4px !important;
    padding: 0.4rem 1.2rem !important;
    transition: all 0.15s ease !important;
}
.stButton > button[kind="primary"] {
    background: #E8724A !important;
    border: none !important;
    color: white !important;
}
.stButton > button[kind="primary"]:hover {
    background: #D45A32 !important;
    transform: translateY(-1px);
    box-shadow: 0 3px 8px rgba(232,114,74,0.4) !important;
}
.stButton > button[kind="secondary"] {
    background: rgba(253,248,238,0.8) !important;
    border: 1.5px solid #C8A050 !important;
    color: #4A2E18 !important;
}
.stButton > button[kind="secondary"]:hover {
    background: #F0E8D0 !important;
    border-color: #A89878 !important;
}

/* Input de texto */
.stTextInput > div > div > input, .stTextArea textarea {
    font-family: 'Lora', serif !important;
    background: rgba(255,255,255,0.85) !important;
    border: 1px solid #C8A050 !important;
    border-radius: 4px !important;
    color: #3A2010 !important;
}
.stTextInput label, .stTextArea label {
    color: #E8C890 !important;
    font-family: 'Lora', serif !important;
}
.stCaption { color: #C8A870 !important; }

/* Ocultar elementos de Streamlit que sobran */
#MainMenu, footer, [data-testid="stToolbar"] { visibility: hidden; }
[data-testid="stFileUploaderDropzone"] {
    background: rgba(253,248,238,0.7) !important;
    border-color: #C8A050 !important;
}

/* Placeholder de imagen */
.img-placeholder {
    width: 100%;
    max-width: 340px;
    aspect-ratio: 1;
    background: linear-gradient(135deg, #F0E8D8 0%, #E8DCC8 100%);
    border: 2px dashed #C8B89A;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-direction: column;
    gap: 0.5rem;
    color: #A89878;
    font-family: 'Caveat', cursive;
    font-size: 1.1rem;
    position: relative;
    z-index: 1;
}

/* Chip de turno */
.turn-chip {
    display: inline-block;
    background: #E8724A;
    color: white;
    font-family: 'Caveat', cursive;
    font-size: 0.9rem;
    padding: 0.1rem 0.6rem;
    border-radius: 20px;
    margin-bottom: 0.5rem;
}

/* Alternativas de historia */
.alt-card {
    background: rgba(255,255,255,0.6);
    border: 1px solid #D4C8A8;
    border-radius: 6px;
    padding: 0.7rem 1rem;
    margin-bottom: 0.6rem;
    cursor: pointer;
    transition: all 0.15s;
    font-family: 'Lora', serif;
    font-size: 0.92rem;
    color: #2C1810;
    position: relative;
    z-index: 1;
}
.alt-card:hover { background: rgba(232,114,74,0.08); border-color: #E8724A; }

</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------
def img_to_b64(img_bytes: bytes) -> str:
    return base64.b64encode(img_bytes).decode()

def pil_to_bytes(pil_img) -> bytes:
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    return buf.getvalue()

def generate_checkpoint_question(llm_provider, story_text: str, character_description: str) -> tuple[str, str, str]:
    """
    Usa el LLM para generar una pregunta narrativa concreta con dos opciones,
    basada en el punto de tensión donde terminó el fragmento de historia.
    Devuelve (pregunta, opción_A, opción_B).
    """
    prompt = (
        f"El personaje es: {character_description}\n\n"
        f"El cuento ha llegado a este punto:\n{story_text[-600:]}\n\n"
        "Genera una pregunta narrativa emocionante con DOS opciones concretas para que "
        "el lector elija cómo continúa la historia. "
        "La pregunta debe ser específica al momento de la historia, no genérica. "
        "Ejemplo: '¿Debería el dragoncito entrar al bosque oscuro o seguir el río brillante?'\n\n"
        "Responde EXACTAMENTE en este formato (3 líneas, sin nada más):\n"
        "PREGUNTA: [pregunta aquí]\n"
        "A: [opción A aquí]\n"
        "B: [opción B aquí]"
    )
    raw = ""
    for chunk in llm_provider.stream_story([{"role": "user", "content": prompt}]):
        raw += chunk

    question = "¿Qué debería hacer el personaje?"
    opt_a = "Seguir adelante con valentía"
    opt_b = "Buscar otro camino"

    for line in raw.strip().split("\n"):
        line = line.strip()
        if line.startswith("PREGUNTA:"):
            question = line[len("PREGUNTA:"):].strip()
        elif line.startswith("A:"):
            opt_a = line[2:].strip()
        elif line.startswith("B:"):
            opt_b = line[2:].strip()

    return question, opt_a, opt_b


def render_notebook(left_html: str, right_html: str):
    st.markdown(f"""
    <div class="notebook">
        <div class="page-left">{left_html}</div>
        <div class="page-right">{right_html}</div>
    </div>
    """, unsafe_allow_html=True)


# -----------------------------------------------------------------------
# Helper: popup de error de proveedor de IA
# -----------------------------------------------------------------------
def show_provider_error(exc: Exception):
    message = str(exc).lower()
    is_limit_error = any(
        token in message
        for token in ["429", "quota", "rate limit", "exhausted", "token", "tokens", "context length", "maximum context", "too many tokens"]
    )

    if is_limit_error:
        st.error(
            "### ⚠️ La API de IA no pudo completar la petición\n\n"
            "Esto puede deberse a un límite de cuota, de tokens o a un problema temporal del proveedor. "
            "Prueba de nuevo en unos segundos y revisa que tu API key y el modelo configurado sean correctos.\n\n"
            "_La historia quedó guardada hasta este punto. Recarga la página para reintentar._"
        )
    else:
        st.error(
            f"### ⚠️ Error al generar la historia\n\n"
            f"{exc}\n\n"
            "Comprueba tu conexión, tu API key y el modelo configurado."
        )
    st.stop()


# -----------------------------------------------------------------------
# Estado de sesión
# -----------------------------------------------------------------------
def init_session():
    defaults = {
        "stage": "upload",
        "character_description": None,
        "context": None,
        "checkpoint": None,
        "current_illustration": None,   # bytes de la ilustración activa
        "character_visual_prompt": None,  # prompt visual de la 1ª ilustración (ancla)
        "current_story_text": "",        # texto del fragmento activo
        "uploaded_drawing": None,        # bytes del dibujo original
        "uploaded_drawing_mime": "image/png",
        "story_started": False,
        "awaiting_choice": False,        # True cuando hay que mostrar opciones
        "story_options": [],             # opciones generadas por el LLM
        "story_question": "",            # pregunta narrativa del checkpoint
        "story_choice_a": "",            # opción A generada por LLM
        "story_choice_b": "",            # opción B generada por LLM
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()

# Providers (se instancian una vez por sesión)
if "llm_provider" not in st.session_state:
    try:
        st.session_state.llm_provider = get_llm_provider()
        st.session_state.image_provider = get_image_provider()
    except ValueError as e:
        st.error(f"Error de configuración: {e}")
        st.stop()

# -----------------------------------------------------------------------
# Título
# -----------------------------------------------------------------------
st.markdown('<h1 class="notebook-title">Libro de Cuentos Mágicos</h1>', unsafe_allow_html=True)


# -----------------------------------------------------------------------
# ETAPA 1 — Subida del dibujo (layout cuaderno vacío)
# -----------------------------------------------------------------------
if st.session_state.stage == "upload":

    # Página izquierda: uploader
    left = """
    <div class="upload-card">
        <div class="upload-title">🖍️ Sube tu dibujo aquí</div>
        <div class="upload-subtitle">Foto o escaneo de tu personaje favorito</div>
    </div>
    """
    right = """
    <div class="welcome-card">
        Tu historia aparecerá aquí...
        <br/><br/>
        <span class="welcome-icon">✨</span>
    </div>
    """

    # Renderizamos el cuaderno visualmente
    render_notebook(left, right)

    # Los widgets de Streamlit van FUERA del HTML (Streamlit los maneja aparte)
    st.markdown("<br/>", unsafe_allow_html=True)
    col_up, col_btn, col_empty = st.columns([2, 1.2, 2])

    with col_up:
        uploaded = st.file_uploader(
            "Elige una imagen",
            type=["png", "jpg", "jpeg", "webp"],
            label_visibility="collapsed",
        )

    if uploaded:
        img_bytes, mime = validate_and_prepare_image(uploaded)
        st.session_state.uploaded_drawing = img_bytes
        st.session_state.uploaded_drawing_mime = mime

        with col_btn:
            if st.button("✨ Crear historia", type="primary", use_container_width=True):
                with st.spinner("Observando tu dibujo..."):
                    desc = analyze_character(
                        st.session_state.llm_provider,
                        img_bytes,
                        mime,
                    )
                st.session_state.character_description = desc
                st.session_state.context = ContextManager(desc)
                st.session_state.checkpoint = CheckpointController(
                    max_turns=MAX_TURNS, max_images=MAX_IMAGES
                )
                st.session_state.stage = "choose_opening"
                st.rerun()


# -----------------------------------------------------------------------
# ETAPA 2 — Elegir cómo empieza la historia (3 alternativas)
# -----------------------------------------------------------------------
if st.session_state.stage == "choose_opening":

    drawing_b64 = img_to_b64(st.session_state.uploaded_drawing)
    left_html = f"""
    <div class="drawing-frame">
        <img src="data:{st.session_state.uploaded_drawing_mime};base64,{drawing_b64}" alt="tu dibujo"/>
    </div>
    <div class="drawing-caption">🖍️ Tu personaje</div>
    <div style="font-family:'Lora',serif;font-size:0.85rem;color:#7B6754;
                margin-top:1rem;text-align:center;position:relative;z-index:1;
                max-width:300px;">
        {st.session_state.character_description}
    </div>
    """

    right_html = """
    <div class="choice-card">
        <div class="choice-title">¿Cómo empieza la aventura?</div>
        <div class="choice-subtitle">Elige una de estas dos ideas para comenzar, o escribe la tuya:</div>
    </div>
    """
    render_notebook(left_html, right_html)

    # Generar 3 opciones de inicio si no existen aún
    if not st.session_state.story_options:
        with st.spinner("Imaginando posibles aventuras..."):
            options_prompt = (
                f"El personaje es: {st.session_state.character_description}\n\n"
                "Genera exactamente 2 frases de inicio para un libro de cuentos ilustrado. "
                "Cada una en un escenario completamente distinto y mágico. "
                "El tono debe ser poético y evocador, como el inicio de un libro clásico para niños. "
                "Devuelve SOLO las 2 opciones numeradas así:\n"
                "1. [frase]\n2. [frase]\n"
                "Una línea por opción, en español."
            )
            raw = ""
            for chunk in st.session_state.llm_provider.stream_story([
                {"role": "user", "content": options_prompt}
            ]):
                raw += chunk
            lines = [l.strip() for l in raw.split("\n") if l.strip()]
            options = []
            for l in lines:
                for prefix in ["1.", "2."]:
                    if l.startswith(prefix):
                        options.append(l[len(prefix):].strip())
            if len(options) < 2:
                options = [
                    "En un bosque encantado donde los árboles susurraban secretos antiguos...",
                    "En el fondo del mar más azul y brillante del mundo...",
                ]
            st.session_state.story_options = options[:2]
            st.rerun()

    st.markdown("<br/>", unsafe_allow_html=True)
    _, col_opts, _ = st.columns([0.3, 3, 0.3])

    with col_opts:
        for i, opt in enumerate(st.session_state.story_options):
            emoji = ["🌲", "🌊"][i]
            if st.button(f"{emoji}  {opt}", key=f"opt_{i}", use_container_width=True):
                st.session_state.stage = "opening"
                st.session_state.chosen_opening = opt
                st.rerun()

        st.markdown("<br/>", unsafe_allow_html=True)
        custom = st.text_input(
            "✍️ O escribe tu propia idea de comienzo:",
            placeholder="Había una vez, en un volcán que escupía caramelos...",
            label_visibility="visible",
        )
        if st.button("Usar mi idea ✨", type="primary"):
            if custom.strip():
                st.session_state.stage = "opening"
                st.session_state.chosen_opening = custom.strip()
                st.rerun()


# -----------------------------------------------------------------------
# ETAPA 3 — Generar apertura de la historia
# -----------------------------------------------------------------------
if st.session_state.stage == "opening":

    drawing_b64 = img_to_b64(st.session_state.uploaded_drawing)

    # Página izquierda: dibujo original mientras se genera la ilustración
    left_html = f"""
    <div class="drawing-frame">
        <img src="data:{st.session_state.uploaded_drawing_mime};base64,{drawing_b64}" alt="tu personaje"/>
    </div>
    <div class="drawing-caption">🖍️ Tu personaje</div>
    """
    # Streaming dentro del libro: col izquierda=imagen, col derecha=texto en vivo
    col_l_a, col_r_a = st.columns([1, 1], gap="small")
    with col_l_a:
        st.markdown(f'<div class="page-left-shell">{left_html}</div>', unsafe_allow_html=True)
    with col_r_a:
        stream_slot = st.empty()
        stream_slot.markdown(
            '<div class="page-right-shell">'
            '<div class="chapter-label">📖 Capítulo I</div>'
            '<div class="story-placeholder">Escribiendo tu historia...</div>'
            '</div>',
            unsafe_allow_html=True
        )

    # Streaming del texto
    opening_user_msg = (
        f"Comienza la historia con este arranque elegido por el lector: "
        f'"{ st.session_state.chosen_opening}". '
        "Desarrolla las primeras páginas del cuento (80-150 palabras) y termina "
        "en un punto de tensión, sin formular aún la pregunta al usuario."
    )
    st.session_state.context.add_user_turn(opening_user_msg)

    try:
        full_text = ""
        for chunk in st.session_state.llm_provider.stream_story(
            st.session_state.context.get_messages()
        ):
            full_text += chunk
            stream_slot.markdown(
                f'<div class="page-right-shell">'
                f'<div class="chapter-label">📖 Capítulo I</div>'
                f'<div class="story-text">{full_text}</div></div>',
                unsafe_allow_html=True
            )
    except Exception as e:
        show_provider_error(e)

    st.session_state.context.add_assistant_turn(full_text)
    st.session_state.current_story_text = full_text

    # Generar pregunta narrativa con opciones A/B
    with st.spinner("📖 Preparando el siguiente momento de la historia..."):
        try:
            q, a, b = generate_checkpoint_question(
                st.session_state.llm_provider,
                full_text,
                st.session_state.character_description,
            )
            st.session_state.story_question = q
            st.session_state.story_choice_a = a
            st.session_state.story_choice_b = b
        except Exception as e:
            show_provider_error(e)

    # Generar ilustración (primera — guarda el prompt visual como ancla)
    with st.spinner("🎨 Creando la primera ilustración del personaje..."):
        if st.session_state.checkpoint.should_generate_image_for_stage("opening"):
            img_bytes, vis_prompt = image_generator.generate_illustration(
                st.session_state.image_provider,
                st.session_state.character_description,
                full_text,
                st.session_state.checkpoint.images_used,
                st.session_state.checkpoint.max_images,
                llm_provider=st.session_state.llm_provider,
                character_visual_prompt=None,  # primera vez: sin ancla
            )
            if img_bytes:
                st.session_state.current_illustration = img_bytes
                st.session_state.character_visual_prompt = vis_prompt  # guardar ancla
                st.session_state.checkpoint.register_image_used()

    st.session_state.stage = "turn"
    st.rerun()


# -----------------------------------------------------------------------
# ETAPA 4 — Turno interactivo (muestra cuaderno + recibe mensaje)
# -----------------------------------------------------------------------
if st.session_state.stage == "turn":
    checkpoint = st.session_state.checkpoint

    if checkpoint.is_story_finished():
        st.session_state.stage = "conclusion"
        st.rerun()

    # Página izquierda: ilustración generada (o dibujo si no hay aún)
    if st.session_state.current_illustration:
        ill_b64 = img_to_b64(st.session_state.current_illustration)
        left_html = f"""
        <div class="drawing-frame">
            <img src="data:image/png;base64,{ill_b64}" alt="ilustración"/>
        </div>
        <div class="drawing-caption">✨ Ilustración generada por IA</div>
        """
    else:
        drawing_b64 = img_to_b64(st.session_state.uploaded_drawing)
        left_html = f"""
        <div class="drawing-frame">
            <img src="data:{st.session_state.uploaded_drawing_mime};base64,{drawing_b64}" alt="personaje"/>
        </div>
        <div class="drawing-caption">🖍️ Tu personaje</div>
        """

    turn_num = checkpoint.current_turn + 1
    turns_left = checkpoint.turns_remaining()

    story_html = st.session_state.current_story_text.replace(chr(10), "<br/>")
    question   = st.session_state.get("story_question", "¿Qué debería hacer el personaje?")
    choice_a   = st.session_state.get("story_choice_a", "Seguir adelante")
    choice_b   = st.session_state.get("story_choice_b", "Buscar otro camino")

    right_html = f"""
    <div class="story-page-body">
        <div class="turn-chip">Capítulo {turn_num}
            <span class="turn-count">
                &nbsp;·&nbsp;{turns_left} {'página' if turns_left==1 else 'páginas'} más
            </span>
        </div>
        <div class="story-text">{story_html}</div>
    </div>
    <div class="decision-zone">
        <div class="decision-label">✨ {question}</div>
    </div>
    """

    render_notebook(left_html, right_html)

    # Botones A/B + campo libre debajo del libro
    st.markdown("<br/>", unsafe_allow_html=True)
    _, col_input, _ = st.columns([0.3, 3, 0.3])

    with col_input:
        col_a, col_b = st.columns(2)
        chosen = None
        with col_a:
            if st.button(f"🅰️  {choice_a}", key=f"btn_a_{turn_num}", use_container_width=True, type="primary"):
                chosen = choice_a
        with col_b:
            if st.button(f"🅱️  {choice_b}", key=f"btn_b_{turn_num}", use_container_width=True, type="primary"):
                chosen = choice_b

        st.markdown("<div class='helper-text'>— o escribe tu propia idea —</div>", unsafe_allow_html=True)
        col_txt, col_send = st.columns([3, 1])
        with col_txt:
            custom = st.text_input("Tu idea", placeholder="Describe tu propia dirección para la historia...",
                                   key=f"user_turn_{turn_num}", label_visibility="collapsed")
        with col_send:
            send_custom = st.button("Continuar ➜", key=f"send_{turn_num}", use_container_width=True)

    if chosen:
        st.session_state.stage = "continuing"
        st.session_state.user_message = chosen
        checkpoint.register_turn()
        st.rerun()

    if send_custom and custom.strip():
        st.session_state.stage = "continuing"
        st.session_state.user_message = custom.strip()
        checkpoint.register_turn()
        st.rerun()


# -----------------------------------------------------------------------
# ETAPA 5 — Generando continuación
# -----------------------------------------------------------------------
if st.session_state.stage == "continuing":

    # Mostrar ilustración anterior mientras se genera
    if st.session_state.current_illustration:
        ill_b64 = img_to_b64(st.session_state.current_illustration)
        left_html = f"""
        <div class="drawing-frame">
            <img src="data:image/png;base64,{ill_b64}" alt="ilustración"/>
        </div>
        <div class="drawing-caption">✨ Escena anterior</div>
        """
    else:
        drawing_b64 = img_to_b64(st.session_state.uploaded_drawing)
        left_html = f"""
        <div class="drawing-frame">
            <img src="data:{st.session_state.uploaded_drawing_mime};base64,{drawing_b64}" alt="personaje"/>
        </div>
        """

    tn_lbl = st.session_state.checkpoint.current_turn
    col_l_c, col_r_c = st.columns([1, 1], gap="small")
    with col_l_c:
        st.markdown(f'<div class="page-left-shell">{left_html}</div>', unsafe_allow_html=True)
    with col_r_c:
        stream_slot_c = st.empty()
        stream_slot_c.markdown(
            f'<div class="page-right-shell">'
            f'<div class="chapter-label">📖 Capítulo {tn_lbl}</div>'
            '<div class="story-placeholder">Continuando la historia...</div>'
            '</div>',
            unsafe_allow_html=True
        )

    try:
        full_text = ""
        for chunk in story_generator.stream_continuation(
            st.session_state.llm_provider,
            st.session_state.context,
            st.session_state.user_message,
        ):
            full_text += chunk
            stream_slot_c.markdown(
                f'<div class="page-right-shell">'
                f'<div class="chapter-label">📖 Capítulo {tn_lbl}</div>'
                f'<div class="story-text">{full_text}</div></div>',
                unsafe_allow_html=True
            )
    except Exception as e:
        show_provider_error(e)

    st.session_state.context.add_assistant_turn(full_text)
    st.session_state.current_story_text = full_text

    # Generar nueva pregunta narrativa (si no es el último turno)
    if not st.session_state.checkpoint.is_story_finished():
        with st.spinner("📖 Preparando el siguiente momento de la historia..."):
            q, a, b = generate_checkpoint_question(
                st.session_state.llm_provider,
                full_text,
                st.session_state.character_description,
            )
            st.session_state.story_question = q
            st.session_state.story_choice_a = a
            st.session_state.story_choice_b = b

    # Nueva ilustración (reutiliza el prompt visual de la primera como ancla)
    with st.spinner("🎨 Ilustrando la nueva escena..."):
        if st.session_state.checkpoint.should_generate_image_for_stage("continuing"):
            try:
                img_bytes, vis_prompt = image_generator.generate_illustration(
                    st.session_state.image_provider,
                    st.session_state.character_description,
                    full_text,
                    st.session_state.checkpoint.images_used,
                    st.session_state.checkpoint.max_images,
                    llm_provider=st.session_state.llm_provider,
                    character_visual_prompt=st.session_state.get('character_visual_prompt'),
                    user_direction=st.session_state.get('user_message'),
                )
                if img_bytes:
                    st.session_state.current_illustration = img_bytes
                    st.session_state.checkpoint.register_image_used()
            except Exception as e:
                show_provider_error(e)

    st.session_state.stage = "turn"
    st.rerun()


# -----------------------------------------------------------------------
# ETAPA 6 — Conclusión
# -----------------------------------------------------------------------
if st.session_state.stage == "conclusion":

    if st.session_state.current_illustration:
        ill_b64 = img_to_b64(st.session_state.current_illustration)
        left_html = f"""
        <div class="drawing-frame">
            <img src="data:image/png;base64,{ill_b64}" alt="ilustración final"/>
        </div>
        <div class="drawing-caption">🌟 Escena final</div>
        """
    else:
        drawing_b64 = img_to_b64(st.session_state.uploaded_drawing)
        left_html = f"""
        <div class="drawing-frame">
            <img src="data:{st.session_state.uploaded_drawing_mime};base64,{drawing_b64}"/>
        </div>
        """

    col_l_cl, col_r_cl = st.columns([1, 1], gap="small")
    with col_l_cl:
        st.markdown(f'<div class="page-left-shell">{left_html}</div>', unsafe_allow_html=True)
    with col_r_cl:
        stream_slot_cl = st.empty()
        stream_slot_cl.markdown(
            '<div class="page-right-shell">'
            '<div class="chapter-label">📖 El Final</div>'
            '<div class="story-placeholder">Escribiendo el final...</div>'
            '</div>',
            unsafe_allow_html=True
        )

    try:
        full_text = ""
        for chunk in story_generator.stream_conclusion(
            st.session_state.llm_provider,
            st.session_state.context,
        ):
            full_text += chunk
            stream_slot_cl.markdown(
               
                f'<div class="page-right-shell">'
                f'<div class="chapter-label">📖 Final </div>'
                f'<div class="story-text">{full_text}</div></div>',
                unsafe_allow_html=True
            )
    except Exception as e:
        show_provider_error(e)

    st.session_state.context.add_assistant_turn(full_text)
    st.session_state.current_story_text = full_text

    with st.spinner("🎨 Analizando escena y generando ilustración final..."):
        if st.session_state.checkpoint.should_generate_image_for_stage("conclusion"):
            img_bytes, _ = image_generator.generate_illustration(
                st.session_state.image_provider,
                st.session_state.character_description,
                full_text,
                st.session_state.checkpoint.images_used,
                st.session_state.checkpoint.max_images,
                llm_provider=st.session_state.llm_provider,
                character_visual_prompt=st.session_state.get('character_visual_prompt'),
            )
            if img_bytes:
                st.session_state.current_illustration = img_bytes
                st.session_state.checkpoint.register_image_used()

    st.session_state.stage = "finished"
    st.rerun()


# -----------------------------------------------------------------------
# ETAPA 7 — Fin
# -----------------------------------------------------------------------
if st.session_state.stage == "finished":

    if st.session_state.current_illustration:
        ill_b64 = img_to_b64(st.session_state.current_illustration)
        left_html = f"""
        <div class="drawing-frame">
            <img src="data:image/png;base64,{ill_b64}" alt="ilustración final"/>
        </div>
        <div class="drawing-caption">🌟 Fin de la historia</div>
        """
    else:
        drawing_b64 = img_to_b64(st.session_state.uploaded_drawing)
        left_html = f"""
        <div class="drawing-frame">
            <img src="data:{st.session_state.uploaded_drawing_mime};base64,{drawing_b64}"/>
        </div>
        <div class="drawing-caption">🌟 Fin de la historia</div>
        """

    right_html = f"""
    <div class="story-page-body">
        <div class="completion-title">🎉 ¡Historia completada!</div>
        <div class="story-text">
            {st.session_state.current_story_text.replace(chr(10), "<br/>")}
        </div>
    </div>
    """

    render_notebook(left_html, right_html)

    st.markdown("<br/>", unsafe_allow_html=True)
    _, col_btn, _ = st.columns([1, 1, 1])
    with col_btn:
        if st.button("✨ Crear una nueva historia", type="primary", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
