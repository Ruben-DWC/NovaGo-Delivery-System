document.addEventListener('DOMContentLoaded', () => {
    const forms = document.querySelectorAll('[data-qty-form]');
    if (!forms.length) {
        return;
    }

    forms.forEach((form) => {
        const input = form.querySelector('.qty-input');
        const minus = form.querySelector('[data-qty-minus]');
        const plus = form.querySelector('[data-qty-plus]');

        if (!input || !minus || !plus) {
            return;
        }

        const getLimits = () => {
            const min = Number.parseInt(input.min || '0', 10);
            const max = Number.parseInt(input.max || '9999', 10);
            return {
                min: Number.isNaN(min) ? 0 : min,
                max: Number.isNaN(max) ? 9999 : max,
            };
        };

        minus.addEventListener('click', () => {
            const { min } = getLimits();
            const current = Number.parseInt(input.value || '0', 10);
            const next = Number.isNaN(current) ? min : Math.max(min, current - 1);
            input.value = String(next);
        });

        plus.addEventListener('click', () => {
            const { max } = getLimits();
            const current = Number.parseInt(input.value || '0', 10);
            const next = Number.isNaN(current) ? 1 : Math.min(max, current + 1);
            input.value = String(next);
        });
    });
});
