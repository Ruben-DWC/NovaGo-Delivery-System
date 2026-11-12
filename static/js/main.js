// ===========================
// Main JavaScript File
// ===========================

document.addEventListener('DOMContentLoaded', function() {
    console.log('NovaGo initialized');

    initializeThemeSwitcher();
    
    // Quick Cart Offcanvas & Reactive Cart Sync
    initializeGlobalCartDrawer();
    
    // Auto-dismiss alerts after 5 seconds
    autoDissmissAlerts();
    
    // Initialize tooltips
    initializeTooltips();
    
    // Smooth scroll
    enableSmoothScroll();

    // Staggered section reveal
    initializeRevealOnScroll();

    // Interactive metrics
    initializeMetricCounters();

    // Button microinteractions
    initializeButtonMicroInteractions();

    // Post-auth success auto-redirects
    initializeSuccessRedirect();
});

// ===========================
// Auto-dismiss alerts
// ===========================
function autoDissmissAlerts() {
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
}

// ===========================
// Initialize Bootstrap Tooltips
// ===========================
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(
        document.querySelectorAll('[data-bs-toggle="tooltip"]')
    );
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// ===========================
// Smooth Scroll
// ===========================
function enableSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (href !== '#' && href !== '#!') {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });
}

// ===========================
// Reveal on scroll
// ===========================
function initializeRevealOnScroll() {
    const elements = document.querySelectorAll('.reveal-up');
    if (!elements.length) return;

    const observer = new IntersectionObserver((entries, obs) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                entry.target.classList.add('is-visible');
                obs.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.15,
        rootMargin: '0px 0px -40px 0px'
    });

    elements.forEach((element) => observer.observe(element));
}

// ===========================
// Theme switcher (auto/light/dark)
// ===========================
function initializeThemeSwitcher() {
    const html = document.documentElement;
    const optionButtons = document.querySelectorAll('[data-theme-option]');
    const media = window.matchMedia('(prefers-color-scheme: dark)');

    const getStoredPreference = () => localStorage.getItem('novago-theme') || 'auto';

    const resolveTheme = (pref) => {
        if (pref === 'dark' || pref === 'light') return pref;
        return media.matches ? 'dark' : 'light';
    };

    const applyTheme = (pref) => {
        const resolved = resolveTheme(pref);
        html.setAttribute('data-theme', resolved);
        html.setAttribute('data-bs-theme', resolved);
        html.setAttribute('data-theme-pref', pref);

        optionButtons.forEach((btn) => {
            const active = btn.dataset.themeOption === pref;
            btn.classList.toggle('active', active);
            btn.setAttribute('aria-pressed', active ? 'true' : 'false');
        });
    };

    applyTheme(getStoredPreference());

    optionButtons.forEach((button) => {
        button.addEventListener('click', () => {
            const pref = button.dataset.themeOption;
            localStorage.setItem('novago-theme', pref);
            applyTheme(pref);
        });
    });

    media.addEventListener('change', () => {
        if (getStoredPreference() === 'auto') {
            applyTheme('auto');
        }
    });
}

// ===========================
// Metric counters
// ===========================
function initializeMetricCounters() {
    const counters = document.querySelectorAll('.metric-value');
    if (!counters.length) return;

    const formatCounterValue = (value, element) => {
        const formatType = element.dataset.format;
        const fixed = Number(element.dataset.fixed || 0);
        const prefix = element.dataset.prefix || '';
        const suffix = element.dataset.suffix || '';

        let display = value;
        if (formatType === 'k') {
            display = `${(value / 1000).toFixed(0)}k`;
            return `${prefix}${display}${suffix}`;
        }

        if (fixed > 0) {
            display = Number(value).toFixed(fixed);
        } else {
            display = Math.round(value);
        }

        return `${prefix}${display}${suffix}`;
    };

    const animateCounter = (counter) => {
        const target = Number(counter.dataset.target || 0);
        const duration = 1200;
        const start = performance.now();

        const step = (now) => {
            const progress = Math.min((now - start) / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            const current = target * eased;
            counter.textContent = formatCounterValue(current, counter);
            if (progress < 1) requestAnimationFrame(step);
        };

        requestAnimationFrame(step);
    };

    const observer = new IntersectionObserver((entries, obs) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                animateCounter(entry.target);
                obs.unobserve(entry.target);
            }
        });
    }, { threshold: 0.5 });

    counters.forEach((counter) => observer.observe(counter));
}

