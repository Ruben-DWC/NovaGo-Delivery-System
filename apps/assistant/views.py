import json
import time
from typing import Any, Optional

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import ConversacionLog
from .services import llm_client, prompts, tools
from .services.llm_client import LLMNoDisponible

SESSION_HISTORY_KEY = 'nova_historial'
MAX_HISTORY_TURNS = 6
MAX_MESSAGE_LENGTH = 500
MAX_TOOL_ROUNDS = 3


def _get_rate_limit_config() -> tuple[int, int]:
    limit = int(getattr(settings, 'NOVA_RATE_LIMIT', 20))
    window = int(getattr(settings, 'NOVA_RATE_WINDOW_SECONDS', 600))
    return limit, window


def _get_session_key(request) -> str:
    if not request.session.session_key:
        request.session.save()
    return request.session.session_key or ''


def _check_rate_limit(request) -> bool:
    """Retorna True si la petición está dentro del límite, False si excede."""
    limit, window = _get_rate_limit_config()
    if getattr(request.user, 'is_authenticated', False):
        ident = f'user_{request.user.id}'
    else:
        sk = _get_session_key(request)
        ip = request.META.get('REMOTE_ADDR', 'unknown')
        ident = f'anon_{sk or ip}'

    cache_key = f'nova_rate_limit:{ident}'
    count = cache.get(cache_key)
    if count is None:
        cache.set(cache_key, 1, timeout=window)
        return True
    if int(count) >= limit:
        return False
    try:
        cache.incr(cache_key)
    except ValueError:
        cache.set(cache_key, int(count) + 1, timeout=window)
    return True


def _derive_emotion(
    last_tool_result: Optional[dict[str, Any]],
    pedido_data: Optional[dict[str, Any]],
    error: Optional[str] = None,
) -> str:
    if error:
        return 'disculpa'
    if pedido_data and pedido_data.get('estado') == 'entregado':
        return 'celebrando'
    if last_tool_result:
        if last_tool_result.get('requiere_login') or last_tool_result.get('encontrado') is False:
            return 'disculpa'
        if last_tool_result.get('encontrado') is True:
            return 'feliz'
    return 'neutral'


