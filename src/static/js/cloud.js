document.addEventListener("DOMContentLoaded", () => {
    const container = document.getElementById('tag-cloud');
    if (!container) return;

    const palette = [
        '#2980b9', '#27ae60', '#8e44ad', '#c0392b', '#d35400',
        '#16a085', '#2c3e50', '#1abc9c', '#e67e22', '#7f8c8d'
    ];

    const rawData = container.getAttribute('data-words');
    const wordsData = JSON.parse(rawData || '[]');

    if (wordsData.length === 0) {
        container.textContent = 'אין נתונים להצגה';
        return;
    }

    const maxCount = Math.max(...wordsData.map(w => w[1]));
    const minCount = Math.min(...wordsData.map(w => w[1]));

    wordsData.forEach((item, i) => {
        const word = item[0];
        const count = item[1];

        // Scale font between 13px and 36px relative to frequency
        const range = maxCount - minCount || 1;
        const fontSize = 13 + Math.round(((count - minCount) / range) * 23);

        const span = document.createElement('span');
        span.textContent = word;
        span.style.fontSize = `${fontSize}px`;
        span.style.color = palette[i % palette.length];
        span.style.margin = '6px';
        span.style.display = 'inline-block';
        span.style.fontWeight = fontSize > 22 ? '700' : '500';
        span.title = `${word}: ${count}`;

        container.appendChild(span);
    });
});