// ===========================
// Buttons microinteractions
// ===========================
function initializeButtonMicroInteractions() {
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach((button) => {
        button.addEventListener('pointerdown', () => {
            button.style.transform = 'translateY(0) scale(0.98)';
        });
        button.addEventListener('pointerup', () => {
            button.style.transform = '';
        });
        button.addEventListener('pointerleave', () => {
            button.style.transform = '';
        });
    });
}

// ===========================
// Success screen redirects
// ===========================
function initializeSuccessRedirect() {
    const screen = document.querySelector('[data-success-redirect]');
    if (!screen) return;

    const destination = screen.dataset.destination;
    let seconds = Number(screen.dataset.seconds || 2);
    const countdown = screen.querySelector('[data-countdown]');

    const interval = setInterval(() => {
        seconds -= 1;
        if (countdown) countdown.textContent = String(Math.max(seconds, 0));
        if (seconds <= 0) {
            clearInterval(interval);
            window.location.assign(destination);
        }
    }, 1000);
}

// ===========================
// Loading Spinner
// ===========================
function showLoading() {
    let spinner = document.querySelector('.spinner-overlay');
    if (!spinner) {
        spinner = document.createElement('div');
        spinner.className = 'spinner-overlay';
        spinner.innerHTML = `
            <div class="spinner-border text-light" role="status" style="width: 3rem; height: 3rem;">
                <span class="visually-hidden">Cargando...</span>
            </div>
        `;
        document.body.appendChild(spinner);
    }
    spinner.classList.add('active');
}

function hideLoading() {
    const spinner = document.querySelector('.spinner-overlay');
    if (spinner) {
        spinner.classList.remove('active');
    }
}

// ===========================
// Utility Functions
// ===========================

// Format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('es-PE', {
        style: 'currency',
        currency: 'PEN'
    }).format(amount);
}

