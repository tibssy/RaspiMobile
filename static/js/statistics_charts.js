/**
 * @file statistics_charts.js
 * @description Handles the initialization and dynamic updating of charts on the dashboard statistics page.
 * Uses Chart.js library to render line and bar charts for sales trends, order volume,
 * and top products. Allows users to change the date range for the charts via dropdowns,
 * fetching new data via AJAX requests.
 */

document.addEventListener("DOMContentLoaded", function () {
    const chartInstances = {};
    const statisticsContainer = document.getElementById(
        "statisticsChartsContainer"
    );

    /**
     * Formats a numeric value as Euro currency using Irish locale conventions.
     * @param {number|string} value - The numeric value to format.
     * @returns {string} The formatted currency string (e.g., "€1,234.56") or an empty string if input is invalid.
     */
    const formatCurrency = (value) => {
        const numValue = Number(value);
        if (isNaN(numValue)) return "";
        return new Intl.NumberFormat("en-IE", {
            style: "currency",
            currency: "EUR",
        }).format(numValue);
    };

    /**
     * Shows or hides a chart canvas and its corresponding "no data" message element.
     * @param {string} chartId - The ID of the chart's canvas element.
     * @param {string} msgId - The ID of the message element to show when there's no data.
     * @param {boolean} hasData - Whether there is data to display in the chart.
     */
    const updateChartVisibility = (chartId, msgId, hasData) => {
        const canvasElement = document.getElementById(chartId);
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
     * Initializes a Chart.js chart instance with given data and configuration.
     * Destroys any existing chart instance for the same canvas ID before creating a new one.
     * Determines the chart type and configuration based on the provided chartId.
     * Handles cases where there is no initial data to display.
     *
     * @param {string} chartId - The ID of the canvas element for the chart.
     * @param {Array<string>} initialLabels - Array of labels for the X-axis (or Y-axis for bar chart).
     * @param {Array<number>} initialData - Array of data points corresponding to the labels.
     */
    const initializeChart = (chartId, initialLabels, initialData) => {
        const canvasElement = document.getElementById(chartId);
        const msgId = `${chartId}Msg`;
        if (!canvasElement) {
            console.error(`Canvas element not found for chart ID: ${chartId}`);
            return;
        }
        const ctx = canvasElement.getContext("2d");
        let config = {};

        if (chartInstances[chartId]) {
            chartInstances[chartId].destroy();
        }

        if (chartId === "salesTrendChart") {
            config = {
                type: "line",
                data: {
                    labels: initialLabels,
                    datasets: [
                        {
                            label: "Daily Sales (€)",
                            data: initialData,
                            borderColor: "rgb(75, 192, 192)",
                            backgroundColor: "rgba(75, 192, 192, 0.2)",
                            tension: 0.1,
                            fill: true,
                            pointRadius: 3,
                            pointHoverRadius: 6,
                        },
                    ],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: { display: true, text: "Sales Amount (€)" },
                        },
                        x: { title: { display: true, text: "Date" } },
                    },
                    plugins: {
                        tooltip: {
                            mode: "index",
                            intersect: false,
                            callbacks: {
                                label: (context) =>
                                    `${
                                        context.dataset.label || ""
                                    }: ${formatCurrency(context.parsed.y)}`,
                            },
                        },
                        legend: { display: true, position: "top" },
                    },
                },
            };
        } else if (chartId === "orderVolumeChart") {
            config = {
                type: "line",
                data: {
                    labels: initialLabels,
                    datasets: [
                        {
                            label: "Daily Orders",
                            data: initialData,
                            borderColor: "rgb(255, 159, 64)",
                            backgroundColor: "rgba(255, 159, 64, 0.2)",
                            tension: 0.1,
                            fill: true,
                            pointRadius: 3,
                            pointHoverRadius: 6,
                        },
                    ],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: { display: true, text: "Number of Orders" },
                            ticks: { stepSize: 1 },
                        },
                        x: { title: { display: true, text: "Date" } },
                    },
                    plugins: {
                        tooltip: {
                            mode: "index",
                            intersect: false,
                            callbacks: {
                                label: (context) =>
                                    `${context.dataset.label || ""}: ${
                                        context.parsed.y
                                    }`,
                            },
                        },
                        legend: { display: true, position: "top" },
                    },
                },
            };
        } else if (chartId === "topProductsChart") {
            config = {
                type: "bar",
                data: {
                    labels: initialLabels,
                    datasets: [
                        {
                            label: "Total Revenue (€)",
                            data: initialData,
                            backgroundColor: "rgba(54, 162, 235, 0.6)",
                            borderColor: "rgb(54, 162, 235)",
                            borderWidth: 1,
                        },
                    ],
                },
                options: {
                    indexAxis: "y",
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            beginAtZero: true,
                            title: { display: true, text: "Total Revenue (€)" },
                            ticks: {
                                callback: (value) => formatCurrency(value),
                            },
                        },
                        y: { title: { display: true, text: "Product" } },
                    },
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: (context) =>
                                    `${
                                        context.dataset.label || ""
                                    }: ${formatCurrency(context.parsed.x)}`,
                            },
                        },
                    },
                },
            };
        } else {
            console.error(`Unknown chart configuration for ID: ${chartId}`);
            return;
        }

        if (
            initialLabels &&
            initialData &&
            initialLabels.length > 0 &&
            initialData.length > 0
        ) {
            chartInstances[chartId] = new Chart(ctx, config);
            updateChartVisibility(chartId, msgId, true);
        } else {
            updateChartVisibility(chartId, msgId, false);
        }
    };

    /**
     * Fetches new data for a specific chart based on the selected date range
     * and updates the corresponding Chart.js instance. Handles loading states
     * and potential errors during the fetch operation.
     *
     * @param {string} chartDOMId - The ID of the chart's canvas element.
     * @param {string} chartType - The logical type of the chart (e.g., 'sales', 'orders', 'topProducts'). Used for API call.
     * @param {string} range - The selected date range ('10', '30', 'all').
     * @param {HTMLElement} linkElement - The clicked range selector link element (for styling).
     */
    const updateChart = async (chartDOMId, chartType, range, linkElement) => {
        const chartWrapper = document
            .getElementById(chartDOMId)
            ?.closest("[data-chart-id]");
        if (!chartWrapper) {
            console.error(`Chart wrapper not found for ${chartDOMId}`);
            return;
        }

        const backendChartId = chartWrapper.dataset.chartId;
        const titleElement = document.getElementById(
            `${backendChartId}ChartTitle`
        );
        let loadingSpinner = null;

        if (titleElement) {
            if (!titleElement.querySelector(".fa-spinner")) {
                loadingSpinner = document.createElement("i");
                loadingSpinner.className = "fas fa-spinner fa-spin ms-2";
                titleElement.appendChild(loadingSpinner);
            }
        } else {
            console.warn(
                `Title element not found for ${backendChartId}ChartTitle`
            );
        }

        const dropdown = linkElement.closest(".range-dropdown");
        if (dropdown) {
            dropdown
                .querySelectorAll(".range-selector-link")
                .forEach((link) => link.classList.remove("active"));
            linkElement.classList.add("active");
        }

        try {
            const response = await fetch(
                `/dashboard/statistics/?fetch=true&chart_id=${backendChartId}&range=${range}`
            );
            if (!response.ok) {
                let errorMsg = `HTTP error! status: ${response.status}`;
                try {
                    const errorData = await response.json();
                    if (errorData && errorData.error) {
                        errorMsg = errorData.error;
                    }
                } catch (jsonError) {}
                throw new Error(errorMsg);
            }
            const newData = await response.json();

            const chartInstance = chartInstances[chartDOMId];
            const msgId = `${chartDOMId}Msg`;

            let baseTitleText = "";
            if (titleElement) {
                baseTitleText =
                    titleElement.firstChild &&
                    titleElement.firstChild.nodeType === Node.TEXT_NODE
                        ? titleElement.firstChild.textContent
                              .split("(")[0]
                              .trim()
                        : titleElement.textContent.split("(")[0].trim();
            }
            const suffix = `(${
                range === "10"
                    ? "Last 10 Days"
                    : range === "30"
                    ? "Last 30 Days"
                    : "All Time"
            })`;

            if (chartInstance && newData.labels && newData.data) {
                if (
                    newData.labels.length > 0 &&
                    newData.data.length > 0 &&
                    newData.labels.length === newData.data.length
                ) {
                    chartInstance.data.labels = newData.labels;
                    chartInstance.data.datasets[0].data = newData.data;
                    chartInstance.update();
                    updateChartVisibility(chartDOMId, msgId, true);
                    if (titleElement)
                        titleElement.firstChild.textContent = `${baseTitleText} ${suffix} `;
                } else {
                    updateChartVisibility(chartDOMId, msgId, false);
                    if (titleElement)
                        titleElement.firstChild.textContent = `${baseTitleText} ${suffix} - No Data `;
                }
            } else {
                console.warn(
                    `Chart instance missing or invalid data received for ${chartDOMId}`
                );
                updateChartVisibility(chartDOMId, msgId, false);
                if (titleElement)
                    titleElement.firstChild.textContent = `${baseTitleText} ${suffix} - Error Loading `;
            }
        } catch (error) {
            console.error(
                `Failed to fetch or update chart ${chartDOMId}:`,
                error
            );
            const msgId = `${chartDOMId}Msg`;
            updateChartVisibility(chartDOMId, msgId, false);
            if (titleElement)
                titleElement.firstChild.textContent = `${titleElement.textContent
                    .split("(")[0]
                    .trim()} - Error `;
        } finally {
            if (
                titleElement &&
                loadingSpinner &&
                titleElement.contains(loadingSpinner)
            ) {
                titleElement.removeChild(loadingSpinner);
            }
        }
    };

    /**
     * Loads and initializes all charts on the page based on data embedded
     * in data-* attributes on the canvas elements. Handles potential JSON
     * parsing errors during initialization.
     */
    const loadInitialCharts = () => {
        try {
            const salesCanvas = document.getElementById("salesTrendChart");
            let initialSalesLabels = [];
            let initialSalesData = [];
            if (salesCanvas && salesCanvas.dataset.labels)
                initialSalesLabels = JSON.parse(
                    salesCanvas.dataset.labels || "[]"
                );
            if (salesCanvas && salesCanvas.dataset.sales)
                initialSalesData = JSON.parse(
                    salesCanvas.dataset.sales || "[]"
                );
            initializeChart(
                "salesTrendChart",
                initialSalesLabels,
                initialSalesData
            );

            const ordersCanvas = document.getElementById("orderVolumeChart");
            let initialOrdersData = [];
            if (ordersCanvas && ordersCanvas.dataset.orders)
                initialOrdersData = JSON.parse(
                    ordersCanvas.dataset.orders || "[]"
                );
            initializeChart(
                "orderVolumeChart",
                initialSalesLabels,
                initialOrdersData
            );

            const topProductsCanvas =
                document.getElementById("topProductsChart");
            let initialTopLabels = [];
            let initialTopRevenue = [];
            if (topProductsCanvas && topProductsCanvas.dataset.labels)
                initialTopLabels = JSON.parse(
                    topProductsCanvas.dataset.labels || "[]"
                );
            if (topProductsCanvas && topProductsCanvas.dataset.revenue)
                initialTopRevenue = JSON.parse(
                    topProductsCanvas.dataset.revenue || "[]"
                );
            initializeChart(
                "topProductsChart",
                initialTopLabels,
                initialTopRevenue
            );
        } catch (e) {
            console.error("Error during initial chart JSON parsing:", e);
            const errorDiv = document.createElement("div");
            errorDiv.className = "alert alert-danger mt-3";
            errorDiv.textContent =
                "Could not load initial chart data due to a parsing error. Please check console.";
            if (statisticsContainer) {
                if (!statisticsContainer.querySelector(".alert.alert-danger")) {
                    statisticsContainer.prepend(errorDiv);
                }
            }
        }
    };

    // Use event delegation on the container for efficiency
    if (statisticsContainer) {
        statisticsContainer.addEventListener("click", function (event) {
            const targetLink = event.target.closest(".range-selector-link");
            if (targetLink) {
                event.preventDefault();
                const range = targetLink.dataset.range;
                const chartWrapper = targetLink.closest("[data-chart-id]");
                if (chartWrapper && range) {
                    const chartDOMId = chartWrapper.querySelector("canvas")?.id;
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
