document.addEventListener("DOMContentLoaded", () => {
    const PALETTE = ['#2980b9', '#e74c3c', '#2ecc71', '#9b59b6', '#f39c12',
                     '#1abc9c', '#34495e', '#e67e22', '#3498db', '#95a5a6'];

    function makeChart(id, type, datasetOverride) {
        const canvas = document.getElementById(id);
        if (!canvas) return;
        const labels = JSON.parse(canvas.getAttribute('data-labels') || '[]');
        const values = JSON.parse(canvas.getAttribute('data-values') || '[]');
        new Chart(canvas.getContext('2d'), {
            type,
            data: {
                labels,
                datasets: [Object.assign({
                    data: values,
                    backgroundColor: PALETTE,
                    borderColor: PALETTE,
                    borderWidth: 1
                }, datasetOverride)]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: type === 'bar' || type === 'line' ? 'top' : 'bottom' }
                }
            }
        });
    }

    makeChart('articlesBySourceChart', 'bar', {
        label: 'מספר מאמרים',
        backgroundColor: '#2980b9',
        borderColor: '#2980b9',
        borderRadius: 6
    });

    makeChart('articlesByDayChart', 'line', {
        label: 'מאמרים שנאספו',
        borderColor: '#e74c3c',
        backgroundColor: 'rgba(231,76,60,0.15)',
        fill: true,
        tension: 0.4,
        pointRadius: 4
    });

    makeChart('articlesByCategoryChart', 'doughnut', {
        backgroundColor: PALETTE,
        hoverOffset: 8
    });

    makeChart('articlesByLanguageChart', 'pie', {
        backgroundColor: PALETTE
    });

    makeChart('trendsChart', 'line', {
        label: 'מגמת איסוף',
        borderColor: '#9b59b6',
        backgroundColor: 'rgba(155,89,182,0.15)',
        fill: true,
        tension: 0.4,
        pointRadius: 4
    });
});