@require_POST
def chat_view(request):
    """Endpoint POST /assistant/chat/ protegido por CSRF y rate-limit."""
    if request.content_type and 'application/json' in request.content_type:
        try:
            raw_body = request.body.decode('utf-8') if request.body else '{}'
            payload = json.loads(raw_body or '{}')
            if not isinstance(payload, dict):
                return JsonResponse({'error': 'Formato JSON inválido.'}, status=400)
        except (UnicodeDecodeError, json.JSONDecodeError):
            return JsonResponse({'error': 'JSON malformado en la solicitud.'}, status=400)
    else:
        payload = request.POST

    if payload.get('action') == 'clear' or payload.get('clear') is True:
        return reset_view(request)

    message = str(payload.get('message') or payload.get('mensaje') or '').strip()
    if not message:
        return JsonResponse({'error': 'El mensaje no puede estar vacío.'}, status=400)

    if len(message) > MAX_MESSAGE_LENGTH:
        return JsonResponse(
            {'error': f'El mensaje excede el límite de {MAX_MESSAGE_LENGTH} caracteres.'},
            status=400,
        )

    if not _check_rate_limit(request):
        return JsonResponse(
            {
                'error': 'Has alcanzado el límite temporal de consultas. Intenta nuevamente en unos minutos.',
                'emocion': 'disculpa',
            },
            status=429,
        )

    session_key = _get_session_key(request)
    history = list(request.session.get(SESSION_HISTORY_KEY, []))
    recent_history = history[-(MAX_HISTORY_TURNS * 2):]

    system_prompt = prompts.construir_system_prompt(request.user)
    declaraciones = tools.obtener_herramientas_para_usuario(request.user)

    mensajes: list[dict[str, Any]] = list(recent_history)
    mensajes.append({'role': 'user', 'content': message})

    start_ts = time.monotonic()
    herramientas_usadas: list[str] = []
    acciones: list[dict[str, Any]] = []
    pedido_data: Optional[dict[str, Any]] = None
    last_tool_result: Optional[dict[str, Any]] = None
    proveedor = getattr(settings, 'NOVA_AI_PROVIDER', 'gemini')
    respuesta_texto = ''
    error_msg: Optional[str] = None

    try:
        for _ in range(MAX_TOOL_ROUNDS):
            llm_resp = llm_client.generar(
                mensajes=mensajes,
                herramientas=declaraciones,
                system_prompt=system_prompt,
            )
            proveedor = llm_resp.proveedor or proveedor

            if not llm_resp.llamadas:
                respuesta_texto = llm_resp.texto
                break

            mensajes.append({
                'role': 'assistant',
                'content': llm_resp.texto,
                'tool_calls': [
                    {
                        'id': c.id,
                        'nombre': c.nombre,
                        'argumentos': c.argumentos,
                        'thought_signature': c.thought_signature,
                    }
                    for c in llm_resp.llamadas
                ],
            })

            for call in llm_resp.llamadas:
                herramientas_usadas.append(call.nombre)
                resultado = tools.ejecutar_herramienta(
                    call.nombre,
                    call.argumentos,
                    user=request.user,
                )
                last_tool_result = resultado
                for acc in resultado.get('acciones') or []:
                    if acc not in acciones:
                        acciones.append(acc)

                if call.nombre == 'estado_pedido' and resultado.get('encontrado'):
                    ubi = resultado.get('ubicacion')
                    pedido_data = {
                        'id': resultado.get('pedido_id'),
                        'estado': resultado.get('estado'),
                        'estado_display': resultado.get('estado_display'),
                        'total': resultado.get('total'),
                        'motorizado': resultado.get('motorizado'),
                    }
                    if ubi:
                        pedido_data['lat'] = ubi['latitud']
                        pedido_data['lng'] = ubi['longitud']
                        pedido_data['ubicacion'] = ubi

                mensajes.append({
                    'role': 'tool',
                    'tool_call_id': call.id,
                    'name': call.nombre,
                    'content': resultado,
                })

        if not respuesta_texto:
            final_resp = llm_client.generar(
                mensajes=mensajes,
                herramientas=[],
                system_prompt=system_prompt,
            )
            proveedor = final_resp.proveedor or proveedor
            respuesta_texto = final_resp.texto or (
                last_tool_result.get('mensaje', '') if last_tool_result else ''
            )

    except LLMNoDisponible as exc:
        error_msg = str(exc)
        respuesta_texto = (
            'Lo siento, en este momento tengo inconvenientes para conectarme con mi motor de IA. '
            'Por favor, intenta nuevamente en unos momentos.'
        )
        acciones = []
        pedido_data = None

    latencia_ms = int((time.monotonic() - start_ts) * 1000)
    emocion = _derive_emotion(last_tool_result, pedido_data, error=error_msg)

    if not error_msg:
        history.append({'role': 'user', 'content': message})
        history.append({'role': 'assistant', 'content': respuesta_texto})
        request.session[SESSION_HISTORY_KEY] = history[-(MAX_HISTORY_TURNS * 2):]
        request.session.modified = True

    ConversacionLog.objects.create(
        usuario=request.user if getattr(request.user, 'is_authenticated', False) else None,
        session_key=session_key[:64],
        mensaje=message,
        respuesta=respuesta_texto,
        herramientas_usadas=list(dict.fromkeys(herramientas_usadas)),
        proveedor=proveedor[:32],
        latencia_ms=latencia_ms,
        error=error_msg,
    )

    response_payload: dict[str, Any] = {
        'respuesta': respuesta_texto,
        'emocion': emocion,
        'acciones': acciones,
    }
    if pedido_data is not None:
        response_payload['pedido'] = pedido_data

    return JsonResponse(response_payload)


@require_POST
def reset_view(request):
    """Endpoint POST /assistant/reset/ para limpiar el historial de Nova en sesión."""
    request.session[SESSION_HISTORY_KEY] = []
    request.session.modified = True
    return JsonResponse({
        'ok': True,
        'respuesta': 'Conversación reiniciada. ¿En qué puedo ayudarte hoy?',
        'emocion': 'neutral',
        'acciones': [],
    })
