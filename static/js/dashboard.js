// static/js/dashboard.js

async function fetchJson(url) {
    const res = await fetch(url, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    });
    if (!res.ok) {
        throw new Error("Request failed: " + res.status);
    }
    return await res.json();
}

/* =========================
   ПУБЛИЧНЫЙ ДАШБОРД (ГЛАВНАЯ)
   ========================= */
function initMainDashboard() {
    if (typeof Chart === "undefined") return;

    const revenueCanvas = document.getElementById("mainRevenueChart");
    const categoryCanvas = document.getElementById("mainCategoryChart");

    // Если на странице нет этих canvas — просто выходим
    if (!revenueCanvas && !categoryCanvas) return;

    let currentDays = 30;
    let revenueChart = null;
    let categoryChart = null;

    const rangeButtons = document.querySelectorAll("[data-range-days]");
    rangeButtons.forEach((btn) => {
        btn.addEventListener("click", () => {
            const days = parseInt(btn.dataset.rangeDays || "30", 10);
            currentDays = isNaN(days) ? 30 : days;

            rangeButtons.forEach((b) => b.classList.remove("filter-pill-active"));
            btn.classList.add("filter-pill-active");

            loadCharts();
        });
    });

    async function loadCharts() {
        try {
            const [revData, catData] = await Promise.all([
                fetchJson(`/api/stats/sales/?days=${currentDays}`),
                fetchJson(`/api/stats/categories/?days=${currentDays}`)
            ]);

            // Линейный график выручки
            if (revenueCanvas) {
                const ctx = revenueCanvas.getContext("2d");
                if (revenueChart) {
                    revenueChart.data.labels = revData.labels;
                    revenueChart.data.datasets[0].data = revData.values;
                    revenueChart.update();
                } else {
                    revenueChart = new Chart(ctx, {
                        type: "line",
                        data: {
                            labels: revData.labels,
                            datasets: [{
                                label: "Выручка (₽)",
                                data: revData.values,
                                fill: true,
                                borderWidth: 2,
                                tension: 0.3
                            }]
                        },
                        options: {
                            responsive: true,
                            scales: {
                                y: { beginAtZero: true }
                            },
                            plugins: {
                                legend: { display: true }
                            }
                        }
                    });
                }
            }

            // Круговая диаграмма категорий
            if (categoryCanvas) {
                const ctx2 = categoryCanvas.getContext("2d");
                if (categoryChart) {
                    categoryChart.data.labels = catData.labels;
                    categoryChart.data.datasets[0].data = catData.values;
                    categoryChart.update();
                } else {
                    categoryChart = new Chart(ctx2, {
                        type: "doughnut",
                        data: {
                            labels: catData.labels,
                            datasets: [{
                                data: catData.values
                            }]
                        },
                        options: {
                            responsive: true,
                            plugins: {
                                legend: {
                                    position: "bottom"
                                }
                            }
                        }
                    });
                }
            }
        } catch (e) {
            console.error("Ошибка загрузки статистики (главная):", e);
        }
    }

    loadCharts();
}

/* =========================
   АДМИНСКИЙ ДАШБОРД
   ========================= */
function initAdminDashboard() {
    if (typeof Chart === "undefined") return;

    const revenueCanvas = document.getElementById("adminRevenueChart");
    const categoryCanvas = document.getElementById("adminCategoryChart");

    if (!revenueCanvas && !categoryCanvas) return;

    let currentDays = 30;
    let revenueChart = null;
    let categoryChart = null;

    const rangeButtons = document.querySelectorAll("[data-admin-range-days]");
    rangeButtons.forEach((btn) => {
        btn.addEventListener("click", () => {
            const days = parseInt(btn.dataset.adminRangeDays || "30", 10);
            currentDays = isNaN(days) ? 30 : days;

            rangeButtons.forEach((b) => b.classList.remove("filter-pill-active"));
            btn.classList.add("filter-pill-active");

            loadCharts();
        });
    });

    async function loadCharts() {
        try {
            const [revData, catData] = await Promise.all([
                fetchJson(`/api/stats/sales/?days=${currentDays}`),
                fetchJson(`/api/stats/categories/?days=${currentDays}`)
            ]);

            if (revenueCanvas) {
                const ctx = revenueCanvas.getContext("2d");
                if (revenueChart) {
                    revenueChart.data.labels = revData.labels;
                    revenueChart.data.datasets[0].data = revData.values;
                    revenueChart.update();
                } else {
                    revenueChart = new Chart(ctx, {
                        type: "line",
                        data: {
                            labels: revData.labels,
                            datasets: [{
                                label: "Выручка (₽)",
                                data: revData.values,
                                fill: true,
                                borderWidth: 2,
                                tension: 0.3
                            }]
                        },
                        options: {
                            responsive: true,
                            scales: {
                                y: { beginAtZero: true }
                            }
                        }
                    });
                }
            }

            if (categoryCanvas) {
                const ctx2 = categoryCanvas.getContext("2d");
                if (categoryChart) {
                    categoryChart.data.labels = catData.labels;
                    categoryChart.data.datasets[0].data = catData.values;
                    categoryChart.update();
                } else {
                    categoryChart = new Chart(ctx2, {
                        type: "pie",
                        data: {
                            labels: catData.labels,
                            datasets: [{
                                data: catData.values
                            }]
                        },
                        options: {
                            responsive: true,
                            plugins: {
                                legend: {
                                    position: "bottom"
                                }
                            }
                        }
                    });
                }
            }
        } catch (e) {
            console.error("Ошибка загрузки статистики (админка):", e);
        }
    }

    loadCharts();
}
