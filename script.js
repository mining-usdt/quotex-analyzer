/**
 * Quotex Ultimate Bot - JavaScript Frontend
 * الإدارة الكاملة للواجهة والاتصال بالسيرفر
 */

// ================================================================
// ===== المتغيرات العامة =====
// ================================================================

const API = window.location.origin;
let allPairs = [];
let isConnected = false;
let isTrading = false;
let autoRefreshInterval = null;
let lastResult = null;
let logUpdateInterval = null;
let selectedSymbol = '';
let strongSignalInterval = null;
let isAnalyzing = false;

// ================================================================
// ===== DOM Elements =====
// ================================================================

const elements = {
    symbolSelect: document.getElementById('symbolSelect'),
    limitSelect: document.getElementById('limitSelect'),
    tradeAmount: document.getElementById('tradeAmount'),
    confidenceThreshold: document.getElementById('confidenceThreshold'),
    analyzeBtn: document.getElementById('analyzeBtn'),
    strongSignalBtn: document.getElementById('strongSignalBtn'),
    executeBtn: document.getElementById('executeBtn'),
    connectBtn: document.getElementById('connectBtn'),
    disconnectBtn: document.getElementById('disconnectBtn'),
    startTradingBtn: document.getElementById('startTradingBtn'),
    stopTradingBtn: document.getElementById('stopTradingBtn'),
    accountSelect: document.getElementById('accountSelect'),
    connectionStatus: document.getElementById('connectionStatus'),
    connectionText: document.getElementById('connectionText'),
    balanceDisplay: document.getElementById('balanceDisplay'),
    dailyLossDisplay: document.getElementById('dailyLossDisplay'),
    winRateDisplay: document.getElementById('winRateDisplay'),
    resultContainer: document.getElementById('resultContainer'),
    logContainer: document.getElementById('logContainer'),
    timeDisplay: document.getElementById('timeDisplay'),
    signalsPanel: document.getElementById('signalsPanel'),
    strongSignalsContainer: document.getElementById('strongSignalsContainer'),
    currentSignal: document.getElementById('currentSignal'),
    currentConfidence: document.getElementById('currentConfidence'),
    currentPrice: document.getElementById('currentPrice'),
    currentTimeRemaining: document.getElementById('currentTimeRemaining'),
    currentVolatility: document.getElementById('currentVolatility'),
};

// ================================================================
// ===== التهيئة =====
// ================================================================

document.addEventListener('DOMContentLoaded', async () => {
    await loadMarkets();
    setupEvents();
    updateTime();
    setInterval(updateTime, 1000);
    startLogPolling();
    startStatusPolling();
    
    // تحديث الرصيد كل 10 ثواني إذا كان متصلاً
    setInterval(async () => {
        if (isConnected) {
            await updateStatus();
        }
    }, 10000);
});

// ================================================================
// ===== تحميل الأزواج =====
// ================================================================

async function loadMarkets() {
    try {
        const res = await fetch(`${API}/api/v1/markets`);
        const data = await res.json();
        
        if (data.data && data.data.length > 0) {
            allPairs = data.data;
            elements.symbolSelect.innerHTML = data.data.map(p =>
                `<option value="${p.symbol}">${p.name} (${p.symbol})</option>`
            ).join('');
            selectedSymbol = elements.symbolSelect.value;
        } else {
            elements.symbolSelect.innerHTML = '<option value="">لا توجد أصول</option>';
        }
    } catch (e) {
        console.error('Error loading markets:', e);
        elements.symbolSelect.innerHTML = '<option value="">⚠️ خطأ في الاتصال</option>';
    }
}

// ================================================================
// ===== إعداد الأحداث =====
// ================================================================

function setupEvents() {
    elements.symbolSelect.onchange = () => {
        selectedSymbol = elements.symbolSelect.value;
    };
    
    elements.analyzeBtn.onclick = analyze;
    elements.strongSignalBtn.onclick = findStrongSignal;
    elements.executeBtn.onclick = executeManualTrade;
    elements.connectBtn.onclick = connectToQuotex;
    elements.disconnectBtn.onclick = disconnectFromQuotex;
    elements.startTradingBtn.onclick = startTrading;
    elements.stopTradingBtn.onclick = stopTrading;
    
    // Enter key for analyze
    elements.symbolSelect.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') analyze();
    });
}