// Show notification
function showNotification(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
    alertDiv.style.zIndex = '9999';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alertDiv);
    
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// ===========================
// Global Reactive Cart Drawer
// ===========================
function initializeGlobalCartDrawer() {
    const drawerEl = document.getElementById('cartOffcanvas');
    const floatingPill = document.getElementById('floating-cart-pill');
    const floatingTotal = document.getElementById('floating-cart-total');
    const itemsListEl = document.getElementById('cartDrawerItemsList');
    const emptyEl = document.getElementById('cartDrawerEmpty');
    const footerEl = document.getElementById('cartDrawerFooter');
    const subtotalEl = document.getElementById('cartDrawerSubtotal');
    const shippingEl = document.getElementById('cartDrawerShipping');
    const totalEl = document.getElementById('cartDrawerTotal');

    const getCsrfToken = () => {
        const match = document.cookie.match(/(^|;)\s*csrftoken\s*=\s*([^;]+)/);
        if (match) return match[2];
        const input = document.querySelector('[name=csrfmiddlewaretoken]');
        return input ? input.value : '';
    };

    const updateCartUI = (data, options = {}) => {
        if (!data) return;

        // 1. Notify Alpine.js reactive components
        window.dispatchEvent(new CustomEvent('cart-updated', { detail: data }));

        // 2. Clear any conflicting inline styles from initial SSR render
        const drawerItemsEl = document.getElementById('cartDrawerItemsList');
        const drawerEmptyEl = document.getElementById('cartDrawerEmpty');
        const drawerFooterEl = document.getElementById('cartDrawerFooter');

        if (drawerItemsEl) drawerItemsEl.style.removeProperty('display');
        if (drawerEmptyEl) drawerEmptyEl.style.removeProperty('display');
        if (drawerFooterEl) drawerFooterEl.style.removeProperty('display');

        // 3. Navbar & floating badge counters
        document.querySelectorAll('.js-nav-cart-count').forEach(el => {
            el.textContent = data.cart_count || 0;
            if (data.cart_count > 0) {
                el.classList.remove('d-none');
                el.style.removeProperty('display');
                el.classList.remove('cart-pulse-anim');
                void el.offsetWidth;
                el.classList.add('cart-pulse-anim');
            } else {
                el.classList.add('d-none');
            }
        });

        // 4. Floating action pill
        if (floatingPill) {
            if (data.cart_count > 0) {
                floatingPill.classList.remove('is-hidden');
            } else {
                floatingPill.classList.add('is-hidden');
            }
        }
        if (floatingTotal && data.cart_total !== undefined) {
            floatingTotal.textContent = 'S/ ' + Number(data.cart_total).toFixed(2);
        }

        // 5. Offcanvas totals
        if (subtotalEl && data.cart_subtotal !== undefined) {
            subtotalEl.textContent = 'S/ ' + Number(data.cart_subtotal).toFixed(2);
        }
        if (shippingEl && data.cart_shipping !== undefined) {
            shippingEl.textContent = 'S/ ' + Number(data.cart_shipping).toFixed(2);
        }
        if (totalEl && data.cart_total !== undefined) {
            totalEl.textContent = 'S/ ' + Number(data.cart_total).toFixed(2);
        }

        // 6. Vanilla DOM fallback ONLY when Alpine.js is not active
        if (!window.Alpine && drawerItemsEl && drawerEmptyEl && drawerFooterEl) {
            if (data.items && data.items.length > 0) {
                drawerItemsEl.classList.remove('d-none');
                drawerEmptyEl.classList.add('d-none');
                drawerFooterEl.classList.remove('d-none');

                let html = '';
                data.items.forEach(item => {
                    html += `
                    <article class="cart-drawer-item p-2 rounded border d-flex gap-3 align-items-center" data-item-id="${item.id}">
                        <img src="${item.imagen_url}" alt="${item.nombre}" class="cart-drawer-thumb rounded" width="60" height="60" style="object-fit: cover;">
                        <div class="flex-grow-1 min-w-0">
                            <h6 class="cart-drawer-item-title mb-1 text-truncate fw-bold" title="${item.nombre}">${item.nombre}</h6>
                            <div class="d-flex justify-content-between align-items-center">
                                <span class="small text-muted">S/ ${Number(item.precio).toFixed(2)}</span>
                                <strong class="text-brand small">S/ ${Number(item.subtotal).toFixed(2)}</strong>
                            </div>
                            <div class="d-flex justify-content-between align-items-center mt-2">
                                <div class="qty-control qty-control-sm">
                                    <button type="button" class="qty-btn js-drawer-qty-minus" data-id="${item.id}" aria-label="Disminuir cantidad">-</button>
                                    <span class="qty-input-text px-2 small fw-bold">${item.cantidad}</span>
                                    <button type="button" class="qty-btn js-drawer-qty-plus" data-id="${item.id}" data-max="${item.stock || 999}" aria-label="Aumentar cantidad">+</button>
                                </div>
                                <button type="button" class="btn btn-link text-danger p-0 js-drawer-remove" data-id="${item.id}" title="Quitar producto">
                                    <i class="fas fa-trash-can small"></i>
                                </button>
                            </div>
                        </div>
                    </article>`;
                });
                drawerItemsEl.innerHTML = html;
            } else {
                drawerItemsEl.classList.add('d-none');
                drawerEmptyEl.classList.remove('d-none');
                drawerFooterEl.classList.add('d-none');
            }
        }

        // 7. Toast feedback
        const toastEl = document.getElementById('cartToast');
        const toastMsg = document.getElementById('cartToastMsg');
        if (options.showToast && toastEl && toastMsg && typeof bootstrap !== 'undefined') {
            toastMsg.textContent = options.message || data.message || 'Producto agregado al carrito.';
            const toast = bootstrap.Toast.getOrCreateInstance(toastEl, { delay: 3500 });
            toast.show();
        }

        // 8. Auto-open drawer if requested
        if (options.openDrawer && drawerEl && typeof bootstrap !== 'undefined') {
            const offcanvas = bootstrap.Offcanvas.getOrCreateInstance(drawerEl);
            offcanvas.show();
        }
    };

    // Global listener for Add to Cart forms (.js-add-cart-form)
    document.addEventListener('submit', function(e) {
        const form = e.target.closest('.js-add-cart-form');
        if (!form) return;

        e.preventDefault();
        const action = form.action;
        const formData = new FormData(form);
        const productName = form.getAttribute('data-product-name') || '';

        fetch(action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json'
            }
        })
        .then(res => {
            if (res.ok) return res.json();
            throw new Error('Respuesta no JSON');
        })
        .then(data => {
            updateCartUI(data, {
                showToast: true,
                message: productName ? `¡"${productName}" agregado al carrito!` : data.message,
                openDrawer: true
            });
        })
        .catch(() => {
            form.submit();
        });
    });

    // Drawer quantity buttons and remove button
    if (drawerEl) {
        drawerEl.addEventListener('click', function(e) {
            const plusBtn = e.target.closest('.js-drawer-qty-plus');
            const minusBtn = e.target.closest('.js-drawer-qty-minus');
            const removeBtn = e.target.closest('.js-drawer-remove');

            if (plusBtn) {
                const id = plusBtn.getAttribute('data-id');
                const max = parseInt(plusBtn.getAttribute('data-max') || '999', 10);
                const currentText = plusBtn.parentElement.querySelector('.qty-input-text');
                const current = parseInt(currentText ? currentText.textContent : '1', 10);
                if (current >= max) return;

                const formData = new FormData();
                formData.append('quantity', current + 1);

                fetch(`/orders/carrito/actualizar/${id}/`, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'Accept': 'application/json',
                        'X-CSRFToken': getCsrfToken()
                    }
                })
                .then(res => res.json())
                .then(data => updateCartUI(data))
                .catch(err => console.error(err));
            }

            if (minusBtn) {
                const id = minusBtn.getAttribute('data-id');
                const currentText = minusBtn.parentElement.querySelector('.qty-input-text');
                const current = parseInt(currentText ? currentText.textContent : '1', 10);

                if (current <= 1) {
                    fetch(`/orders/carrito/eliminar/${id}/`, {
                        method: 'POST',
                        headers: {
                            'X-Requested-With': 'XMLHttpRequest',
                            'Accept': 'application/json',
                            'X-CSRFToken': getCsrfToken()
                        }
                    })
                    .then(res => res.json())
                    .then(data => updateCartUI(data))
                    .catch(err => console.error(err));
                } else {
                    const formData = new FormData();
                    formData.append('quantity', current - 1);

                    fetch(`/orders/carrito/actualizar/${id}/`, {
                        method: 'POST',
                        body: formData,
                        headers: {
                            'X-Requested-With': 'XMLHttpRequest',
                            'Accept': 'application/json',
                            'X-CSRFToken': getCsrfToken()
                        }
                    })
                    .then(res => res.json())
                    .then(data => updateCartUI(data))
                    .catch(err => console.error(err));
                }
            }

            if (removeBtn) {
                const id = removeBtn.getAttribute('data-id');
                fetch(`/orders/carrito/eliminar/${id}/`, {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'Accept': 'application/json',
                        'X-CSRFToken': getCsrfToken()
                    }
                })
                .then(res => res.json())
                .then(data => updateCartUI(data))
                .catch(err => console.error(err));
            }
        });
    }

    window.NovaGoUpdateCartUI = updateCartUI;
}

// ===========================
// Export functions (if needed)
// ===========================
window.NovaGo = {
    showLoading,
    hideLoading,
    formatCurrency,
    showNotification
};
