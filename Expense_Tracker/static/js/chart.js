/*! Chart.js v4.4.0 | (c) 2023 Chart.js Contributors | Released under the MIT license */
// Chart.js v4.4.0 minified code below (truncated for brevity in this example)
// In production, use the full minified file from the official CDN or npm package.

// Dashboard Pie and Bar Charts
window.renderDashboardCharts = function(pieLabels, pieData, barLabels, expensesData, incomeData) {
    if (document.getElementById('pieChart')) {
        const pieCtx = document.getElementById('pieChart').getContext('2d');
        new Chart(pieCtx, {
            type: 'pie',
            data: {
                labels: pieLabels,
                datasets: [{
                    data: pieData,
                    backgroundColor: [
                        '#4F8EF7', '#43D19E', '#FFB547', '#A084E8', '#FF6B6B',
                        '#36CFC9', '#FFD166', '#FF7EB9', '#3A86FF', '#B5C99A',
                        '#F67280', '#6C5B7B', '#355C7D', '#C06C84', '#F8B195'
                    ]
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { position: 'bottom' } },
                animation: { duration: 900 }
            }
        });
    }
    if (document.getElementById('barChart')) {
        const barCtx = document.getElementById('barChart').getContext('2d');
        new Chart(barCtx, {
            type: 'bar',
            data: {
                labels: barLabels,
                datasets: [
                    {
                        label: 'Expenses',
                        data: expensesData,
                        backgroundColor: '#ff6f61'
                    },
                    {
                        label: 'Income',
                        data: incomeData,
                        backgroundColor: '#40916c'
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: { legend: { position: 'bottom' } },
                animation: { duration: 900 },
                scales: { y: { beginAtZero: true } }
            }
        });
    }
};

// Budget Trend Chart
window.renderBudgetTrendChart = function(months, stayed, spent, budget) {
    if (document.getElementById('budgetTrendChart')) {
        const ctx = document.getElementById('budgetTrendChart').getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: months.map(m => m.slice(5,7) + '/' + m.slice(0,4)),
                datasets: [{
                    label: 'Stayed Within Budget',
                    data: stayed,
                    backgroundColor: stayed.map(v => v ? '#43D19E' : '#FF6B6B'),
                    borderRadius: 6,
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function(ctx) {
                                const idx = ctx.dataIndex;
                                return stayed[idx] ? 'Within Budget' : 'Over Budget';
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 1,
                        ticks: {
                            callback: function(value) { return value ? 'Yes' : 'No'; },
                            stepSize: 1
                        }
                    }
                }
            }
        });
    }
}; 