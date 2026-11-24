import json
import os
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any, Optional

import requests
from django.conf import settings


class LLMNoDisponible(Exception):
    """Se lanza cuando el proveedor LLM no está configurado, falla o no responde."""


@dataclass
class LlamadaHerramienta:
    id: str
    nombre: str
    argumentos: dict[str, Any] = field(default_factory=dict)
    thought_signature: str = ''


@dataclass
class RespuestaLLM:
    texto: str = ''
    llamadas: list[LlamadaHerramienta] = field(default_factory=list)
    proveedor: str = ''
    modelo: str = ''
    raw: Any = None


def _get_setting(name: str, default: str = '') -> str:
    val = getattr(settings, name, None)
    if val is None or val == '':
        val = os.environ.get(name, default)
    return str(val or default).strip()


def _normalize(text: str) -> str:
    nfkd = unicodedata.normalize('NFKD', (text or '').lower())
    return ''.join(ch for ch in nfkd if not unicodedata.combining(ch)).strip()


def generar(
    mensajes: list[dict[str, Any]],
    herramientas: Optional[list[dict[str, Any]]] = None,
    system_prompt: str = '',
) -> RespuestaLLM:
    """
    Cliente unificado multi-proveedor para Nova IA.
    Soporta NOVA_AI_PROVIDER: 'gemini' (default), 'anthropic', 'openai', 'fake'.
    """
    provider = _get_setting('NOVA_AI_PROVIDER', 'gemini').lower()
    model = _get_setting('NOVA_AI_MODEL', '')
    api_key = _get_setting('NOVA_AI_API_KEY', '') or _get_setting('GEMINI_API_KEY', '')
    tools = herramientas or []

    if provider == 'fake':
        return _generar_fake(mensajes, tools, system_prompt)

    if not api_key:
        raise LLMNoDisponible(f'Falta NOVA_AI_API_KEY para el proveedor {provider}.')

    if provider == 'gemini':
        return _generar_gemini(mensajes, tools, system_prompt, model or 'gemini-3.5-flash-lite', api_key)
    if provider == 'anthropic':
        return _generar_anthropic(mensajes, tools, system_prompt, model or 'claude-3-5-haiku-latest', api_key)
    if provider == 'openai':
        return _generar_openai(mensajes, tools, system_prompt, model or 'gpt-4o-mini', api_key)

    raise LLMNoDisponible(f'Proveedor LLM no soportado: {provider}.')


def _generar_gemini(
    mensajes: list[dict[str, Any]],
    herramientas: list[dict[str, Any]],
    system_prompt: str,
    model: str,
    api_key: str,
) -> RespuestaLLM:
    contents = []
    for msg in mensajes:
        role = msg.get('role')
        if role == 'user':
            contents.append({'role': 'user', 'parts': [{'text': str(msg.get('content', ''))}]})
        elif role == 'assistant':
            parts = []
            if msg.get('content'):
                parts.append({'text': str(msg['content'])})
            for call in msg.get('tool_calls', []):
                fc_part: dict[str, Any] = {
                    'functionCall': {'name': call['nombre'], 'args': call.get('argumentos', {})}
                }
                if call.get('thought_signature'):
                    fc_part['thoughtSignature'] = call['thought_signature']
                parts.append(fc_part)
            if parts:
                contents.append({'role': 'model', 'parts': parts})
        elif role == 'tool':
            contents.append({
                'role': 'user',
                'parts': [{
                    'functionResponse': {
                        'name': msg.get('name', ''),
                        'response': msg.get('content', {}),
                    }
                }],
            })

    payload: dict[str, Any] = {
        'contents': contents,
        'generationConfig': {'temperature': 0.3},
    }
    if system_prompt:
        payload['systemInstruction'] = {'parts': [{'text': system_prompt}]}
    if herramientas:
        payload['tools'] = [{'functionDeclarations': herramientas}]

    url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'
    try:
        resp = requests.post(
            url,
            params={'key': api_key},
            json=payload,
            timeout=30,
        )
    except requests.RequestException as exc:
        raise LLMNoDisponible(f'Error de red con Gemini: {exc}') from exc

    if resp.status_code >= 400:
        raise LLMNoDisponible(f'Gemini HTTP {resp.status_code}: {resp.text[:200]}')

    data = resp.json()
    candidates = data.get('candidates') or []
    if not candidates:
        raise LLMNoDisponible('Gemini no devolvió candidatos.')

    parts = candidates[0].get('content', {}).get('parts', [])
    textos = []
    llamadas = []
    for idx, part in enumerate(parts):
        if 'text' in part:
            textos.append(part['text'])
        if 'functionCall' in part:
            fc = part['functionCall']
            llamadas.append(
                LlamadaHerramienta(
                    id=f'gemini_call_{idx}',
                    nombre=fc.get('name', ''),
                    argumentos=fc.get('args') or {},
                    thought_signature=part.get('thoughtSignature', ''),
                )
            )

    return RespuestaLLM(
        texto='\n'.join(textos).strip(),
        llamadas=llamadas,
        proveedor='gemini',
        modelo=model,
        raw=data,
    )


