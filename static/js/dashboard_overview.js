/**
 * @file dashboard_overview.js
 * @description Initializes charts (Sales Trend, Order Status) on the dashboard overview page.
 * Uses Chart.js library and reads initial data embedded in data-* attributes
 * on the corresponding canvas elements. Handles cases where data might be missing
 * or invalid, showing/hiding chart containers accordingly.
 */

document.addEventListener("DOMContentLoaded", function () {
    /**
     * Helper function to show or hide a chart canvas and its corresponding "no data" message element.
     * Finds the chart's container (assumed to have class '.chart-container') to toggle visibility.
     *
     * @param {string} canvasId - The ID of the chart's canvas element.
     * @param {string} msgId - The ID of the message element to show when there's no data.
     * @param {boolean} hasData - Whether there is valid data to display in the chart.
     */
    const updateOverviewChartVisibility = (canvasId, msgId, hasData) => {
        const canvasElement = document.getElementById(canvasId);
        const msgElement = document.getElementById(msgId);
        const chartContainer = canvasElement
            ? canvasElement.closest(".chart-container")
            : null;

        if (hasData && chartContainer) {
            chartContainer.classList.remove("d-none");
            if (msgElement) msgElement.classList.add("d-none");
        } else {
            if (chartContainer) chartContainer.classList.add("d-none");
            if (msgElement) msgElement.classList.remove("d-none");
        }
    };

    /**
     * Reference to the order status chart canvas element.
     * @type {HTMLCanvasElement|null}
     */
    const salesCanvas = document.getElementById("overviewSalesChart");
    /**
     * ID for the message element associated with the status chart.
     * @const {string}
     */
    const salesMsgId = "overviewSalesChartMsg";

    if (salesCanvas) {
        if (salesCanvas.dataset.labels && salesCanvas.dataset.sales) {
            try {
                const salesLabels = JSON.parse(salesCanvas.dataset.labels);
                const salesData = JSON.parse(salesCanvas.dataset.sales);

                if (
                    salesLabels.length > 0 &&
                    salesData.length > 0 &&
                    salesLabels.length === salesData.length
                ) {
                    const salesCtx = salesCanvas.getContext("2d");
                    new Chart(salesCtx, {
                        type: "line",
                        data: {
                            labels: salesLabels,
                            datasets: [
                                {
                                    label: "Daily Sales (€)",
                                    data: salesData,
                                    borderColor: "rgb(25, 135, 84)",
                                    backgroundColor: "rgba(25, 135, 84, 0.1)",
                                    tension: 0.1,
                                    fill: true,
                                    pointRadius: 2,
                                    pointHoverRadius: 5,
                                },
                            ],
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            scales: {
                                y: {
                                    beginAtZero: true,
                                    ticks: { display: true },
                                },
                                x: { ticks: { display: true } },
                            },
                            plugins: {
                                legend: { display: false },
                                tooltip: { enabled: true },
                            },
                        },
                    });
                    updateOverviewChartVisibility(
                        "overviewSalesChart",
                        salesMsgId,
                        true
                    );
                } else {
                    updateOverviewChartVisibility(
                        "overviewSalesChart",
                        salesMsgId,
                        false
                    );
                }
            } catch (e) {
                console.error(
                    "Error parsing or initializing overview sales chart data:",
                    e
                );
                console.error(
                    "Sales labels data attribute:",
                    salesCanvas.dataset.labels
                );
                console.error(
                    "Sales data data attribute:",
                    salesCanvas.dataset.sales
                );
                updateOverviewChartVisibility(
                    "overviewSalesChart",
                    salesMsgId,
                    false
                );
            }
        } else {
            updateOverviewChartVisibility(
                "overviewSalesChart",
                salesMsgId,
                false
            );
        }
    }

    const statusCanvas = document.getElementById("overviewOrderStatusChart");
    const statusMsgId = "overviewOrderStatusChartMsg";
    if (statusCanvas) {
        if (
            statusCanvas.dataset.labels &&
            statusCanvas.dataset.data &&
            statusCanvas.dataset.colors
        ) {
            try {
                const statusLabels = JSON.parse(statusCanvas.dataset.labels);
                const statusData = JSON.parse(statusCanvas.dataset.data);
                const statusColors = JSON.parse(statusCanvas.dataset.colors);

                if (
                    statusLabels.length > 0 &&
                    statusData.length > 0 &&
                    statusLabels.length === statusData.length
                ) {
                    const statusCtx = statusCanvas.getContext("2d");
                    new Chart(statusCtx, {
                        type: "doughnut",
                        data: {
                            labels: statusLabels,
                            datasets: [
                                {
                                    label: "Order Count",
                                    data: statusData,
                                    backgroundColor: statusColors,
                                    hoverOffset: 4,
                                },
                            ],
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                legend: {
                                    position: "bottom",
                                    labels: { boxWidth: 12 },
                                },
                                tooltip: { enabled: true },
                            },
                        },
                    });
                    updateOverviewChartVisibility(
                        "overviewOrderStatusChart",
                        statusMsgId,
                        true
                    );
                } else {
                    updateOverviewChartVisibility(
                        "overviewOrderStatusChart",
                        statusMsgId,
                        false
                    );
                }
            } catch (e) {
                console.error(
                    "Error parsing or initializing overview status chart data:",
                    e
                );
                console.error(
                    "Status labels data attribute:",
                    statusCanvas.dataset.labels
                );
                console.error(
                    "Status data data attribute:",
                    statusCanvas.dataset.data
                );
                console.error(
                    "Status colors data attribute:",
                    statusCanvas.dataset.colors
                );
                updateOverviewChartVisibility(
                    "overviewOrderStatusChart",
                    statusMsgId,
                    false
                );
            }
        } else {
            updateOverviewChartVisibility(
                "overviewOrderStatusChart",
                statusMsgId,
                false
            );
        }
    }
});