// ================================================================
// ===== الاتصال بـ Quotex =====
// ================================================================

async function connectToQuotex() {
    const accountType = elements.accountSelect.value;
    const btn = elements.connectBtn;
    
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> جاري الاتصال...';
    
    showLoading('🔌 جاري الاتصال بـ Quotex...', `حساب ${accountType === 'demo' ? 'تجريبي' : 'حقيقي'}`);
    
    try {
        const res = await fetch(`${API}/api/v2/connect?account_type=${accountType}`, {
            method: 'POST'
        });
        const data = await res.json();
        
        if (data.status === 'success' || data.status === 'already_connected') {
            isConnected = true;
            elements.connectionStatus.className = 'status-connection connected';
            elements.connectionStatus.textContent = '🟢 متصل';
            elements.connectionText.className = 'value connected';
            elements.connectionText.textContent = '✅ متصل';
            elements.connectBtn.style.display = 'none';
            elements.disconnectBtn.style.display = 'inline-flex';
            elements.startTradingBtn.disabled = false;
            elements.executeBtn.disabled = false;
            
            if (data.balance !== undefined) {
                elements.balanceDisplay.textContent = `$${data.balance.toFixed(2)}`;
                elements.balanceDisplay.className = 'value connected';
            }
            
            addLog('✅ تم الاتصال بحساب ' + (accountType === 'demo' ? 'تجريبي' : 'حقيقي'));
            await updateStatus();
            showPlaceholder('✅ تم الاتصال بنجاح', 'الآن يمكنك بدء التداول التلقائي');
        } else {
            showError(`❌ ${data.message || 'فشل الاتصال'}`);
            addLog('❌ فشل الاتصال: ' + (data.message || 'خطأ غير معروف'));
        }
    } catch (e) {
        showError(`❌ خطأ في الاتصال: ${e.message}`);
        addLog('❌ خطأ في الاتصال: ' + e.message);
    }
    
    btn.disabled = false;
    btn.innerHTML = '<i class="fas fa-plug"></i> اتصال';
}

// ================================================================
// ===== قطع الاتصال =====
// ================================================================

async function disconnectFromQuotex() {
    try {
        await fetch(`${API}/api/v2/disconnect`, { method: 'POST' });
        isConnected = false;
        isTrading = false;
        
        elements.connectionStatus.className = 'status-connection';
        elements.connectionStatus.textContent = '🔴 غير متصل';
        elements.connectionText.className = 'value disconnected';
        elements.connectionText.textContent = '❌ غير متصل';
        elements.connectBtn.style.display = 'inline-flex';
        elements.disconnectBtn.style.display = 'none';
        elements.startTradingBtn.disabled = true;
        elements.startTradingBtn.style.display = 'inline-flex';
        elements.stopTradingBtn.style.display = 'none';
        elements.executeBtn.disabled = true;
        elements.balanceDisplay.className = 'value disconnected';
        
        if (strongSignalInterval) {
            clearInterval(strongSignalInterval);
            strongSignalInterval = null;
        }
        
        addLog('⏹️ تم قطع الاتصال بـ Quotex');
        showPlaceholder('⏹️ تم قطع الاتصال', 'يمكنك إعادة الاتصال في أي وقت');
    } catch (e) {
        console.error('Disconnect error:', e);
    }
}

// ================================================================
// ===== بدء التداول =====
// ================================================================

async function startTrading() {
    const symbol = elements.symbolSelect.value;
    if (!symbol) {
        alert('الرجاء اختيار زوج أولاً');
        return;
    }
    
    const btn = elements.startTradingBtn;
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> جاري البدء...';
    
    try {
        const res = await fetch(`${API}/api/v2/enable-trading?symbol=${symbol}`, {
            method: 'POST'
        });
        const data = await res.json();
        
        if (data.status === 'success' || data.status === 'already_running') {
            isTrading = true;
            elements.startTradingBtn.style.display = 'none';
            elements.stopTradingBtn.style.display = 'inline-flex';
            addLog(`🚀 بدء التداول التلقائي على ${symbol}`);
            showPlaceholder('🚀 التداول التلقائي مفعل', `جاري التداول على ${symbol}`);
        } else {
            addLog('❌ فشل بدء التداول: ' + (data.message || 'خطأ غير معروف'));
            showError(`❌ ${data.message || 'فشل بدء التداول'}`);
        }
    } catch (e) {
        addLog('❌ خطأ في بدء التداول: ' + e.message);
        showError(`❌ ${e.message}`);
    }
    
    btn.disabled = false;
    btn.innerHTML = '<i class="fas fa-play"></i> بدء التداول';
}

