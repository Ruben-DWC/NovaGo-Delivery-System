document.addEventListener('DOMContentLoaded', () => {
    const shell = document.querySelector('.logout-shell');
    const timerElement = document.getElementById('timer');
    const skipButton = document.getElementById('skip-redirect');

    if (!shell || !timerElement) {
        return;
    }

    const homeUrl = shell.dataset.homeUrl;
    if (!homeUrl) {
        return;
    }

    let secondsLeft = Number.parseInt(timerElement.textContent || '3', 10);

    const redirectNow = () => {
        window.location.href = homeUrl;
    };

    const countdownInterval = window.setInterval(() => {
        secondsLeft -= 1;
        timerElement.textContent = String(Math.max(secondsLeft, 0));

        if (secondsLeft <= 0) {
            window.clearInterval(countdownInterval);
            redirectNow();
        }
    }, 1000);

    if (skipButton) {
        skipButton.addEventListener('click', () => {
            window.clearInterval(countdownInterval);
            redirectNow();
        });
    }

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            window.clearInterval(countdownInterval);
            redirectNow();
        }
    });
});
