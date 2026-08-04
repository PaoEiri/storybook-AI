"""
Helpers para conectar generadores de texto en streaming con la UI de
Streamlit, y para acumular el texto final una vez completado el stream.
"""

from typing import Generator


def render_stream_and_collect(container, stream: Generator[str, None, None]) -> str:
    """
    Renderiza progresivamente un generador de texto dentro de un
    contenedor de Streamlit (st.empty() o similar) y devuelve el texto
    completo acumulado al finalizar, para poder guardarlo en el historial.
    """
    accumulated = ""
    for chunk in stream:
        accumulated += chunk
        container.markdown(accumulated)
    return accumulated
