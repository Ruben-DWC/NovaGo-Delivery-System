/**
 * Mapa realtime de motorizado basado en WebSocket + snapshot inicial.
 */
class DeliveryMap {
    constructor(options = {}) {
        this.mapElement = options.mapElement || document.getElementById('map-track');
        this.map = null;
        this.tileLayer = null;
        this.markers = {};
        this.route = null;
        this.historyPolyline = null;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.autoGpsTimer = null;
        this.autoGpsEnabled = false;
        this.autoGpsWatchId = null;
        this.lastAutoGpsSentAt = 0;
        this.lastRoadRouteKey = '';
        this.lastRoadRoutePoints = null;
        this.routeFetchToken = 0;
        this.routeRenderToken = 0;

        this.apiUrl = this.mapElement?.dataset.apiUrl || '';
        this.updateLocationUrl = this.mapElement?.dataset.updateLocationUrl || '';
        this.activeOrderId = this.mapElement?.dataset.activeOrderId || '';

        this.orderSelect = document.getElementById('active-order-select');
        this.gpsButton = document.getElementById('gps-update-btn');
        this.refreshButton = document.getElementById('map-refresh-btn');
        this.centerButton = document.getElementById('map-center-btn');
        this.autoGpsToggle = document.getElementById('gps-auto-toggle');
        this.autoGpsInterval = document.getElementById('gps-auto-interval');
        this.signalStatus = document.getElementById('gps-signal-status');
        this.lastUpdateEl = document.getElementById('current-last-update');
        this.orderStateEl = document.getElementById('current-order-state');
        this.autoGpsStatusEl = document.getElementById('auto-gps-status');
        this.autoGpsCountersEl = document.getElementById('auto-gps-counters');

        this.autoGpsStats = {
            sent: 0,
            failed: 0,
            lastSuccessAt: null,
        };

        const storeLat = Number.parseFloat(this.mapElement?.dataset.storeLat || '-12.0262');
        const storeLng = Number.parseFloat(this.mapElement?.dataset.storeLng || '-76.9212');

        this.currentData = {
            origin: { lat: storeLat, lng: storeLng, name: 'NovaGo Ate - Vitarte' },
            motorizado: { lat: storeLat, lng: storeLng, name: 'Motorizado' },
            destination: { lat: storeLat + 0.0045, lng: storeLng + 0.0045, name: 'Destino' },
            distanceKm: 0,
            etaMin: 0,
            trackingHistory: [],
            orderStatus: '',
        };

        this.updateGpsButtonState(Boolean(this.activeOrderId));
    }

    static getCsrfToken() {
        const cookie = document.cookie
            .split(';')
            .map((item) => item.trim())
            .find((item) => item.startsWith('csrftoken='));
        return cookie ? decodeURIComponent(cookie.split('=')[1]) : '';
    }

    setSignalStatus(text, isLive = false) {
        if (!this.signalStatus) {
            return;
        }
        this.signalStatus.textContent = text;
        this.signalStatus.classList.toggle('is-live', isLive);
    }

    updateGpsButtonState(enabled) {
        if (!this.gpsButton) {
            return;
        }

        this.gpsButton.disabled = !enabled;
        this.gpsButton.title = enabled
            ? 'Enviar mi ubicacion actual para este pedido'
            : 'Selecciona o activa un pedido para usar GPS';
    }

    setLastUpdate(isoDate) {
        if (!this.lastUpdateEl) {
            return;
        }
        if (!isoDate) {
            this.lastUpdateEl.innerHTML = '<i class="fas fa-wave-square icon" aria-hidden="true"></i> Sin señal GPS';
            return;
        }

        const date = new Date(isoDate);
        if (Number.isNaN(date.getTime())) {
            this.lastUpdateEl.innerHTML = '<i class="fas fa-wave-square icon" aria-hidden="true"></i> Señal inválida';
            return;
        }

        const hh = String(date.getHours()).padStart(2, '0');
        const mm = String(date.getMinutes()).padStart(2, '0');
        const ss = String(date.getSeconds()).padStart(2, '0');
        this.lastUpdateEl.innerHTML = `<i class="fas fa-wave-square icon" aria-hidden="true"></i> ${hh}:${mm}:${ss}`;
    }

