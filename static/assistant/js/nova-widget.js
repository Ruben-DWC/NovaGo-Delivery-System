const WELCOME_TEXT =
    '¡Hola! Soy Nova, tu asistente de entregas NovaGo. Pregúntame por tu pedido, productos del catálogo, métodos de pago o costos de envío.';

function getCookie(name) {
    const value = '; ' + document.cookie;
    const parts = value.split('; ' + name + '=');
    if (parts.length === 2) {
        return decodeURIComponent(parts.pop().split(';').shift());
    }
    return '';
}

function getCsrfToken() {
    const cookieToken = getCookie('csrftoken');
    if (cookieToken) {
        return cookieToken;
    }
    const hxHeaders = document.body ? document.body.getAttribute('hx-headers') : null;
    if (hxHeaders) {
        try {
            const parsed = JSON.parse(hxHeaders);
            if (parsed['X-CSRFToken']) {
                return parsed['X-CSRFToken'];
            }
        } catch (_) {
            return '';
        }
    }
    return '';
}

function sanitizeUrl(rawUrl, fallback) {
    if (typeof rawUrl !== 'string' || !rawUrl.trim()) {
        return fallback;
    }
    const trimmed = rawUrl.trim();
    if (trimmed.startsWith('/') && !trimmed.startsWith('//')) {
        return trimmed;
    }
    if (trimmed.startsWith('https://') || trimmed.startsWith('http://')) {
        return trimmed;
    }
    return fallback;
}

function resolveActionHref(action) {
    if (!action || typeof action !== 'object') {
        return null;
    }
    if (action.url) {
        return sanitizeUrl(String(action.url), null);
    }
    const tipo = String(action.tipo || '').toLowerCase();
    if (tipo === 'ver_producto') {
        const pid = action.id || action.producto_id;
        return pid ? '/products/' + encodeURIComponent(String(pid)) + '/' : '/products/';
    }
    if (tipo === 'ver_pedido') {
        const oid = action.id || action.pedido_id;
        return oid ? '/orders/' + encodeURIComponent(String(oid)) + '/' : '/orders/';
    }
    if (tipo === 'login') {
        return '/users/login/';
    }
    return null;
}

function resolveActionLabel(action) {
    if (action && typeof action.label === 'string' && action.label.trim()) {
        return action.label.trim();
    }
    const tipo = String((action && action.tipo) || '').toLowerCase();
    if (tipo === 'ver_producto') return 'Ver producto';
    if (tipo === 'ver_pedido') return 'Ver pedido';
    if (tipo === 'login') return 'Iniciar sesión';
    return 'Abrir';
}

function loadLeafletAssets(callback) {
    if (window.L && typeof window.L.map === 'function') {
        callback();
        return;
    }
    if (!document.getElementById('leaflet-css-cdn')) {
        const link = document.createElement('link');
        link.id = 'leaflet-css-cdn';
        link.rel = 'stylesheet';
        link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
        document.head.appendChild(link);
    }
    const existingScript = document.getElementById('leaflet-js-cdn');
    if (existingScript) {
        existingScript.addEventListener('load', callback, { once: true });
        return;
    }
    const script = document.createElement('script');
    script.id = 'leaflet-js-cdn';
    script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
    script.onload = callback;
    document.head.appendChild(script);
}

