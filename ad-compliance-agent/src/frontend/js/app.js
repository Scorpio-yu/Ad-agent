/* ===== 广告合规审核 Agent - Frontend ===== */

const API_URL = '/api/v1/audit';
const STREAM_URL = '/api/v1/audit/stream';

const chatArea = document.getElementById('chatArea');
const adInput = document.getElementById('adInput');
const sendBtn = document.getElementById('sendBtn');
const charCount = document.getElementById('charCount');
const welcome = document.getElementById('welcome');

// ===== Event Listeners =====
sendBtn.addEventListener('click', handleSend);
adInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
    }
});
adInput.addEventListener('input', () => {
    charCount.textContent = adInput.value.length;
    autoResize();
});

// Example tags
document.querySelectorAll('.example-tag').forEach(tag => {
    tag.addEventListener('click', () => {
        adInput.value = tag.dataset.text;
        charCount.textContent = adInput.value.length;
        autoResize();
        handleSend();
    });
});

// ===== Core: Send (SSE streaming) =====
async function handleSend() {
    const content = adInput.value.trim();
    if (!content) return;
    if (sendBtn.disabled) return;

    if (welcome) welcome.remove();

    addUserMessage(content);
    adInput.value = '';
    charCount.textContent = '0';
    autoResize();

    // 添加流式预览框
    const streamEl = addStreamingBox();
    scrollToBottom();
    setInputDisabled(true);

    try {
        const res = await fetch(STREAM_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ad_content: content }),
        });

        if (!res.ok) throw new Error(`HTTP ${res.status}`);

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let fullText = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
                if (!line.startsWith('data: ')) continue;
                const data = line.slice(6);

                if (data === '[DONE]') continue;

                try {
                    const payload = JSON.parse(data);
                    if (payload.done) {
                        // 流结束，替换为结果卡片
                        streamEl.remove();
                        if (payload.result) {
                            addResultCard(payload.result);
                        }
                    } else if (payload.token) {
                        fullText += payload.token;
                        updateStreamingText(streamEl, fullText);
                    }
                } catch (e) {
                    // 跳过无法解析的行
                }
            }
        }

        // 如果没有收到 done 事件，尝试用完整文本渲染
        if (fullText && streamEl.parentNode) {
            streamEl.remove();
            try {
                const result = JSON.parse(fullText.replace(/```json\n?/g, '').replace(/```/g, ''));
                addResultCard(result);
            } catch (e) {
                addErrorMessage('响应格式异常：' + fullText.substring(0, 200));
            }
        }
    } catch (err) {
        streamEl.remove();
        addErrorMessage('网络错误，请检查后端是否启动');
    }

    setInputDisabled(false);
    adInput.focus();
}

// ===== Render: Streaming Box =====
function addStreamingBox() {
    const tpl = document.getElementById('streamingTemplate');
    const el = tpl.content.cloneNode(true);
    chatArea.appendChild(el);
    return chatArea.lastElementChild;
}

function updateStreamingText(el, text) {
    const textEl = el.querySelector('.streaming-text');
    if (textEl) {
        textEl.textContent = text;
        scrollToBottom();
    }
}

// ===== Render: User Message =====
function addUserMessage(text) {
    const tpl = document.getElementById('userMsgTemplate');
    const el = tpl.content.cloneNode(true);
    el.querySelector('.msg-content').textContent = text;
    chatArea.appendChild(el);
    scrollToBottom();
}

// ===== Render: Error =====
function addErrorMessage(msg) {
    const div = document.createElement('div');
    div.className = 'message bot-message';
    div.innerHTML = `
        <div class="msg-avatar">AI</div>
        <div class="msg-content"><div class="error-message">${escapeHtml(msg)}</div></div>
    `;
    chatArea.appendChild(div);
    scrollToBottom();
}

// ===== Render: Result Card =====
function addResultCard(data) {
    const tpl = document.getElementById('resultCardTemplate');
    const el = tpl.content.cloneNode(true);

    const isVio = data.is_violation;
    const risk = data.risk_level || 'none';

    const statusEl = el.querySelector('.result-status');
    statusEl.className = `result-status ${isVio ? 'violation' : 'compliant'}`;
    statusEl.innerHTML = `
        <span class="status-dot ${risk}"></span>
        <span>${isVio ? '违规' : '合规'}</span>
        <span class="risk-badge ${risk}">${riskLabel(risk)}</span>
    `;

    const body = el.querySelector('.result-body');
    let html = '';

    if (isVio && data.violation_type) {
        html += section('违规类型', data.violation_type);
    }

    if (data.risk_keywords && data.risk_keywords.length > 0) {
        const tags = data.risk_keywords.map(k => `<span class="keyword-tag">${escapeHtml(k)}</span>`).join('');
        html += `<div class="result-section">
            <div class="result-label">风险关键词</div>
            <div class="keyword-tags">${tags}</div>
        </div>`;
    }

    if (data.violation_clauses && data.violation_clauses.length > 0) {
        const laws = data.violation_clauses.map(c => `
            <li class="law-item">
                <div class="law-name">${escapeHtml(c.law)}</div>
                <div class="law-article">${escapeHtml(c.article)}</div>
                <div class="law-text">${escapeHtml(c.content)}</div>
            </li>
        `).join('');
        html += `<div class="result-section">
            <div class="result-label">法规依据</div>
            <ul class="law-list">${laws}</ul>
        </div>`;
    }

    html += section('判定理由', data.reason);

    if (data.suggestion) {
        html += `<div class="result-section">
            <div class="result-label">修改建议</div>
            <div class="suggestion-block">${escapeHtml(data.suggestion)}</div>
        </div>`;
    }

    body.innerHTML = html;
    chatArea.appendChild(el);
    scrollToBottom();
}

// ===== Helpers =====
function section(label, value) {
    return `<div class="result-section">
        <div class="result-label">${label}</div>
        <div class="result-value">${escapeHtml(value || '')}</div>
    </div>`;
}

function riskLabel(risk) {
    const map = { high: '高风险', medium: '中风险', low: '低风险', none: '合规' };
    return map[risk] || risk;
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function scrollToBottom() {
    chatArea.scrollTop = chatArea.scrollHeight;
}

function autoResize() {
    adInput.style.height = 'auto';
    adInput.style.height = Math.min(adInput.scrollHeight, 120) + 'px';
}

function setInputDisabled(disabled) {
    sendBtn.disabled = disabled;
    adInput.disabled = disabled;
}