    bindDashboardControls() {
        if (this.orderSelect) {
            this.orderSelect.addEventListener('change', () => {
                this.activeOrderId = this.orderSelect.value;
                this.requestSnapshot(this.activeOrderId);
            });
        }

        if (this.gpsButton) {
            this.gpsButton.addEventListener('click', () => this.captureAndSendCurrentPosition());
        }

        if (this.refreshButton) {
            this.refreshButton.addEventListener('click', () => this.requestSnapshot(this.activeOrderId));
        }

        if (this.centerButton) {
            this.centerButton.addEventListener('click', () => this.centerMapToRoute());
        }

        if (this.autoGpsToggle) {
            this.autoGpsToggle.addEventListener('click', () => this.toggleAutoGps());
        }

        if (this.autoGpsInterval) {
            this.autoGpsInterval.addEventListener('change', () => {
                if (this.autoGpsEnabled) {
                    this.startAutoGpsWatch();
                    this.setSignalStatus('Auto GPS reconfigurado', true);
                }
            });
        }

        document.addEventListener('visibilitychange', () => {
            if (document.hidden && this.autoGpsEnabled) {
                this.stopAutoGps('Auto GPS pausado por pestaña inactiva');
            }
        });

        document.querySelectorAll('.location-form').forEach((form) => {
            form.addEventListener('submit', (event) => {
                event.preventDefault();
                const orderId = form.querySelector('input[name="pedido_id"]')?.value || this.activeOrderId;
                const lat = Number.parseFloat(form.querySelector('input[name="latitud"]')?.value || '');
                const lng = Number.parseFloat(form.querySelector('input[name="longitud"]')?.value || '');

                if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
                    this.setSignalStatus('Coordenadas inválidas', false);
                    return;
                }

                this.sendLocation(orderId, lat, lng);
            });
        });