function initNovaWidget() {
    const root = document.getElementById('nova-root');
    if (!root) return;

    const chatUrl = root.getAttribute('data-chat-url') || '/assistant/chat/';
    const resetUrl = root.getAttribute('data-reset-url') || '/assistant/reset/';
    const avatarSrc = root.getAttribute('data-avatar-src') || '/static/assistant/js/nova-avatar.js';
    const modelUrl = root.getAttribute('data-model-url') || '/static/assistant/models/nova.glb';

    const toggleBtn = document.getElementById('nova-toggle');
    const closeBtn = document.getElementById('nova-close');
    const resetBtn = document.getElementById('nova-reset');
    const voiceToggleBtn = document.getElementById('nova-voice-toggle');
    const voiceIcon = document.getElementById('nova-voice-icon');
    const panel = document.getElementById('nova-panel');
    const canvas = document.getElementById('nova-avatar-canvas');
    const statusEl = document.getElementById('nova-status');
    const messagesEl = document.getElementById('nova-messages');
    const form = document.getElementById('nova-form');
    const input = document.getElementById('nova-input');
    const sendBtn = document.getElementById('nova-send');
    const chips = root.querySelectorAll('[data-nova-prompt]');

    let isOpen = false;
    let isBusy = false;
    let voiceEnabled = false;
    let avatarController = null;
    let avatarLoadingPromise = null;
    let mapCounter = 0;

    function setStatus(text) {
        if (statusEl) {
            statusEl.textContent = text;
        }
    }

    function setAvatarEmotion(emotion) {
        if (avatarController) {
            avatarController.setEmotion(emotion);
        }
    }

    function ensureAvatarLoaded() {
        if (avatarController) {
            avatarController.resume();
            return Promise.resolve(avatarController);
        }
        if (avatarLoadingPromise) {
            return avatarLoadingPromise;
        }
        if (!canvas) {
            return Promise.resolve(null);
        }

        avatarLoadingPromise = import(avatarSrc)
            .then((mod) => {
                if (!mod || typeof mod.NovaAvatarController !== 'function') {
                    return null;
                }
                avatarController = new mod.NovaAvatarController(canvas, { modelUrl });
                if (isOpen) {
                    avatarController.resume();
                }
                return avatarController;
            })
            .catch(() => null);

        return avatarLoadingPromise;
    }

    function stopSpeech() {
        if ('speechSynthesis' in window) {
            window.speechSynthesis.cancel();
        }
    }

    function speakText(text, afterEmotion) {
        if (!voiceEnabled || !('speechSynthesis' in window) || !text) {
            return;
        }
        stopSpeech();
        const utterance = new SpeechSynthesisUtterance(text);
        const voices = window.speechSynthesis.getVoices();
        const preferredVoice =
            voices.find((v) => v.lang && v.lang.toLowerCase().startsWith('es-pe')) ||
            voices.find((v) => v.lang && v.lang.toLowerCase().startsWith('es-es')) ||
            voices.find((v) => v.lang && v.lang.toLowerCase().startsWith('es'));
        if (preferredVoice) {
            utterance.voice = preferredVoice;
            utterance.lang = preferredVoice.lang;
        } else {
            utterance.lang = 'es-PE';
        }
        utterance.rate = 1.03;

        utterance.onstart = () => setAvatarEmotion('hablando');
        utterance.onend = () => setAvatarEmotion(afterEmotion || 'neutral');
        utterance.onerror = () => setAvatarEmotion(afterEmotion || 'neutral');

        window.speechSynthesis.speak(utterance);
    }

    function setPanelOpen(open) {
        if (!panel || !toggleBtn) return;
        isOpen = open;
        if (open) {
            panel.classList.remove('is-hidden');
            panel.setAttribute('aria-hidden', 'false');
            toggleBtn.setAttribute('aria-expanded', 'true');
            ensureAvatarLoaded();
            if (input) {
                input.focus();
            }
        } else {
            panel.classList.add('is-hidden');
            panel.setAttribute('aria-hidden', 'true');
            toggleBtn.setAttribute('aria-expanded', 'false');
            stopSpeech();
            if (avatarController) {
                avatarController.pause();
            }
        }
    }

    function scrollToBottom() {
        if (messagesEl) {
            messagesEl.scrollTop = messagesEl.scrollHeight;
        }
    }

    function renderActions(container, acciones) {
        if (!Array.isArray(acciones) || acciones.length === 0) {
            return;
        }
        const wrap = document.createElement('div');
        wrap.className = 'nova-actions';

        acciones.slice(0, 6).forEach((action) => {
            const href = resolveActionHref(action);
            if (!href) return;
            const link = document.createElement('a');
            link.className = 'nova-action-btn';
            link.href = href;
            link.textContent = resolveActionLabel(action);
            wrap.appendChild(link);
        });

        if (wrap.childElementCount > 0) {
            container.appendChild(wrap);
        }
    }

    function renderOrderMiniMap(container, pedido) {
        if (!pedido || typeof pedido !== 'object') return;
        const lat = Number(pedido.lat);
        const lng = Number(pedido.lng);
        if (!Number.isFinite(lat) || !Number.isFinite(lng)) return;

        mapCounter += 1;
        const mapId = 'nova-mini-map-' + mapCounter;

        const card = document.createElement('div');
        card.className = 'nova-map-card';

        const mapDiv = document.createElement('div');
        mapDiv.id = mapId;
        mapDiv.className = 'nova-mini-map';
        mapDiv.setAttribute('aria-label', 'Ubicación del pedido en mapa');
        card.appendChild(mapDiv);

        const caption = document.createElement('div');
        caption.className = 'nova-map-caption';
        const codeText = pedido.codigo ? 'Pedido #' + pedido.codigo : 'Ubicación actual';
        const stateText = pedido.estado ? ' · ' + pedido.estado : '';
        caption.textContent = codeText + stateText;
        card.appendChild(caption);

        container.appendChild(card);

        loadLeafletAssets(() => {
            if (!window.L || !document.getElementById(mapId)) return;
            const map = window.L.map(mapId, {
                center: [lat, lng],
                zoom: 15,
                zoomControl: false,
                attributionControl: false,
            });
            window.L.tileLayer(
                'https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}',
                { maxZoom: 19 }
            ).addTo(map);
            window.L.marker([lat, lng]).addTo(map);
            window.setTimeout(() => map.invalidateSize(), 150);
        });
    }

    function appendMessage(role, text, options = {}) {
        if (!messagesEl) return null;

        const wrapper = document.createElement('div');
        wrapper.className = role === 'user' ? 'nova-msg nova-msg-user' : 'nova-msg nova-msg-bot';

        const bubble = document.createElement('div');
        bubble.className = options.typing ? 'nova-bubble nova-typing' : 'nova-bubble';
        bubble.textContent = text;
        wrapper.appendChild(bubble);

        if (role === 'bot') {
            renderActions(wrapper, options.acciones);
            renderOrderMiniMap(wrapper, options.pedido);
        }

        messagesEl.appendChild(wrapper);
        scrollToBottom();
        return wrapper;
    }

    function setBusy(busy) {
        isBusy = busy;
        if (sendBtn) sendBtn.disabled = busy;
        if (input) input.disabled = busy;
    }

    async function sendMessage(rawMessage) {
        const message = String(rawMessage || '').trim();
        if (!message || isBusy) return;

        appendMessage('user', message);
        if (input) input.value = '';

        setBusy(true);
        setStatus('Pensando...');
        setAvatarEmotion('pensando');
        const typingEl = appendMessage('bot', 'Nova está pensando...', { typing: true });

        try {
            const response = await fetch(chatUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken(),
                },
                body: JSON.stringify({ message }),
            });

            const payload = await response.json().catch(() => ({}));
            if (typingEl && typingEl.parentNode) {
                typingEl.parentNode.removeChild(typingEl);
            }

            if (!response.ok) {
                const errText =
                    payload.error ||
                    payload.respuesta ||
                    'No pude procesar tu solicitud en este momento.';
                appendMessage('bot', errText);
                setAvatarEmotion('disculpa');
                setStatus('Asistente IA NovaGo');
                return;
            }

            const botText = payload.respuesta || payload.reply || 'Sin respuesta disponible.';
            const emotion = payload.emocion || 'neutral';

            appendMessage('bot', botText, {
                acciones: payload.acciones,
                pedido: payload.pedido,
            });

            setAvatarEmotion(emotion);
            setStatus('Asistente IA NovaGo');
            speakText(botText, emotion);
        } catch (_) {
            if (typingEl && typingEl.parentNode) {
                typingEl.parentNode.removeChild(typingEl);
            }
            appendMessage('bot', 'Error de conexión con Nova. Intenta nuevamente.');
            setAvatarEmotion('disculpa');
            setStatus('Sin conexión');
        } finally {
            setBusy(false);
            if (isOpen && input) {
                input.focus();
            }
        }
    }

    async function resetConversation() {
        if (isBusy) return;
        stopSpeech();
        setBusy(true);

        try {
            await fetch(resetUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken(),
                },
                body: JSON.stringify({ action: 'clear' }),
            });
        } catch (_) {
            // Even if network fails, reset local UI cleanly
        } finally {
            setBusy(false);
        }

        if (messagesEl) {
            messagesEl.textContent = '';
            appendMessage('bot', WELCOME_TEXT);
        }
        setAvatarEmotion('neutral');
        setStatus('Asistente IA NovaGo');
    }

    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => setPanelOpen(!isOpen));
    }

    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            setPanelOpen(false);
            if (toggleBtn) toggleBtn.focus();
        });
    }

    if (resetBtn) {
        resetBtn.addEventListener('click', resetConversation);
    }

    if (voiceToggleBtn) {
        voiceToggleBtn.addEventListener('click', () => {
            voiceEnabled = !voiceEnabled;
            voiceToggleBtn.setAttribute('aria-pressed', voiceEnabled ? 'true' : 'false');
            voiceToggleBtn.setAttribute(
                'aria-label',
                voiceEnabled ? 'Silenciar voz de Nova' : 'Activar voz de Nova'
            );
            if (voiceIcon) {
                voiceIcon.className = voiceEnabled ? 'ph-fill ph-speaker-high' : 'ph ph-speaker-slash';
            }
            if (!voiceEnabled) {
                stopSpeech();
            }
        });
    }

    if (form) {
        form.addEventListener('submit', (evt) => {
            evt.preventDefault();
            if (input) {
                sendMessage(input.value);
            }
        });
    }

    chips.forEach((chip) => {
        chip.addEventListener('click', () => {
            const prompt = chip.getAttribute('data-nova-prompt') || '';
            if (prompt) {
                sendMessage(prompt);
            }
        });
    });

    document.addEventListener('keydown', (evt) => {
        if (evt.key === 'Escape' && isOpen) {
            setPanelOpen(false);
            if (toggleBtn) toggleBtn.focus();
        }
    });
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initNovaWidget);
} else {
    initNovaWidget();
}
