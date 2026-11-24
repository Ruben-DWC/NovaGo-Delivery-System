import re
import unicodedata
from functools import lru_cache
from pathlib import Path

FAQ_PATH = Path(__file__).resolve().parent.parent / 'data' / 'faq_novago.md'

TOPIC_ALIASES = {
    'pagos': ('pago', 'pagar', 'yape', 'plin', 'efectivo', 'tarjeta', 'transferencia', 'pos', 'metodo'),
    'envio': ('envio', 'delivery', 'costo', 'tarifa', 'precio envio', 'gratis', 'demora', 'tiempo', 'eta'),
    'zonas': ('zona', 'cobertura', 'lima', 'distrito', 'alcance', 'llegan', 'radio'),
    'horarios': ('horario', 'hora', 'abierto', 'atienden', 'cierra', 'domingo', 'feriado'),
    'cancelaciones': ('cancelar', 'cancelacion', 'anular', 'devolucion'),
}


def _normalizar(texto: str) -> str:
    nfkd = unicodedata.normalize('NFKD', (texto or '').lower())
    return ''.join(ch for ch in nfkd if not unicodedata.combining(ch)).strip()


@lru_cache(maxsize=1)
def cargar_secciones_faq() -> dict[str, str]:
    """Carga las secciones ## del archivo faq_novago.md."""
    if not FAQ_PATH.exists():
        return {}
    contenido = FAQ_PATH.read_text(encoding='utf-8')
    secciones: dict[str, str] = {}
    titulo_actual: str | None = None
    buffer: list[str] = []

    for linea in contenido.splitlines():
        match = re.match(r'^##\s+(.+)$', linea.strip())
        if match:
            if titulo_actual is not None:
                secciones[titulo_actual] = '\n'.join(buffer).strip()
            titulo_actual = match.group(1).strip()
            buffer = []
        elif titulo_actual is not None:
            buffer.append(linea)

    if titulo_actual is not None:
        secciones[titulo_actual] = '\n'.join(buffer).strip()

    return secciones


def buscar_faq(tema: str = '') -> dict[str, str]:
    """Retorna la sección más relevante del FAQ según el tema consultado."""
    secciones = cargar_secciones_faq()
    if not secciones:
        return {
            'tema': 'general',
            'contenido': 'En NovaGo aceptamos Yape, Plin y Efectivo. El envío cuesta S/ 5.00 en Lima Metropolitana.',
        }

    tema_norm = _normalizar(tema)
    if tema_norm:
        coincidencias: list[tuple[str, str]] = []
        vistos: set[str] = set()

        for titulo, texto in secciones.items():
            if _normalizar(titulo) in tema_norm or tema_norm in _normalizar(titulo):
                coincidencias.append((titulo, texto))
                vistos.add(titulo)

        for clave_alias, palabras in TOPIC_ALIASES.items():
            if any(p in tema_norm for p in palabras):
                for titulo, texto in secciones.items():
                    if titulo not in vistos and (
                        _normalizar(titulo) == clave_alias or clave_alias in _normalizar(titulo)
                    ):
                        coincidencias.append((titulo, texto))
                        vistos.add(titulo)

        if coincidencias:
            return {
                'tema': ', '.join(t for t, _ in coincidencias),
                'contenido': ' '.join(txt for _, txt in coincidencias),
            }

    resumen = ' '.join(f"{titulo}: {texto}" for titulo, texto in secciones.items())
    return {'tema': 'general', 'contenido': resumen}