        this.watchThemeChanges();
    }

    async fetchInitialSnapshot() {
        if (!this.apiUrl) {
            return;
        }

        const url = new URL(this.apiUrl, window.location.origin);
        if (this.activeOrderId) {
            url.searchParams.set('pedido_id', this.activeOrderId);
        }

        try {
            const response = await fetch(url.toString(), {
                method: 'GET',
                credentials: 'same-origin',
                headers: {
                    Accept: 'application/json',
                },
            });

            if (!response.ok) {
                this.setSignalStatus('No se pudo cargar mapa', false);
                return;
            }

            const data = await response.json();
            this.applySnapshot(data);
        } catch (error) {
            this.setSignalStatus('Error inicial de mapa', false);
        }
    }

    initWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
        const wsUrl = `${protocol}://${window.location.host}/ws/tracking/motorizado/`;

        this.ws = new WebSocket(wsUrl);
        this.setSignalStatus('Conectando tiempo real...', false);

        this.ws.addEventListener('open', () => {
            this.reconnectAttempts = 0;
            this.setSignalStatus('Tiempo real activo', true);
            this.requestSnapshot(this.activeOrderId);
        });

        this.ws.addEventListener('message', (event) => {
            try {
                const message = JSON.parse(event.data);
                const payload = message.payload || {};
                if (message.type === 'tracking.snapshot' || message.type === 'tracking.location') {
                    this.applySnapshot(payload);
                }
            } catch (error) {
                this.setSignalStatus('Mensaje realtime inválido', false);
            }
        });

        this.ws.addEventListener('close', () => {
            this.setSignalStatus('Tiempo real desconectado', false);
            this.scheduleReconnect();
        });

        this.ws.addEventListener('error', () => {
            this.setSignalStatus('Error en canal realtime', false);
        });
    }

    scheduleReconnect() {
        this.reconnectAttempts += 1;
        const waitMs = Math.min(10000, 1500 * this.reconnectAttempts);
        window.setTimeout(() => this.initWebSocket(), waitMs);
    }

    requestSnapshot(orderId = '') {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            this.fetchInitialSnapshot();
            return;
        }

        this.ws.send(JSON.stringify({
            type: 'tracking.request_snapshot',
            pedido_id: orderId || null,
        }));
    }

    async captureAndSendCurrentPosition() {
        if (!navigator.geolocation) {
            this.setSignalStatus('Geolocalización no soportada en este navegador', false);
            return;
        }

        if (!this.activeOrderId) {
            this.setSignalStatus('Selecciona un pedido activo para usar GPS', false);
            return;
        }

        if (this.gpsButton) {
            this.gpsButton.disabled = true;
            this.gpsButton.textContent = '⏳ Localizando... (máx 10s)';
        }
        this.setSignalStatus('Obteniendo GPS...', false);

        // Timeout manual más largo para dar tiempo
        const timeoutId = setTimeout(() => {
            this.setSignalStatus('Timeout de GPS - intenta de nuevo', false);
            if (this.gpsButton) {
                this.gpsButton.disabled = false;
                this.gpsButton.textContent = '📍 Usar mi GPS';
            }
        }, 11000);

        navigator.geolocation.getCurrentPosition(
            (position) => {
                clearTimeout(timeoutId);
                if (this.gpsButton) {
                    this.gpsButton.textContent = '📍 Usar mi GPS';
                }
                this.sendLocation(
                    this.activeOrderId,
                    position.coords.latitude,
                    position.coords.longitude,
                    position.coords.accuracy,
                );
            },
            (error) => {
                clearTimeout(timeoutId);
                let errorMsg = 'Error de GPS desconocido';
                if (error.code === error.PERMISSION_DENIED) {
                    errorMsg = 'Permiso GPS denegado. Actívalo en configuración';
                } else if (error.code === error.POSITION_UNAVAILABLE) {
                    errorMsg = 'Ubicación no disponible. Intenta en otro lugar';
                } else if (error.code === error.TIMEOUT) {
                    errorMsg = 'Timeout de GPS (10s). Intenta de nuevo';
                }
                this.setSignalStatus(errorMsg, false);
                if (this.gpsButton) {
                    this.gpsButton.disabled = false;
                    this.gpsButton.textContent = '📍 Usar mi GPS';
                }
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 0,
            },
        );
    }

    getAutoGpsIntervalMs() {
        const seconds = Number.parseInt(this.autoGpsInterval?.value || '15', 10);
        if (!Number.isFinite(seconds) || seconds < 5) {
            return 15000;
        }
        return seconds * 1000;
    }

    toggleAutoGps() {
        if (this.autoGpsEnabled) {
            this.stopAutoGps('Auto GPS desactivado');
            return;
        }

        if (!this.activeOrderId) {
            this.setSignalStatus('Selecciona un pedido activo para Auto GPS', false);
            return;
        }

        this.autoGpsEnabled = true;
        this.syncAutoGpsUi();
        this.setSignalStatus('Auto GPS activo', true);
        this.updateAutoGpsTelemetry('Activo, esperando posición...');

        this.lastAutoGpsSentAt = 0;
        this.startAutoGpsWatch();
    }

    stopAutoGps(statusMessage = 'Auto GPS desactivado') {
        this.autoGpsEnabled = false;
        if (this.autoGpsTimer) {
            window.clearInterval(this.autoGpsTimer);
            this.autoGpsTimer = null;
        }
        if (this.autoGpsWatchId !== null && navigator.geolocation) {
            navigator.geolocation.clearWatch(this.autoGpsWatchId);
            this.autoGpsWatchId = null;
        }
        this.syncAutoGpsUi();
        this.setSignalStatus(statusMessage, false);
        this.updateAutoGpsTelemetry('Inactivo');
    }

    updateAutoGpsTelemetry(statusText = '') {
        if (this.autoGpsStatusEl) {
            const status = statusText || (this.autoGpsEnabled ? 'Activo' : 'Inactivo');
            this.autoGpsStatusEl.innerHTML = `<span class="icon"><i class="fas fa-wave-square" aria-hidden="true"></i></span> ${status}`;
        }

        if (this.autoGpsCountersEl) {
            this.autoGpsCountersEl.innerHTML = `<span class="icon"><i class="fas fa-paper-plane" aria-hidden="true"></i></span> Envios: ${this.autoGpsStats.sent} | Fallos: ${this.autoGpsStats.failed}`;
        }
    }

    startAutoGpsWatch() {
        if (!navigator.geolocation) {
            this.stopAutoGps('Geolocalización no soportada');
            return;
        }

        if (this.autoGpsWatchId !== null) {
            navigator.geolocation.clearWatch(this.autoGpsWatchId);
            this.autoGpsWatchId = null;
        }

        const intervalMs = this.getAutoGpsIntervalMs();

        this.autoGpsWatchId = navigator.geolocation.watchPosition(
            (position) => {
                if (!this.autoGpsEnabled || !this.activeOrderId) {
                    return;
                }

                const now = Date.now();
                if ((now - this.lastAutoGpsSentAt) < intervalMs) {
                    return;
                }

                this.lastAutoGpsSentAt = now;
                this.sendLocation(
                    this.activeOrderId,
                    position.coords.latitude,
                    position.coords.longitude,
                    position.coords.accuracy,
                    'auto',
                );
            },
            (error) => {
                let errorMsg = 'Auto GPS sin señal';
                if (error.code === error.PERMISSION_DENIED) {
                    errorMsg = 'Permiso GPS denegado';
                } else if (error.code === error.POSITION_UNAVAILABLE) {
                    errorMsg = 'Ubicación no disponible';
                } else if (error.code === error.TIMEOUT) {
                    errorMsg = 'Timeout de GPS';
                }
                this.setSignalStatus(errorMsg, false);
                this.autoGpsStats.failed += 1;
                this.updateAutoGpsTelemetry(errorMsg);
            },
            {
                enableHighAccuracy: true,
                timeout: 12000,
                maximumAge: 2000,
            },
        );
    }

    syncAutoGpsUi() {
        if (!this.autoGpsToggle) {
            return;
        }

        this.autoGpsToggle.setAttribute('aria-pressed', this.autoGpsEnabled ? 'true' : 'false');
        this.autoGpsToggle.classList.toggle('is-active', this.autoGpsEnabled);
        this.autoGpsToggle.innerHTML = this.autoGpsEnabled
            ? '<i class="fas fa-wave-square"></i> Auto GPS ON'
            : '<i class="fas fa-wave-square"></i> Auto GPS OFF';
    }

    updateOrderState(status) {
        if (!this.orderStateEl) {
            return;
        }

        const statusLabels = {
            confirmado: 'Confirmado',
            en_preparacion: 'En preparación',
            en_camino: 'En camino',
            entregado: 'Entregado',
            pendiente_asignacion: 'Pendiente de asignación',
            cancelado: 'Cancelado',
        };

        const state = statusLabels[status] || status || 'Sin pedido seleccionado';
        this.orderStateEl.innerHTML = `<span class="icon"><i class="fas fa-box" aria-hidden="true"></i></span> ${state}`;
    }

    getThemeTileConfig() {
        const theme = document.documentElement.getAttribute('data-theme') || 'light';
        if (theme === 'dark') {
            return {
                url: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
                attribution: '&copy; OpenStreetMap contributors, &copy; CartoDB',
            };
        }
        return {
            url: 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
            attribution: '&copy; OpenStreetMap contributors, &copy; CartoDB',
        };
    }

    applyThemeTiles() {
        if (!this.map) {
            return;
        }

        const tileConfig = this.getThemeTileConfig();
        if (this.tileLayer) {
            this.map.removeLayer(this.tileLayer);
        }

        this.tileLayer = L.tileLayer(tileConfig.url, {
            attribution: tileConfig.attribution,
            maxZoom: 19,
            crossOrigin: 'anonymous',
        }).addTo(this.map);
    }

    watchThemeChanges() {
        const observer = new MutationObserver(() => {
            this.applyThemeTiles();
        });
        observer.observe(document.documentElement, {
            attributes: true,
            attributeFilter: ['data-theme'],
        });
    }

    centerMapToRoute() {
        if (!this.map) {
            return;
        }

        const bounds = L.latLngBounds([
            [this.currentData.origin.lat, this.currentData.origin.lng],
            [this.currentData.motorizado.lat, this.currentData.motorizado.lng],
            [this.currentData.destination.lat, this.currentData.destination.lng],
        ]);
        this.map.fitBounds(bounds, { padding: [50, 50], maxZoom: 15 });
    }

    async fetchRoadRoute(points) {
        const coords = points
            .map((point) => `${point[1]},${point[0]}`)
            .join(';');
        const routeUrl = `https://router.project-osrm.org/route/v1/driving/${coords}?overview=full&geometries=geojson&steps=false`;
        const response = await fetch(routeUrl, { method: 'GET', cache: 'no-store' });
        if (!response.ok) {
            throw new Error('route fetch failed');
        }

        const data = await response.json();
        const geometry = data?.routes?.[0]?.geometry?.coordinates;
        if (!Array.isArray(geometry) || geometry.length < 2) {
            throw new Error('invalid route geometry');
        }

        return geometry.map((coord) => [Number(coord[1]), Number(coord[0])]);
    }

    async resolveRoutePoints(fallbackPoints) {
        const routeKey = fallbackPoints
            .map((point) => `${point[0].toFixed(5)},${point[1].toFixed(5)}`)
            .join('|');

        if (routeKey === this.lastRoadRouteKey && this.lastRoadRoutePoints) {
            return this.lastRoadRoutePoints;
        }

        this.lastRoadRouteKey = routeKey;
        const token = ++this.routeFetchToken;

        try {
            const resolved = await this.fetchRoadRoute(fallbackPoints);
            if (token !== this.routeFetchToken) {
                return this.lastRoadRoutePoints || fallbackPoints;
            }
            this.lastRoadRoutePoints = resolved;
            return resolved;
        } catch (error) {
            if (token !== this.routeFetchToken) {
                return this.lastRoadRoutePoints || fallbackPoints;
            }
            this.lastRoadRoutePoints = fallbackPoints;
            return fallbackPoints;
        }
    }

    async sendLocation(orderId, lat, lng, precision = null, source = 'manual') {
        if (!this.updateLocationUrl || !orderId) {
            this.setSignalStatus('Sin pedido activo para actualizar', false);
            return;
        }

        try {
            const response = await fetch(this.updateLocationUrl, {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': DeliveryMap.getCsrfToken(),
                },
                body: JSON.stringify({
                    pedido_id: orderId,
                    latitud: lat,
                    longitud: lng,
                    precision,
                }),
            });

            const payload = await response.json().catch(() => ({}));

            if (!response.ok || !payload.ok) {
                const errorMessage = payload.error || 'No se pudo actualizar ubicación';
                this.setSignalStatus(errorMessage, false);
                if (source === 'auto') {
                    this.autoGpsStats.failed += 1;
                    this.updateAutoGpsTelemetry(errorMessage);
                }
                return;
            }

            this.setSignalStatus('Ubicación enviada', true);
            if (source === 'auto') {
                this.autoGpsStats.sent += 1;
                this.autoGpsStats.lastSuccessAt = new Date();
                const hh = String(this.autoGpsStats.lastSuccessAt.getHours()).padStart(2, '0');
                const mm = String(this.autoGpsStats.lastSuccessAt.getMinutes()).padStart(2, '0');
                const ss = String(this.autoGpsStats.lastSuccessAt.getSeconds()).padStart(2, '0');
                this.updateAutoGpsTelemetry(`Ultimo envio ${hh}:${mm}:${ss}`);
            }
            if (this.map) {
                this.map.panTo([lat, lng], { animate: true, duration: 0.6 });
            }
            this.requestSnapshot(orderId);
        } catch (error) {
            this.setSignalStatus('Error de red al enviar GPS', false);
            if (source === 'auto') {
                this.autoGpsStats.failed += 1;
                this.updateAutoGpsTelemetry('Error de red');
            }
        } finally {
            if (this.gpsButton) {
                this.gpsButton.disabled = false;
            }
        }
    }

    async applySnapshot(data) {
        if (!data.ok || !data.has_active_order) {
            if (this.autoGpsEnabled) {
                this.stopAutoGps('Auto GPS detenido: sin pedidos activos');
            }
            this.setSignalStatus('Sin pedidos activos', false);
            this.setLastUpdate(null);
            this.updateGpsButtonState(false);
            this.currentData.distanceKm = 0;
            this.currentData.etaMin = 0;
            this.updateDistance();
            this.updateOrderState('');
            if (this.route && this.map) {
                this.map.removeLayer(this.route);
                this.route = null;
            }
            return;
        }

        this.activeOrderId = String(data.active_order_id || this.activeOrderId);
        if (this.orderSelect && this.activeOrderId) {
            this.orderSelect.value = this.activeOrderId;
        }

        this.currentData.origin = {
            lat: Number.parseFloat(data.store.lat),
            lng: Number.parseFloat(data.store.lng),
            name: data.store.name || 'NovaGo',
        };
        this.currentData.motorizado = {
            lat: Number.parseFloat(data.motorizado.lat),
            lng: Number.parseFloat(data.motorizado.lng),
            name: 'Motorizado',
        };
        this.currentData.destination = {
            lat: Number.parseFloat(data.destination.lat),
            lng: Number.parseFloat(data.destination.lng),
            name: 'Destino',
        };
        this.currentData.distanceKm = Number.parseFloat(data.distance_km || 0);
        this.currentData.etaMin = Number.parseInt(data.eta_min || 0, 10);
        this.currentData.trackingHistory = Array.isArray(data.tracking_history) ? data.tracking_history : [];
        this.currentData.orderStatus = data.order_status || '';

        this.updateGpsButtonState(true);

        this.updateMarkers();
        await this.addRoute();
        this.drawHistoryPolyline();
        this.updateDistance();
        this.updateOrderState(this.currentData.orderStatus);
        this.setLastUpdate(data.motorizado.last_update);
        this.setSignalStatus('Tiempo real activo', true);
    }

    async initMap() {
        if (!this.mapElement || typeof L === 'undefined') {
            return;
        }

        this.map = L.map('map-track', { zoomControl: false }).setView([this.currentData.origin.lat, this.currentData.origin.lng], 14);
        this.applyThemeTiles();

        this.bindDashboardControls();
        this.updateMarkers();
        await this.addRoute();
        this.drawHistoryPolyline();

        this.fetchInitialSnapshot();
        this.initWebSocket();
    }

    updateMarkers() {
        if (!this.map) {
            return;
        }

        const points = [
            {
                key: 'origin',
                coords: [this.currentData.origin.lat, this.currentData.origin.lng],
                iconType: 'origin',
                iconClass: 'fa-store',
                title: this.currentData.origin.name,
                subtitle: 'Local NovaGo',
            },
            {
                key: 'motorizado',
                coords: [this.currentData.motorizado.lat, this.currentData.motorizado.lng],
                iconType: 'motorizado',
                iconClass: 'fa-motorcycle',
                title: this.currentData.motorizado.name,
                subtitle: 'Ubicación en tiempo real',
            },
            {
                key: 'destination',
                coords: [this.currentData.destination.lat, this.currentData.destination.lng],
                iconType: 'destination',
                iconClass: 'fa-house',
                title: this.currentData.destination.name,
                subtitle: 'Punto de entrega',
            },
        ];

        points.forEach((point) => {
            if (!this.markers[point.key]) {
                this.markers[point.key] = L.marker(point.coords, {
                    icon: this.createCustomIcon(point.iconType, point.iconClass),
                    title: point.title,
                })
                    .bindPopup(`<strong>${point.title}</strong><br>${point.subtitle}`)
                    .addTo(this.map);
                return;
            }

            this.markers[point.key].setLatLng(point.coords);
        });
    }

    drawHistoryPolyline() {
        if (!this.map) {
            return;
        }

        if (this.historyPolyline) {
            this.map.removeLayer(this.historyPolyline);
            this.historyPolyline = null;
        }

        const latLngs = this.currentData.trackingHistory
            .map((point) => [Number.parseFloat(point.lat), Number.parseFloat(point.lng)])
            .filter((pair) => Number.isFinite(pair[0]) && Number.isFinite(pair[1]));

        if (latLngs.length < 2) {
            return;
        }

        this.historyPolyline = L.polyline(latLngs, {
            color: '#0ea5e9',
            weight: 4,
            opacity: 0.65,
            dashArray: '6 8',
        }).addTo(this.map);
    }

    createCustomIcon(type, iconClass) {
        const colors = {
            origin: '#10b981',
            motorizado: '#ff6a3d',
            destination: '#ef4444',
        };

        return L.divIcon({
            html: `
                <div style="
                    background: ${colors[type]};
                    border: 3px solid #fff;
                    border-radius: 50%;
                    width: 40px;
                    height: 40px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 1.05rem;
                    color: #ffffff;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
                ">
                    <i class="fas ${iconClass}" aria-hidden="true"></i>
                </div>
            `,
            className: `location-marker ${type}`,
            iconSize: [40, 40],
            iconAnchor: [20, 20],
            popupAnchor: [0, -20],
        });
    }

    async addRoute() {
        if (!this.map) {
            return;
        }

        const renderToken = ++this.routeRenderToken;

        if (this.route) {
            this.map.removeLayer(this.route);
            this.route = null;
        }

        const fallbackPoints = [
            [this.currentData.origin.lat, this.currentData.origin.lng],
            [this.currentData.motorizado.lat, this.currentData.motorizado.lng],
            [this.currentData.destination.lat, this.currentData.destination.lng],
        ];
        const routePoints = await this.resolveRoutePoints(fallbackPoints);

        if (renderToken !== this.routeRenderToken || !this.map) {
            return;
        }

        this.route = L.polyline(routePoints, {
            color: '#ff6a3d',
            opacity: 0.9,
            weight: 4,
            lineJoin: 'round',
            lineCap: 'round',
        }).addTo(this.map);

        setTimeout(() => {
            this.centerMapToRoute();
        }, 200);
    }

    updateDistance() {
        const distanceEl = document.getElementById('current-distance');
        const etaEl = document.getElementById('current-eta');

        if (distanceEl) {
            distanceEl.innerHTML = `<span class="icon"><i class="fas fa-location-dot" aria-hidden="true"></i></span> ${this.currentData.distanceKm.toFixed(2)} km`;
        }
        if (etaEl) {
            etaEl.innerHTML = `<span class="icon"><i class="fas fa-clock" aria-hidden="true"></i></span> ETA ${this.currentData.etaMin} min`;
        }
    }

    destroy() {
        if (this.autoGpsTimer) {
            window.clearInterval(this.autoGpsTimer);
        }
        if (this.autoGpsWatchId !== null && navigator.geolocation) {
            navigator.geolocation.clearWatch(this.autoGpsWatchId);
            this.autoGpsWatchId = null;
        }
        if (this.route && this.map) {
            this.map.removeLayer(this.route);
        }
        if (this.historyPolyline && this.map) {
            this.map.removeLayer(this.historyPolyline);
        }
        if (this.ws) {
            this.ws.close();
        }
        if (this.map) {
            this.map.remove();
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const mapContainer = document.getElementById('map-track');
    if (!mapContainer) {
        return;
    }

    const deliveryMap = new DeliveryMap({ mapElement: mapContainer });
    deliveryMap.initMap();
});