def _generar_anthropic(
    mensajes: list[dict[str, Any]],
    herramientas: list[dict[str, Any]],
    system_prompt: str,
    model: str,
    api_key: str,
) -> RespuestaLLM:
    anthropic_msgs = []
    for msg in mensajes:
        role = msg.get('role')
        if role == 'user':
            anthropic_msgs.append({'role': 'user', 'content': str(msg.get('content', ''))})
        elif role == 'assistant':
            blocks = []
            if msg.get('content'):
                blocks.append({'type': 'text', 'text': str(msg['content'])})
            for call in msg.get('tool_calls', []):
                blocks.append({
                    'type': 'tool_use',
                    'id': call['id'],
                    'name': call['nombre'],
                    'input': call.get('argumentos', {}),
                })
            if blocks:
                anthropic_msgs.append({'role': 'assistant', 'content': blocks})
        elif role == 'tool':
            anthropic_msgs.append({
                'role': 'user',
                'content': [{
                    'type': 'tool_result',
                    'tool_use_id': msg.get('tool_call_id', ''),
                    'content': json.dumps(msg.get('content', {}), ensure_ascii=False),
                }],
            })

    payload: dict[str, Any] = {
        'model': model,
        'max_tokens': 512,
        'messages': anthropic_msgs,
    }
    if system_prompt:
        payload['system'] = system_prompt
    if herramientas:
        payload['tools'] = [
            {
                'name': h['name'],
                'description': h.get('description', ''),
                'input_schema': h.get('parameters', {'type': 'object', 'properties': {}}),
            }
            for h in herramientas
        ]

    try:
        resp = requests.post(
            'https://api.anthropic.com/v1/messages',
            headers={
                'x-api-key': api_key,
                'anthropic-version': '2023-06-01',
                'content-type': 'application/json',
            },
            json=payload,
            timeout=20,
        )
    except requests.RequestException as exc:
        raise LLMNoDisponible(f'Error de red con Anthropic: {exc}') from exc

    if resp.status_code >= 400:
        raise LLMNoDisponible(f'Anthropic HTTP {resp.status_code}: {resp.text[:200]}')

    data = resp.json()
    textos = []
    llamadas = []
    for block in data.get('content', []):
        if block.get('type') == 'text':
            textos.append(block.get('text', ''))
        elif block.get('type') == 'tool_use':
            llamadas.append(
                LlamadaHerramienta(
                    id=block.get('id', ''),
                    nombre=block.get('name', ''),
                    argumentos=block.get('input') or {},
                )
            )

    return RespuestaLLM(
        texto='\n'.join(textos).strip(),
        llamadas=llamadas,
        proveedor='anthropic',
        modelo=model,
        raw=data,
    )


