// ===========================
// Main JavaScript File
// ===========================

document.addEventListener('DOMContentLoaded', function() {
    console.log('NovaGo initialized');

    initializeThemeSwitcher();
    
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
// Export functions (if needed)
// ===========================
window.NovaGo = {
    showLoading,
    hideLoading,
    formatCurrency,
    showNotification
};