// ================================================================
// ===== إيقاف التداول =====
// ================================================================

async function stopTrading() {
    try {
        await fetch(`${API}/api/v2/disable-trading`, { method: 'POST' });
        isTrading = false;
        elements.startTradingBtn.style.display = 'inline-flex';
        elements.stopTradingBtn.style.display = 'none';
        addLog('⏹️ تم إيقاف التداول التلقائي');
        showPlaceholder('⏹️ تم إيقاف التداول', 'يمكنك البدء مرة أخرى في أي وقت');
    } catch (e) {
        addLog('❌ خطأ في إيقاف التداول: ' + e.message);
    }
}

// ================================================================
// ===== التحليل =====
// ================================================================

async function analyze() {
    if (isAnalyzing) return;
    
    const symbol = elements.symbolSelect.value;
    const limit = elements.limitSelect.value;
    
    if (!symbol) {
        showError('⚠️ الرجاء اختيار زوج أولاً');
        return;
    }
    
    isAnalyzing = true;
    elements.analyzeBtn.disabled = true;
    elements.analyzeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> جاري التحليل...';
    
    showLoading('🔍 جاري التحليل العميق...', 'جاري حساب 12 استراتيجية و 15 مؤشراً...');
    
    try {
        const res = await fetch(`${API}/api/v2/analyze/${symbol}?limit=${limit}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        if (data.error) throw new Error(data.error);
        
        lastResult = data;
        displayResult(data);
        updateStatsBar(data);
        
    } catch (e) {
        showError(`❌ ${e.message}`);
    }
    
    isAnalyzing = false;
    elements.analyzeBtn.disabled = false;
    elements.analyzeBtn.innerHTML = '<i class="fas fa-rocket"></i> تحليل';
}

// ================================================================
// ===== البحث عن إشارة قوية =====
// ================================================================

async function findStrongSignal() {
    if (isAnalyzing) return;
    
    const symbol = elements.symbolSelect.value;
    if (!symbol) {
        showError('⚠️ الرجاء اختيار زوج أولاً');
        return;
    }
    
    isAnalyzing = true;
    elements.strongSignalBtn.disabled = true;
    elements.strongSignalBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> جاري البحث...';
    
    showLoading('🔍 جاري البحث عن إشارة قوية...', `جاري فحص ${symbol}...`);
    
    try {
        const res = await fetch(`${API}/api/v2/strong-signal?symbol=${symbol}`);
        const data = await res.json();
        
        if (data.status === 'success' && data.signal) {
            lastResult = data.signal;
            displayResult(data.signal);
            updateStatsBar(data.signal);
            addLog(`🔥 إشارة قوية على ${data.signal.symbol} (ثقة: ${data.signal.confidence}%)`);
            showStrongSignals([data.signal]);
        } else if (data.status === 'no_signal') {
            showError('❌ لا توجد إشارات قوية حالياً');
            addLog('⏳ لا توجد إشارات قوية');
        } else {
            showError(`❌ ${data.message || 'خطأ غير معروف'}`);
        }
    } catch (e) {
        showError(`❌ ${e.message}`);
        addLog(`❌ خطأ في البحث: ${e.message}`);
    }
    
    isAnalyzing = false;
    elements.strongSignalBtn.disabled = false;
    elements.strongSignalBtn.innerHTML = '<i class="fas fa-bolt"></i> إشارة قوية';
}

// ================================================================
// ===== تنفيذ يدوي =====
// ================================================================

async function executeManualTrade() {
    if (!isConnected) {
        alert('❌ الرجاء الاتصال بـ Quotex أولاً');
        return;
    }
    
    const symbol = elements.symbolSelect.value;
    const amount = parseFloat(elements.tradeAmount.value) || 1.0;
    
    if (!symbol) {
        alert('الرجاء اختيار زوج أولاً');
        return;
    }
    
    if (!lastResult) {
        alert('الرجاء إجراء تحليل أولاً');
        return;
    }
    
    const action = lastResult.action || 'NEUTRAL';
    if (!action.includes('BUY') && !action.includes('SELL')) {
        alert('⚠️ لا توجد إشارة واضحة. الرجاء الانتظار.');
        return;
    }
    
    const direction = action.includes('BUY') ? 'CALL' : 'PUT';
    const confidence = lastResult.confidence || 0;
    const threshold = parseInt(elements.confidenceThreshold.value) || 85;
    
    if (confidence < threshold) {
        const confirm = window.confirm(`⚠️ الثقة منخفضة (${confidence}% < ${threshold}%). هل تريد المتابعة؟`);
        if (!confirm) return;
    }
    
    showLoading('📤 جاري تنفيذ الصفقة...', `${symbol} | ${direction} | $${amount.toFixed(2)}`);
    
    try {
        const res = await fetch(
            `${API}/api/v2/execute-trade?symbol=${symbol}&direction=${direction}&amount=${amount}&expiry=60`,
            { method: 'POST' }
        );
        const data = await res.json();
        
        if (data.success) {
            showSuccess(`✅ تم تنفيذ الصفقة`, `${symbol} | ${direction} | $${amount.toFixed(2)}`);
            addLog(`✅ ${symbol} | ${direction} | $${amount.toFixed(2)}`);
            await updateStatus();
        } else {
            showError(`❌ فشل التنفيذ: ${data.error || 'خطأ غير معروف'}`);
            addLog(`❌ فشل التنفيذ: ${data.error || 'خطأ غير معروف'}`);
        }
    } catch (e) {
        showError(`❌ ${e.message}`);
    }
}

// ================================================================
// ===== عرض النتيجة =====
// ================================================================

function displayResult(data) {
    const action = data.action || 'NEUTRAL';
    const isBuy = action.includes('BUY');
    const isStrong = action.startsWith('STRONG_');
    
    let actionText = '⚪ محايد';
    let actionClass = 'NEUTRAL';
    if (action.includes('BUY')) {
        actionText = (isStrong ? '🔥 ' : '🟢 ') + 'شراء' + (isStrong ? ' قوي جداً' : '');
        actionClass = isStrong ? 'STRONG_BUY' : 'BUY';
    } else if (action.includes('SELL')) {
        actionText = (isStrong ? '🔥 ' : '🔴 ') + 'بيع' + (isStrong ? ' قوي جداً' : '');
        actionClass = isStrong ? 'STRONG_SELL' : 'SELL';
    }
    
    // بناء الإشارات المكونة
    let signalsHtml = '';
    if (data.signals && data.signals.length > 0) {
        signalsHtml = data.signals.map(s => {
            const isBuySignal = s.type === 'BUY';
            return `<span class="signal-tag ${isBuySignal ? 'buy' : 'sell'}">
                ${s.name} (${s.score > 0 ? '+' : ''}${s.score})
            </span>`;
        }).join(' ');
    }
    
    // وقت الدخول
    let entryMinutes = data.time_remaining_minutes || 0;
    let entrySuggestion = '';
    if (action.includes('BUY') || action.includes('SELL')) {
        if (entryMinutes > 0.5) {
            entrySuggestion = `⏱️ دخول الآن (${entryMinutes.toFixed(1)} دقيقة متبقية)`;
        } else {
            entrySuggestion = `⏱️ انتظر الشمعة القادمة (${entryMinutes.toFixed(1)} دقيقة متبقية)`;
        }
    }
    
    elements.resultContainer.innerHTML = `
        <div class="result-card">
            <div class="result-header">
                <div>
                    <div class="result-symbol">
                        ${data.symbol}
                        <span class="pair-name">${data.pair_name || ''}</span>
                    </div>
                    <div class="result-price">
                        <span class="live" id="livePrice">${data.current_price?.toFixed(5) || '--'}</span>
                        <span class="payout">| العائد: ${data.payout || 92}%</span>
                        <span class="time-left">| ⏱️ <span id="timeRemaining">${entryMinutes.toFixed(2)}</span> دقيقة</span>
                    </div>
                </div>
                <div class="action-badge ${actionClass}">
                    ${actionText}
                    <span class="action-confidence">الثقة: ${data.confidence}%</span>
                </div>
            </div>

            ${entrySuggestion ? `
                <div class="entry-suggestion">
                    <span class="label">💡 التوصية:</span>
                    <span class="value">${entrySuggestion}</span>
                </div>
            ` : ''}

            ${signalsHtml ? `<div class="signals-list">${signalsHtml}</div>` : ''}

            <div class="stats-grid">
                <div class="stat-card">
                    <div class="label">🎯 القوة</div>
                    <div class="value ${data.confidence >= 80 ? 'high' : data.confidence >= 50 ? 'mid' : 'low'}">
                        ${data.confidence >= 80 ? '🔥 ممتازة' : data.confidence >= 60 ? '✅ جيدة' : '⚠️ متوسطة'}
                    </div>
                </div>
                <div class="stat-card">
                    <div class="label">📊 الدرجة</div>
                    <div class="value ${data.score >= 40 ? 'high' : data.score <= -40 ? 'low' : 'mid'}">
                        ${data.score > 0 ? '+' : ''}${data.score}
                    </div>
                </div>
                <div class="stat-card">
                    <div class="label">📈 السعر</div>
                    <div class="value info" id="livePriceStat">${data.current_price?.toFixed(5) || '--'}</div>
                </div>
                <div class="stat-card">
                    <div class="label">📉 التقلب</div>
                    <div class="value ${data.volatility === 'HIGH' ? 'high' : data.volatility === 'MEDIUM' ? 'mid' : ''}">
                        ${data.volatility || '--'}
                    </div>
                </div>
            </div>

            <div class="indicators-grid">
                <div class="indicator-card">
                    <div class="name">RSI</div>
                    <div class="value">${data.rsi?.toFixed(2) || '--'}</div>
                    <span class="tag ${data.rsi < 30 ? 'buy-tag' : data.rsi > 70 ? 'sell-tag' : 'neutral-tag'}">
                        ${data.rsi < 30 ? 'تشبع شرائي' : data.rsi > 70 ? 'تشبع بيعي' : 'محايد'}
                    </span>
                </div>
                <div class="indicator-card">
                    <div class="name">MACD</div>
                    <div class="value">${data.macd?.histogram?.toFixed(4) || '--'}</div>
                    <span class="tag ${data.macd?.histogram > 0 ? 'buy-tag' : 'sell-tag'}">
                        ${data.macd?.histogram > 0 ? 'صاعد' : 'هابط'}
                    </span>
                </div>
                <div class="indicator-card">
                    <div class="name">Bollinger</div>
                    <div class="value" style="font-size:12px;">U: ${data.bollinger?.upper?.toFixed(5) || '--'}</div>
                    <div class="value" style="font-size:12px;">L: ${data.bollinger?.lower?.toFixed(5) || '--'}</div>
                </div>
                <div class="indicator-card">
                    <div class="name">Stochastic</div>
                    <div class="value" style="font-size:12px;">K: ${data.stochastic?.k?.toFixed(2) || '--'}</div>
                    <div class="value" style="font-size:12px;">D: ${data.stochastic?.d?.toFixed(2) || '--'}</div>
                </div>
                <div class="indicator-card">
                    <div class="name">الدعم</div>
                    <div class="value">${data.support_resistance?.support?.toFixed(5) || '--'}</div>
                </div>
                <div class="indicator-card">
                    <div class="name">المقاومة</div>
                    <div class="value">${data.support_resistance?.resistance?.toFixed(5) || '--'}</div>
                </div>
                <div class="indicator-card">
                    <div class="name">ATR</div>
                    <div class="value">${data.atr?.toFixed(5) || '--'}</div>
                </div>
                <div class="indicator-card">
                    <div class="name">ADX</div>
                    <div class="value">${data.adx?.toFixed(2) || '--'}</div>
                </div>
                <div class="indicator-card">
                    <div class="name">EMA 9</div>
                    <div class="value">${data.ema9?.toFixed(5) || '--'}</div>
                </div>
                <div class="indicator-card">
                    <div class="name">EMA 21</div>
                    <div class="value">${data.ema21?.toFixed(5) || '--'}</div>
                </div>
                <div class="indicator-card">
                    <div class="name">EMA 50</div>
                    <div class="value">${data.ema50?.toFixed(5) || '--'}</div>
                </div>
                <div class="indicator-card">
                    <div class="name">SMA 20</div>
                    <div class="value">${data.sma20?.toFixed(5) || '--'}</div>
                </div>
            </div>

            <div style="font-size:10px;color:#333;text-align:center;margin-top:12px;border-top:1px solid rgba(255,255,255,0.03);padding-top:10px;">
                🕐 آخر تحديث: ${new Date(data.timestamp).toLocaleTimeString('ar-EG')}
            </div>
        </div>
    `;
    
    // تحديث السعر الحي
    if (autoRefreshInterval) clearInterval(autoRefreshInterval);
    autoRefreshInterval = setInterval(() => {
        updateLivePrice();
    }, 2000);
}

// ================================================================
// ===== تحديث شريط الإحصائيات =====
// ================================================================

function updateStatsBar(data) {
    const action = data.action || 'NEUTRAL';
    const confidence = data.confidence || 0;
    
    elements.currentSignal.textContent = action.replace('_', ' ');
    elements.currentSignal.className = 'stat-value ' + action.toLowerCase();
    elements.currentConfidence.textContent = confidence + '%';
    elements.currentPrice.textContent = data.current_price?.toFixed(5) || '--';
    elements.currentTimeRemaining.textContent = (data.time_remaining_minutes || 0).toFixed(2) + ' دقيقة';
    elements.currentVolatility.textContent = data.volatility || '--';
}

// ================================================================
// ===== تحديث السعر الحي =====
// ================================================================

function updateLivePrice() {
    if (!lastResult) return;
    
    // محاكاة تغير السعر البسيط
    const change = (Math.random() - 0.5) * 0.0002;
    const newPrice = lastResult.current_price + change;
    lastResult.current_price = newPrice;
    
    const priceEl = document.getElementById('livePrice');
    const priceStatEl = document.getElementById('livePriceStat');
    if (priceEl) {
        priceEl.textContent = newPrice.toFixed(5);
    }
    if (priceStatEl) {
        priceStatEl.textContent = newPrice.toFixed(5);
    }
    
    // تحديث الوقت المتبقي
    const timeEl = document.getElementById('timeRemaining');
    if (timeEl) {
        const current = parseFloat(timeEl.textContent) || 0;
        if (current > 0) {
            timeEl.textContent = (current - 0.0167).toFixed(2);
        }
    }
}

// ================================================================
// ===== عرض الإشارات القوية =====
// ================================================================

function showStrongSignals(signals) {
    elements.signalsPanel.style.display = 'block';
    elements.strongSignalsContainer.innerHTML = signals.map(data => {
        const isBuy = data.action.includes('BUY');
        return `
            <div class="strong-signal-card ${!isBuy ? 'sell' : ''}">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <strong>${data.pair_name || data.symbol}</strong>
                    <span style="font-weight:900;color:${isBuy ? '#00ff88' : '#ff4444'};">
                        ${isBuy ? '🟢 شراء' : '🔴 بيع'} 🔥
                    </span>
                </div>
                <div class="s-detail">الثقة: ${data.confidence}% | السعر: ${data.current_price?.toFixed(5) || '--'}</div>
                <div class="s-detail">⏱️ ${data.time_remaining_minutes?.toFixed(2) || '--'} دقيقة متبقية</div>
            </div>
        `;
    }).join('');
}

// ================================================================
// ===== تحديث الحالة =====
// ================================================================

async function updateStatus() {
    try {
        const res = await fetch(`${API}/api/v2/status`);
        const data = await res.json();
        
        if (data.connected) {
            elements.balanceDisplay.textContent = `$${data.balance?.toFixed(2) || '0.00'}`;
            elements.balanceDisplay.className = 'value connected';
        }
        
        if (data.daily_loss !== undefined) {
            elements.dailyLossDisplay.textContent = `$${data.daily_loss.toFixed(2)}`;
        }
        
        if (data.logs && data.logs.length > 0) {
            const logContainer = elements.logContainer;
            logContainer.innerHTML = data.logs.slice(-10).map(log => {
                const cls = log.includes('✅') ? 'success' : 
                           log.includes('❌') ? 'error' : 
                           log.includes('⚠️') ? 'warning' : '';
                return `<div class="log-entry"><span class="${cls}">${log}</span></div>`;
            }).join('');
        }
        
        // تحديث شريط الإحصائيات إذا كان هناك تحليل سابق
        if (lastResult) {
            updateStatsBar(lastResult);
        }
        
    } catch (e) {
        console.error('Status update error:', e);
    }
}

// ================================================================
// ===== إضافة سجل =====
// ================================================================

function addLog(message) {
    const container = elements.logContainer;
    const cls = message.includes('✅') ? 'success' : 
               message.includes('❌') ? 'error' : 
               message.includes('⚠️') ? 'warning' : '';
    const entry = document.createElement('div');
    entry.className = 'log-entry';
    entry.innerHTML = `<span class="${cls}">${message}</span>`;
    container.prepend(entry);
    
    // الاحتفاظ بآخر 50 سجل
    while (container.children.length > 50) {
        container.removeChild(container.lastChild);
    }
}

// ================================================================
// ===== دوال العرض =====
// ================================================================

function showLoading(message, subMessage = '') {
    elements.resultContainer.innerHTML = `
        <div class="loading">
            <i class="fas fa-spinner"></i>
            <div class="scan-text">${message}<span class="scan-dots"></span></div>
            ${subMessage ? `<div class="scan-sub">${subMessage}</div>` : ''}
        </div>
    `;
}

function showPlaceholder(message, subMessage = '') {
    elements.resultContainer.innerHTML = `
        <div class="placeholder">
            <i class="fas fa-info-circle" style="color:#00d4ff;"></i>
            <p>${message}</p>
            ${subMessage ? `<p class="sub">${subMessage}</p>` : ''}
        </div>
    `;
}

function showError(message) {
    elements.resultContainer.innerHTML = `
        <div style="text-align:center;color:#ff4444;padding:40px;">
            <i class="fas fa-exclamation-triangle" style="font-size:32px;"></i>
            <p style="margin-top:15px;">${message}</p>
        </div>
    `;
}

function showSuccess(message, subMessage = '') {
    elements.resultContainer.innerHTML = `
        <div style="text-align:center;color:#00ff88;padding:40px;">
            <i class="fas fa-check-circle" style="font-size:48px;"></i>
            <p style="margin-top:15px;font-size:20px;font-weight:700;">${message}</p>
            ${subMessage ? `<p style="color:#888;margin-top:5px;">${subMessage}</p>` : ''}
        </div>
    `;
}

// ================================================================
// ===== جلب السجل تلقائياً =====
// ================================================================

function startLogPolling() {
    setInterval(async () => {
        try {
            const res = await fetch(`${API}/api/v2/logs?limit=10`);
            const data = await res.json();
            if (data.logs && data.logs.length > 0) {
                const container = elements.logContainer;
                container.innerHTML = data.logs.slice(-10).map(log => {
                    const cls = log.includes('✅') ? 'success' : 
                               log.includes('❌') ? 'error' : 
                               log.includes('⚠️') ? 'warning' : '';
                    return `<div class="log-entry"><span class="${cls}">${log}</span></div>`;
                }).join('');
            }
        } catch (e) {
            // تجاهل الأخطاء
        }
    }, 5000);
}

// ================================================================
// ===== جلب الحالة تلقائياً =====
// ================================================================

function startStatusPolling() {
    setInterval(async () => {
        await updateStatus();
    }, 10000);
}

// ================================================================
// ===== تحديث الوقت =====
// ================================================================

function updateTime() {
    const now = new Date();
    elements.timeDisplay.textContent = now.toLocaleTimeString('ar-EG', { hour12: false });
}