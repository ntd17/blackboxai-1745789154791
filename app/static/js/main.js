document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    document.querySelectorAll('[data-tooltip]').forEach(element => {
        tippy(element, {
            content: element.getAttribute('data-tooltip'),
            placement: element.getAttribute('data-tooltip-placement') || 'top'
        });
    });

    // Initialize toast notifications
    window.showToast = function(message, type = 'success') {
        const container = document.getElementById('toast-container');
        if (!container) return;

        const toast = document.createElement('div');
        const bgColor = {
            success: 'bg-green-500',
            error: 'bg-red-500',
            warning: 'bg-yellow-500',
            info: 'bg-blue-500'
        }[type] || 'bg-blue-500';

        const icon = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        }[type] || 'fa-info-circle';

        toast.className = `${bgColor} text-white px-6 py-4 rounded-lg shadow-lg flex items-center space-x-2 mb-4`;
        toast.innerHTML = `
            <i class="fas ${icon}"></i>
            <span>${message}</span>
            <button onclick="this.parentElement.remove()" class="ml-auto">
                <i class="fas fa-times"></i>
            </button>
        `;

        container.appendChild(toast);
        setTimeout(() => toast.remove(), 5000);
    };

    // Handle mobile menu
    const mobileMenuButton = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');
    
    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener('click', () => {
            mobileMenu.classList.toggle('hidden');
        });
    }

    // Handle form submissions
    document.querySelectorAll('form[data-submit="ajax"]').forEach(form => {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();

            const submitButton = form.querySelector('[type="submit"]');
            const originalText = submitButton.textContent;
            submitButton.disabled = true;
            submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> ' + t('loading');

            try {
                const formData = new FormData(form);
                const response = await fetch(form.action, {
                    method: form.method,
                    body: formData,
                    headers: {
                        'Accept': 'application/json'
                    }
                });

                const data = await response.json();

                if (response.ok) {
                    showToast(data.message || t('success'), 'success');
                    if (data.redirect) {
                        window.location.href = data.redirect;
                    }
                } else {
                    showToast(data.error || t('error'), 'error');
                }
            } catch (error) {
                showToast(t('error_generic'), 'error');
            } finally {
                submitButton.disabled = false;
                submitButton.textContent = originalText;
            }
        });
    });

    // Handle signature canvas
    const signatureCanvas = document.getElementById('signature-canvas');
    if (signatureCanvas) {
        const ctx = signatureCanvas.getContext('2d');
        let isDrawing = false;
        let lastX = 0;
        let lastY = 0;

        function draw(e) {
            if (!isDrawing) return;
            ctx.beginPath();
            ctx.moveTo(lastX, lastY);
            ctx.lineTo(e.offsetX, e.offsetY);
            ctx.stroke();
            [lastX, lastY] = [e.offsetX, e.offsetY];
        }

        signatureCanvas.addEventListener('mousedown', (e) => {
            isDrawing = true;
            [lastX, lastY] = [e.offsetX, e.offsetY];
        });
        signatureCanvas.addEventListener('mousemove', draw);
        signatureCanvas.addEventListener('mouseup', () => isDrawing = false);
        signatureCanvas.addEventListener('mouseout', () => isDrawing = false);

        // Clear signature
        window.clearSignature = function() {
            ctx.clearRect(0, 0, signatureCanvas.width, signatureCanvas.height);
        };

        // Get signature data
        window.getSignatureData = function() {
            return signatureCanvas.toDataURL();
        };
    }

    // Handle contract filters
    const contractFilters = document.querySelectorAll('[data-filter]');
    if (contractFilters.length > 0) {
        contractFilters.forEach(filter => {
            filter.addEventListener('change', filterContracts);
        });

        function filterContracts() {
            const status = document.querySelector('[data-filter="status"]')?.value || 'all';
            const search = document.querySelector('[data-filter="search"]')?.value?.toLowerCase() || '';
            const dateFrom = document.querySelector('[data-filter="date-from"]')?.value || '';
            const dateTo = document.querySelector('[data-filter="date-to"]')?.value || '';

            document.querySelectorAll('.contract-item').forEach(item => {
                const itemStatus = item.dataset.status;
                const itemDate = item.dataset.date;
                const itemText = item.textContent.toLowerCase();

                const statusMatch = status === 'all' || status === itemStatus;
                const searchMatch = !search || itemText.includes(search);
                const dateMatch = (!dateFrom || itemDate >= dateFrom) && 
                                (!dateTo || itemDate <= dateTo);

                item.classList.toggle('hidden', !(statusMatch && searchMatch && dateMatch));
            });
        }
    }

    // Handle weather prediction updates
    const weatherInputs = document.querySelectorAll('[data-weather-input]');
    if (weatherInputs.length > 0) {
        let weatherTimeout;
        weatherInputs.forEach(input => {
            input.addEventListener('change', () => {
                clearTimeout(weatherTimeout);
                weatherTimeout = setTimeout(updateWeatherPrediction, 1000);
            });
        });

        async function updateWeatherPrediction() {
            const location = {
                city: document.querySelector('[data-weather-input="city"]').value,
                country: document.querySelector('[data-weather-input="country"]').value
            };
            const startDate = document.querySelector('[data-weather-input="start-date"]').value;
            const duration = document.querySelector('[data-weather-input="duration"]').value;

            if (!location.city || !location.country || !startDate || !duration) return;

            try {
                const response = await fetch('/api/ml/predict_rain', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        location,
                        planned_start_date: startDate,
                        planned_duration_days: parseInt(duration)
                    })
                });

                const data = await response.json();
                if (response.ok) {
                    updateWeatherUI(data.data);
                }
            } catch (error) {
                console.error('Weather prediction failed:', error);
            }
        }

        function updateWeatherUI(prediction) {
            const container = document.getElementById('weather-prediction');
            if (!container) return;

            container.classList.remove('hidden');
            
            // Update prediction values
            document.getElementById('rain-probability').textContent = 
                formatPercentage(prediction.rain_probability);
            document.getElementById('recommended-duration').textContent = 
                t('days', { count: prediction.recommended_duration });
            document.getElementById('confidence-score').textContent = 
                formatPercentage(prediction.confidence_score);

            // Update daily forecast
            const forecastGrid = document.getElementById('daily-forecast');
            if (forecastGrid && prediction.daily_forecasts) {
                forecastGrid.innerHTML = prediction.daily_forecasts.map(day => `
                    <div class="bg-white rounded-lg p-3 shadow-sm">
                        <div class="text-xs text-gray-500">${formatDate(day.date, 'short')}</div>
                        <div class="mt-2 flex items-center">
                            <i class="fas ${day.rain_prob > 0.5 ? 'fa-cloud-rain text-blue-500' : 'fa-sun text-yellow-500'} text-2xl"></i>
                            <div class="ml-2">
                                <div class="text-sm font-medium">${formatNumber(day.temp.day, { maximumFractionDigits: 1 })}°C</div>
                                <div class="text-xs text-gray-500">${formatPercentage(day.rain_prob)} ${t('rain')}</div>
                            </div>
                        </div>
                    </div>
                `).join('');
            }
        }
    }
});
