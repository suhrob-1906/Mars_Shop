async function fetchJson(url) {
    const res = await fetch(url, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    });
    if (!res.ok) {
        throw new Error("Request failed: " + res.status);
    }
    return await res.json();
}

// Главная (если будешь использовать графики на обычной витрине)
function initMainDashboard() {
    if (!window.Chart) return;

    fetchJson('/api/stats/sales/?days=7')
        .then(revData => {
            const ctx = document.getElementById('mainRevenueChart');
            if (!ctx) return;
            new Chart(ctx.getContext('2d'), {
                type: 'line',
                data: {
                    labels: revData.labels,
                    datasets: [{
                        label: 'Выручка (₽)',
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
        })
        .catch(err => console.error(err));
}

// Админский дашборд
function initAdminDashboard() {
    if (!window.Chart) return;

    Promise.all([
        fetchJson('/api/stats/sales/?days=30'),
        fetchJson('/api/stats/categories/?days=30')
    ]).then(([revData, catData]) => {
        const revCtx = document.getElementById('adminRevenueChart');
        if (revCtx) {
            new Chart(revCtx.getContext('2d'), {
                type: 'line',
                data: {
                    labels: revData.labels,
                    datasets: [{
                        label: 'Выручка (₽)',
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

        const catCtx = document.getElementById('adminCategoryChart');
        if (catCtx) {
            new Chart(catCtx.getContext('2d'), {
                type: 'pie',
                data: {
                    labels: catData.labels,
                    datasets: [{
                        data: catData.values
                    }]
                },
                options: {
                    responsive: true
                }
            });
        }
    }).catch(err => console.error(err));
}