def _generar_openai(
    mensajes: list[dict[str, Any]],
    herramientas: list[dict[str, Any]],
    system_prompt: str,
    model: str,
    api_key: str,
) -> RespuestaLLM:
    oai_msgs = []
    if system_prompt:
        oai_msgs.append({'role': 'system', 'content': system_prompt})

    for msg in mensajes:
        role = msg.get('role')
        if role == 'user':
            oai_msgs.append({'role': 'user', 'content': str(msg.get('content', ''))})
        elif role == 'assistant':
            entry: dict[str, Any] = {'role': 'assistant', 'content': msg.get('content') or ''}
            if msg.get('tool_calls'):
                entry['tool_calls'] = [
                    {
                        'id': call['id'],
                        'type': 'function',
                        'function': {
                            'name': call['nombre'],
                            'arguments': json.dumps(call.get('argumentos', {}), ensure_ascii=False),
                        },
                    }
                    for call in msg['tool_calls']
                ]
            oai_msgs.append(entry)
        elif role == 'tool':
            oai_msgs.append({
                'role': 'tool',
                'tool_call_id': msg.get('tool_call_id', ''),
                'content': json.dumps(msg.get('content', {}), ensure_ascii=False),
            })

    payload: dict[str, Any] = {
        'model': model,
        'messages': oai_msgs,
        'temperature': 0.3,
    }
    if herramientas:
        payload['tools'] = [
            {
                'type': 'function',
                'function': {
                    'name': h['name'],
                    'description': h.get('description', ''),
                    'parameters': h.get('parameters', {'type': 'object', 'properties': {}}),
                },
            }
            for h in herramientas
        ]

    try:
        resp = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            json=payload,
            timeout=20,
        )
    except requests.RequestException as exc:
        raise LLMNoDisponible(f'Error de red con OpenAI: {exc}') from exc

    if resp.status_code >= 400:
        raise LLMNoDisponible(f'OpenAI HTTP {resp.status_code}: {resp.text[:200]}')

    data = resp.json()
    choices = data.get('choices') or []
    if not choices:
        raise LLMNoDisponible('OpenAI no devolvió respuestas.')

    message = choices[0].get('message', {})
    llamadas = []
    for tc in message.get('tool_calls') or []:
        fn = tc.get('function', {})
        raw_args = fn.get('arguments', '{}')
        try:
            parsed_args = json.loads(raw_args) if isinstance(raw_args, str) else (raw_args or {})
        except json.JSONDecodeError:
            parsed_args = {}
        llamadas.append(
            LlamadaHerramienta(
                id=tc.get('id', ''),
                nombre=fn.get('name', ''),
                argumentos=parsed_args,
            )
        )

    return RespuestaLLM(
        texto=(message.get('content') or '').strip(),
        llamadas=llamadas,
        proveedor='openai',
        modelo=model,
        raw=data,
    )


def _generar_fake(
    mensajes: list[dict[str, Any]],
    herramientas: list[dict[str, Any]],
    system_prompt: str,
) -> RespuestaLLM:
    """Proveedor determinístico para pruebas y entorno sin API key."""
    if not mensajes:
        return RespuestaLLM(
            texto='¡Hola! Soy Nova, tu asistente de NovaGo Delivery. ¿En qué te ayudo hoy?',
            proveedor='fake',
            modelo='fake-local',
        )

    last_msg = mensajes[-1]
    if last_msg.get('role') == 'tool':
        return _format_fake_tool_response(last_msg.get('name', ''), last_msg.get('content') or {})

    user_text = str(last_msg.get('content', ''))
    norm = _normalize(user_text)
    is_moto = '(rol: motorizado)' in system_prompt.lower()

    if any(k in norm for k in ('cancelar', 'anular', 'cancelacion')):
        match = re.search(r'(?:pedido|orden|#)\s*#?\s*(\d+)|\b(\d{1,6})\b', norm)
        if match:
            pid = int(match.group(1) or match.group(2))
            return RespuestaLLM(
                llamadas=[LlamadaHerramienta(id='fake_1', nombre='como_cancelar', argumentos={'pedido_id': pid})],
                proveedor='fake',
                modelo='fake-local',
            )
        return RespuestaLLM(
            llamadas=[LlamadaHerramienta(id='fake_1', nombre='faq', argumentos={'tema': 'cancelaciones'})],
            proveedor='fake',
            modelo='fake-local',
        )

    if any(k in norm for k in ('entrega', 'asignada', 'reparto', 'ruta')) and is_moto:
        return RespuestaLLM(
            llamadas=[LlamadaHerramienta(id='fake_1', nombre='entregas_asignadas', argumentos={})],
            proveedor='fake',
            modelo='fake-local',
        )

    if any(k in norm for k in ('pedido', 'orden', 'seguimiento', 'tracking', 'donde esta', 'estado')):
        match = re.search(r'(?:pedido|orden|#)\s*#?\s*(\d+)|\b(\d{1,6})\b', norm)
        if match:
            pid = int(match.group(1) or match.group(2))
            return RespuestaLLM(
                llamadas=[LlamadaHerramienta(id='fake_1', nombre='estado_pedido', argumentos={'pedido_id': pid})],
                proveedor='fake',
                modelo='fake-local',
            )
        if is_moto:
            return RespuestaLLM(
                llamadas=[LlamadaHerramienta(id='fake_1', nombre='entregas_asignadas', argumentos={})],
                proveedor='fake',
                modelo='fake-local',
            )
        return RespuestaLLM(
            llamadas=[LlamadaHerramienta(id='fake_1', nombre='mis_pedidos', argumentos={'limite': 5})],
            proveedor='fake',
            modelo='fake-local',
        )

    if any(k in norm for k in ('detalle', 'ver producto')) and re.search(r'\b(\d{1,6})\b', norm):
        pid = int(re.search(r'\b(\d{1,6})\b', norm).group(1))
        return RespuestaLLM(
            llamadas=[LlamadaHerramienta(id='fake_1', nombre='detalle_producto', argumentos={'id': pid})],
            proveedor='fake',
            modelo='fake-local',
        )

    if any(k in norm for k in ('pago', 'yape', 'plin', 'efectivo', 'envio', 'delivery', 'zona', 'lima', 'horario', 'hora', 'cobertura')):
        return RespuestaLLM(
            llamadas=[LlamadaHerramienta(id='fake_1', nombre='faq', argumentos={'tema': norm})],
            proveedor='fake',
            modelo='fake-local',
        )

    if any(k in norm for k in ('buscar', 'producto', 'catalogo', 'menu', 'carta', 'hamburguesa', 'burger', 'pizza', 'pollo', 'bebida', 'postre', 'tienen', 'quiero', 'precio')):
        stop = {'buscar', 'productos', 'producto', 'catalogo', 'menu', 'carta', 'tienen', 'quiero', 'ver', 'en', 'el', 'la', 'los', 'las', 'de', 'que', 'hay', 'me', 'muestrame'}
        tokens = [t for t in re.findall(r'[a-z0-9]+', norm) if t not in stop and not t.isdigit()]
        texto = ' '.join(tokens[:3])
        return RespuestaLLM(
            llamadas=[LlamadaHerramienta(id='fake_1', nombre='buscar_producto', argumentos={'texto': texto, 'max': 5})],
            proveedor='fake',
            modelo='fake-local',
        )

    return RespuestaLLM(
        texto='¡Hola! Soy Nova, tu asistente de NovaGo Delivery. Puedo ayudarte a buscar productos, consultar tus pedidos o revisar métodos de pago y envío.',
        proveedor='fake',
        modelo='fake-local',
    )


