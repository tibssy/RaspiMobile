document.addEventListener('DOMContentLoaded', function() {
    const updateOverviewChartVisibility = (canvasId, msgId, hasData) => {
        const canvasElement = document.getElementById(canvasId);
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

    const salesCanvas = document.getElementById('overviewSalesChart');
    const salesMsgId = 'overviewSalesChartMsg';
    if (salesCanvas) {
        if (salesCanvas.dataset.labels && salesCanvas.dataset.sales) {
            try {
                const salesLabels = JSON.parse(salesCanvas.dataset.labels);
                const salesData = JSON.parse(salesCanvas.dataset.sales);

                if (salesLabels.length > 0 && salesData.length > 0 && salesLabels.length === salesData.length) {
                    const salesCtx = salesCanvas.getContext('2d');
                    new Chart(salesCtx, {
                        type: 'line',
                        data: {
                            labels: salesLabels,
                            datasets: [{
                                label: 'Daily Sales (€)', data: salesData,
                                borderColor: 'rgb(25, 135, 84)', backgroundColor: 'rgba(25, 135, 84, 0.1)',
                                tension: 0.1, fill: true, pointRadius: 2, pointHoverRadius: 5
                            }]
                        },
                        options: {
                            responsive: true, maintainAspectRatio: false,
                            scales: { y: { beginAtZero: true, ticks: { display: true } }, x: { ticks: { display: true } } },
                            plugins: { legend: { display: false }, tooltip: { enabled: true } }
                        }
                    });
                    updateOverviewChartVisibility('overviewSalesChart', salesMsgId, true);
                } else {
                    updateOverviewChartVisibility('overviewSalesChart', salesMsgId, false);
                }
            } catch(e) {
                console.error("Error parsing or initializing overview sales chart data:", e);
                console.error("Sales labels data attribute:", salesCanvas.dataset.labels);
                console.error("Sales data data attribute:", salesCanvas.dataset.sales);
                updateOverviewChartVisibility('overviewSalesChart', salesMsgId, false);
            }
        } else {
             console.log("Overview sales chart attributes missing.");
             updateOverviewChartVisibility('overviewSalesChart', salesMsgId, false);
        }
    } else {
        console.log("Overview sales chart canvas not found.");
    }

    const statusCanvas = document.getElementById('overviewOrderStatusChart');
    const statusMsgId = 'overviewOrderStatusChartMsg';
     if (statusCanvas) {
        if (statusCanvas.dataset.labels && statusCanvas.dataset.data && statusCanvas.dataset.colors) {
            try {
                const statusLabels = JSON.parse(statusCanvas.dataset.labels);
                const statusData = JSON.parse(statusCanvas.dataset.data);
                const statusColors = JSON.parse(statusCanvas.dataset.colors);

                if (statusLabels.length > 0 && statusData.length > 0 && statusLabels.length === statusData.length) {
                    const statusCtx = statusCanvas.getContext('2d');
                    new Chart(statusCtx, {
                        type: 'doughnut',
                        data: {
                            labels: statusLabels,
                            datasets: [{
                                label: 'Order Count',
                                data: statusData,
                                backgroundColor: statusColors,
                                hoverOffset: 4
                            }]
                        },
                        options: {
                            responsive: true, maintainAspectRatio: false,
                            plugins: { legend: { position: 'bottom', labels: { boxWidth: 12 } }, tooltip: { enabled: true } }
                        }
                    });
                    updateOverviewChartVisibility('overviewOrderStatusChart', statusMsgId, true);
                } else {
                    updateOverviewChartVisibility('overviewOrderStatusChart', statusMsgId, false);
                }
            } catch(e) {
                console.error("Error parsing or initializing overview status chart data:", e);
                console.error("Status labels data attribute:", statusCanvas.dataset.labels);
                console.error("Status data data attribute:", statusCanvas.dataset.data);
                console.error("Status colors data attribute:", statusCanvas.dataset.colors);
                updateOverviewChartVisibility('overviewOrderStatusChart', statusMsgId, false);
            }
        } else {
            console.log("Overview status chart attributes missing.");
            updateOverviewChartVisibility('overviewOrderStatusChart', statusMsgId, false);
        }
     } else {
        console.log("Overview status chart canvas not found.");
     }
});