document.addEventListener("DOMContentLoaded", () => {
    const input  = document.getElementById('chat-input');
    const btn    = document.getElementById('chat-send');
    const status = document.getElementById('chat-status');
    const history = document.getElementById('chat-history');

    if (!input || !btn) return;

    function addMessage(text, role) {
        const wrapper = document.createElement('div');
        wrapper.className = `chat-msg ${role}`;

        const label = document.createElement('span');
        label.className = 'label';
        label.textContent = role === 'user' ? 'אתה' : 'סוכן AI';

        const bubble = document.createElement('div');
        bubble.className = 'bubble';
        bubble.textContent = text;

        wrapper.appendChild(label);
        wrapper.appendChild(bubble);
        history.appendChild(wrapper);
        history.scrollTop = history.scrollHeight;
    }

    async function sendQuestion() {
        const question = input.value.trim();
        if (!question) return;

        input.value = '';
        btn.disabled = true;
        addMessage(question, 'user');
        status.innerHTML = 'שולח שאלה… <span class="spinner"></span>';

        try {
            const res = await fetch('/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question })
            });
            const data = await res.json();

            if (data.answer) {
                addMessage(data.answer, 'bot');
                status.textContent = '';
            } else if (data.error) {
                addMessage(`שגיאה: ${data.error}`, 'bot');
                status.textContent = '';
            }
        } catch (err) {
            addMessage('שגיאת רשת — ודא ש-MindsDB פועל.', 'bot');
            status.textContent = '';
        } finally {
            btn.disabled = false;
            input.focus();
        }
    }

    btn.addEventListener('click', sendQuestion);
    input.addEventListener('keydown', e => {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendQuestion(); }
    });
});