def _format_fake_tool_response(tool_name: str, data: dict[str, Any]) -> RespuestaLLM:
    if data.get('requiere_login'):
        return RespuestaLLM(
            texto=data.get('mensaje', 'Inicia sesión para consultar tus pedidos.'),
            proveedor='fake',
            modelo='fake-local',
        )

    if tool_name == 'buscar_producto':
        prods = data.get('productos') or []
        if not prods:
            return RespuestaLLM(texto=data.get('mensaje', 'No encontré productos.'), proveedor='fake', modelo='fake-local')
        resumen = ', '.join(f"{p['nombre']} (S/ {p['precio']:.2f})" for p in prods[:3])
        return RespuestaLLM(
            texto=f"Encontré {len(prods)} producto(s): {resumen}.",
            proveedor='fake',
            modelo='fake-local',
        )

    if tool_name == 'estado_pedido':
        if not data.get('encontrado'):
            return RespuestaLLM(texto=data.get('mensaje', 'No se encontró el pedido.'), proveedor='fake', modelo='fake-local')
        extra = ' ¡Tu pedido ya fue entregado!' if data.get('estado') == 'entregado' else ''
        return RespuestaLLM(
            texto=f"{data.get('mensaje', '')}{extra}".strip(),
            proveedor='fake',
            modelo='fake-local',
        )

    if tool_name == 'mis_pedidos':
        peds = data.get('pedidos') or []
        if not peds:
            return RespuestaLLM(texto=data.get('mensaje', 'No tienes pedidos.'), proveedor='fake', modelo='fake-local')
        resumen = ', '.join(f"#{p['id']} ({p['estado_display']})" for p in peds[:3])
        return RespuestaLLM(
            texto=f"Tus pedidos recientes: {resumen}.",
            proveedor='fake',
            modelo='fake-local',
        )

    if tool_name == 'entregas_asignadas':
        ents = data.get('entregas') or []
        if not ents:
            return RespuestaLLM(texto=data.get('mensaje', 'Sin entregas asignadas.'), proveedor='fake', modelo='fake-local')
        resumen = ', '.join(f"#{e['id']} ({e['estado_display']})" for e in ents[:3])
        return RespuestaLLM(
            texto=f"Tus entregas activas: {resumen}.",
            proveedor='fake',
            modelo='fake-local',
        )

    return RespuestaLLM(
        texto=data.get('mensaje', 'Listo, aquí tienes la información solicitada.'),
        proveedor='fake',
        modelo='fake-local',
    )
