document.addEventListener('DOMContentLoaded', function () {

    const chartInstances = {};
    const statisticsContainer = document.getElementById('statisticsChartsContainer');

    const formatCurrency = (value) => {
        const numValue = Number(value);
        if (isNaN(numValue)) return '';
        return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(numValue);
    };

    const updateChartVisibility = (chartId, msgId, hasData) => {
        const canvasElement = document.getElementById(chartId);
        const msgElement = document.getElementById(msgId);
        const chartContainer = canvasElement ? canvasElement.closest('.chart-container') : null;

        if (hasData && chartContainer) {
            chartContainer.classList.remove('d-none');
            if (msgElement) msgElement.classList.add('d-none');
        } else {
            if (chartContainer) chartContainer.classList.add('d-none');
            if (msgElement) msgElement.classList.remove('d-none');
        }
    };

    const initializeChart = (chartId, initialLabels, initialData) => {
        const canvasElement = document.getElementById(chartId);
        const msgId = `${chartId}Msg`;
        if (!canvasElement) {
            console.error(`Canvas element not found for chart ID: ${chartId}`);
            return;
        }
        const ctx = canvasElement.getContext('2d');
        let config = {};

        if (chartInstances[chartId]) {
            chartInstances[chartId].destroy();
        }

        if (chartId === 'salesTrendChart') {
            config = {
                type: 'line',
                data: { labels: initialLabels, datasets: [{ label: 'Daily Sales (€)', data: initialData, borderColor: 'rgb(75, 192, 192)', backgroundColor: 'rgba(75, 192, 192, 0.2)', tension: 0.1, fill: true, pointRadius: 3, pointHoverRadius: 6 }] },
                options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true, title: { display: true, text: 'Sales Amount (€)' } }, x: { title: { display: true, text: 'Date' } } }, plugins: { tooltip: { mode: 'index', intersect: false, callbacks: { label: (context) => `${context.dataset.label || ''}: ${formatCurrency(context.parsed.y)}` } }, legend: { display: true, position: 'top' } } }
            };
        } else if (chartId === 'orderVolumeChart') {
            config = {
                type: 'line',
                data: { labels: initialLabels, datasets: [{ label: 'Daily Orders', data: initialData, borderColor: 'rgb(255, 159, 64)', backgroundColor: 'rgba(255, 159, 64, 0.2)', tension: 0.1, fill: true, pointRadius: 3, pointHoverRadius: 6 }] },
                options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true, title: { display: true, text: 'Number of Orders' }, ticks: { stepSize: 1 } }, x: { title: { display: true, text: 'Date' } } }, plugins: { tooltip: { mode: 'index', intersect: false, callbacks: { label: (context) => `${context.dataset.label || ''}: ${context.parsed.y}` } }, legend: { display: true, position: 'top' } } }
            };
        } else if (chartId === 'topProductsChart') {
             config = {
                type: 'bar',
                data: { labels: initialLabels, datasets: [{ label: 'Total Revenue (€)', data: initialData, backgroundColor: 'rgba(54, 162, 235, 0.6)', borderColor: 'rgb(54, 162, 235)', borderWidth: 1 }] },
                options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false, scales: { x: { beginAtZero: true, title: { display: true, text: 'Total Revenue (€)' }, ticks: { callback: (value) => formatCurrency(value) } }, y: { title: { display: true, text: 'Product' } } }, plugins: { legend: { display: false }, tooltip: { callbacks: { label: (context) => `${context.dataset.label || ''}: ${formatCurrency(context.parsed.x)}` } } } }
            };
        } else {
            console.error(`Unknown chart configuration for ID: ${chartId}`);
            return;
        }

        if (initialLabels && initialData && initialLabels.length > 0 && initialData.length > 0) {
             chartInstances[chartId] = new Chart(ctx, config);
             updateChartVisibility(chartId, msgId, true);
        } else {
             updateChartVisibility(chartId, msgId, false);
        }
    };

    const updateChart = async (chartDOMId, chartType, range, linkElement) => {
        const chartWrapper = document.getElementById(chartDOMId).closest('[data-chart-id]');
        if (!chartWrapper) return;
        const backendChartId = chartWrapper.dataset.chartId;
        const titleElement = document.getElementById(`${backendChartId}ChartTitle`);
        const loadingSpinner = document.createElement('i');
        loadingSpinner.className = 'fas fa-spinner fa-spin ms-2';
        if (titleElement) titleElement.appendChild(loadingSpinner);

        const dropdown = linkElement.closest('.range-dropdown');
        if (dropdown) {
            dropdown.querySelectorAll('.range-selector-link').forEach(link => link.classList.remove('active'));
            linkElement.classList.add('active');
        }

        try {
            const response = await fetch(`/dashboard/statistics/?fetch=true&chart_id=${backendChartId}&range=${range}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const newData = await response.json();

            const chartInstance = chartInstances[chartDOMId];
            if (chartInstance && newData.labels && newData.data) {
                if (newData.labels.length > 0 && newData.data.length > 0) {
                    chartInstance.data.labels = newData.labels;
                    chartInstance.data.datasets[0].data = newData.data;
                    chartInstance.update();
                    updateChartVisibility(chartDOMId, `${chartDOMId}Msg`, true);
                    let suffix = `(${range === '10' ? 'Last 10 Days' : range === '30' ? 'Last 30 Days' : 'All Time'})`;
                    if (titleElement) titleElement.textContent = `${titleElement.textContent.split('(')[0].trim()} ${suffix}`;
                } else {
                    updateChartVisibility(chartDOMId, `${chartDOMId}Msg`, false);
                     if (titleElement) titleElement.textContent = `${titleElement.textContent.split('(')[0].trim()} (${range === '10' ? 'Last 10 Days' : range === '30' ? 'Last 30 Days' : 'All Time'}) - No Data`;
                }
            } else {
                 updateChartVisibility(chartDOMId, `${chartDOMId}Msg`, false);
            }

        } catch (error) {
            console.error(`Failed to fetch or update chart ${chartDOMId}:`, error);
        } finally {
             if (titleElement && loadingSpinner) titleElement.removeChild(loadingSpinner);
        }
    };

    const loadInitialCharts = () => {
         try {
            const salesCanvas = document.getElementById('salesTrendChart');
            let initialSalesLabels = [];
            let initialSalesData = [];
            if (salesCanvas && salesCanvas.dataset.labels) initialSalesLabels = JSON.parse(salesCanvas.dataset.labels || '[]');
            if (salesCanvas && salesCanvas.dataset.sales) initialSalesData = JSON.parse(salesCanvas.dataset.sales || '[]');
            initializeChart('salesTrendChart', initialSalesLabels, initialSalesData);

            const ordersCanvas = document.getElementById('orderVolumeChart');
            let initialOrdersData = [];
            if (ordersCanvas && ordersCanvas.dataset.orders) initialOrdersData = JSON.parse(ordersCanvas.dataset.orders || '[]');
            initializeChart('orderVolumeChart', initialSalesLabels, initialOrdersData);

            const topProductsCanvas = document.getElementById('topProductsChart');
            let initialTopLabels = [];
            let initialTopRevenue = [];
            if (topProductsCanvas && topProductsCanvas.dataset.labels) initialTopLabels = JSON.parse(topProductsCanvas.dataset.labels || '[]');
            if (topProductsCanvas && topProductsCanvas.dataset.revenue) initialTopRevenue = JSON.parse(topProductsCanvas.dataset.revenue || '[]');
            initializeChart('topProductsChart', initialTopLabels, initialTopRevenue);

         } catch(e) {
            console.error("Error during initial chart JSON parsing:", e);
            const errorDiv = document.createElement('div');
            errorDiv.className = 'alert alert-danger mt-3';
            errorDiv.textContent = 'Could not load initial chart data due to a parsing error. Please check console.';
            if(statisticsContainer) statisticsContainer.prepend(errorDiv);
         }
    };

    if (statisticsContainer) {
        statisticsContainer.addEventListener('click', function(event) {
            const targetLink = event.target.closest('.range-selector-link');
            if (targetLink) {
                event.preventDefault();
                const range = targetLink.dataset.range;
                const chartWrapper = targetLink.closest('[data-chart-id]');
                if (chartWrapper && range) {
                    const chartDOMId = chartWrapper.querySelector('canvas')?.id;
                     const chartType = chartWrapper.dataset.chartId;
                    if (chartDOMId) {
                         updateChart(chartDOMId, chartType, range, targetLink);
                    }
                }
            }
        });
    }

    loadInitialCharts();
});