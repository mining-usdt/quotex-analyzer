class UltimateAnalyzer {
    constructor() {
        this.apiBase = 'https://quotex-analyzer-1.onrender.com';
        this.continuousMode = false;
        this.continuousInterval = null;
        this.currentSymbol = null;
        
        this.init();
    }
    
    async init() {
        await this.loadAssets();
        this.setupEventListeners();
        this.updateTime();
        setInterval(() => this.updateTime(), 1000);
    }
    
    async loadAssets() {
        try {
            const response = await fetch(`${this.apiBase}/api/v1/markets`);
            const data = await response.json();
            const select = document.getElementById('symbolSelect');
            
            if (data.data && data.data.length > 0) {
                select.innerHTML = data.data.map(asset => 
                    `<option value="${asset.symbol}">${asset.name} (${asset.symbol})</option>`
                ).join('');
            } else {
                select.innerHTML = '<option value="">لا توجد أصول</option>';
            }
        } catch (error) {
            console.error('Error loading assets:', error);
            document.getElementById('symbolSelect').innerHTML = 
                '<option value="">⚠️ خطأ في الاتصال</option>';
        }
    }
    
    setupEventListeners() {
        document.getElementById('analyzeBtn').addEventListener('click', () => this.analyzeOnce());
        document.getElementById('continuousBtn').addEventListener('click', () => this.startContinuous());
        document.getElementById('stopBtn').addEventListener('click', () => this.stopContinuous());
        document.getElementById('strongSignalBtn').addEventListener('click', () => this.findStrongSignal());
    }
    
    async analyzeOnce() {
        const symbol = document.getElementById('symbolSelect').value;
        const limit = parseInt(document.getElementById('limitSelect').value);
        
        if (!symbol) {
            this.showError('⚠️ الرجاء اختيار زوج أولاً');
            return;
        }
        
        this.currentSymbol = symbol;
        this.showLoading();
        
        try {
            const response = await fetch(`${this.apiBase}/api/v2/analyze/${symbol}?limit=${limit}`);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP ${response.status}`);
            }
            const data = await response.json();
            this.displayResult(data);
        } catch (error) {
            console.error('Error analyzing:', error);
            this.showError(`❌ فشل التحليل: ${error.message}`);
        }
    }
    
    async findStrongSignal() {
        this.showLoading('🔍 جاري البحث عن إشارة قوية في جميع الأزواج...');
        
        try {
            const response = await fetch(`${this.apiBase}/api/v2/strong-signal`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            const data = await response.json();
            
            if (data.signals && data.signals.length > 0) {
                // عرض أقوى إشارة
                this.displayResult(data.signals[0]);
                
                // عرض جميع الإشارات القوية
                this.showStrongSignals(data.signals);
            } else {
                this.showError('❌ لا توجد إشارات قوية حالياً. حاول مرة أخرى لاحقاً.');
            }
        } catch (error) {
            console.error('Error finding strong signal:', error);
            this.showError(`❌ خطأ في البحث: ${error.message}`);
        }
    }
    
    startContinuous() {
        if (this.continuousMode) return;
        
        const symbol = document.getElementById('symbolSelect').value;
        if (!symbol) {
            this.showError('⚠️ الرجاء اختيار زوج أولاً');
            return;
        }
        
        this.continuousMode = true;
        this.currentSymbol = symbol;
        document.getElementById('continuousBtn').style.display = 'none';
        document.getElementById('stopBtn').style.display = 'inline-flex';
        document.getElementById('analyzeBtn').disabled = true;
        
        // تحليل فوري
        this.analyzeOnce();
        
        // كل 10 ثوانٍ
        this.continuousInterval = setInterval(() => {
            this.analyzeOnce();
        }, 10000);
    }
    
    stopContinuous() {
        this.continuousMode = false;
        if (this.continuousInterval) {
            clearInterval(this.continuousInterval);
            this.continuousInterval = null;
        }
        document.getElementById('continuousBtn').style.display = 'inline-flex';
        document.getElementById('stopBtn').style.display = 'none';
        document.getElementById('analyzeBtn').disabled = false;
    }
    
    displayResult(data) {
        const container = document.getElementById('resultContainer');
        
        if (data.error) {
            this.showError(data.error);
            return;
        }
        
        const action = data.action || 'NEUTRAL';
        const confidence = data.confidence || 0;
        const isStrong = action.startsWith('STRONG_');
        const displayAction = isStrong ? action.replace('STRONG_', '') : action;
        
        let actionText = '⚪ محايد';
        let actionClass = 'NEUTRAL';
        if (action.includes('BUY')) {
            actionText = (isStrong ? '🔥 ' : '🟢 ') + 'شراء' + (isStrong ? ' قوي جداً' : '');
            actionClass = isStrong ? 'STRONG_BUY' : 'BUY';
        } else if (action.includes('SELL')) {
            actionText = (isStrong ? '🔥 ' : '🔴 ') + 'بيع' + (isStrong ? ' قوي جداً' : '');
            actionClass = isStrong ? 'STRONG_SELL' : 'SELL';
        }
        
        // بناء التوصية
        let suggestionHTML = '';
        if (data.suggestion) {
            const sug = data.suggestion;
            suggestionHTML = `
                <div style="margin:15px 0;padding:15px;border-radius:12px;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.05);">
                    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:10px;">
                        <div>
                            <div style="font-size:11px;color:#666;">الاتجاه</div>
                            <div style="font-weight:700;font-size:16px;color:${sug.direction.includes('شراء') ? '#00ff88' : sug.direction.includes('بيع') ? '#ff4444' : '#888'}">
                                ${sug.direction}
                            </div>
                        </div>
                        <div>
                            <div style="font-size:11px;color:#666;">نقطة الدخول</div>
                            <div style="font-weight:700;">${sug.entry || '--'}</div>
                        </div>
                        <div>
                            <div style="font-size:11px;color:#666;">جني الربح (TP)</div>
                            <div style="font-weight:700;color:#00ff88;">${sug.take_profit || '--'}</div>
                        </div>
                        <div>
                            <div style="font-size:11px;color:#666;">وقف الخسارة (SL)</div>
                            <div style="font-weight:700;color:#ff4444;">${sug.stop_loss || '--'}</div>
                        </div>
                        <div>
                            <div style="font-size:11px;color:#666;">نسبة المخاطرة/المكافأة</div>
                            <div style="font-weight:700;color:#ffbb00;">${sug.risk_reward || 0}</div>
                        </div>
                    </div>
                </div>
            `;
        }
        
        // بناء المؤشرات
        let indicatorsHTML = '';
        if (data.rsi !== undefined) {
            indicatorsHTML = `
                <div class="indicators-grid">
                    <div class="indicator-card">
                        <div class="name">RSI</div>
                        <div class="value">${data.rsi.toFixed(2)}</div>
                        <span class="signal-tag ${data.rsi < 30 ? 'buy-tag' : data.rsi > 70 ? 'sell-tag' : 'neutral-tag'}">
                            ${data.rsi < 30 ? 'تشبع شرائي' : data.rsi > 70 ? 'تشبع بيعي' : 'محايد'}
                        </span>
                    </div>
                    <div class="indicator-card">
                        <div class="name">MACD</div>
                        <div class="value">${data.macd?.histogram?.toFixed(4) || '--'}</div>
                        <span class="signal-tag ${data.macd?.histogram > 0 ? 'buy-tag' : 'sell-tag'}">
                            ${data.macd?.histogram > 0 ? 'صاعد' : 'هابط'}
                        </span>
                    </div>
                    <div class="indicator-card">
                        <div class="name">Stochastic</div>
                        <div class="value" style="font-size:14px;">K: ${data.stochastic?.k?.toFixed(2) || '--'}</div>
                        <div class="value" style="font-size:14px;">D: ${data.stochastic?.d?.toFixed(2) || '--'}</div>
                    </div>
                    <div class="indicator-card">
                        <div class="name">الدعم / المقاومة</div>
                        <div class="value" style="font-size:14px;">دعم: ${data.support_resistance?.support?.toFixed(5) || '--'}</div>
                        <div class="value" style="font-size:14px;">مقاومة: ${data.support_resistance?.resistance?.toFixed(5) || '--'}</div>
                    </div>
                    <div class="indicator-card">
                        <div class="name">ATR (التقلب)</div>
                        <div class="value">${data.atr?.toFixed(5) || '--'}</div>
                    </div>
                    <div class="indicator-card">
                        <div class="name">الوقت المتبقي</div>
                        <div class="value" style="font-size:18px;">${data.time_remaining_minutes?.toFixed(2) || '--'} دقيقة</div>
                    </div>
                </div>
            `;
        }
        
        // بناء الإشارات المكونة
        let signalsList = '';
        if (data.signals && data.signals.length > 0) {
            signalsList = data.signals.map(s => 
                `<span class="signal-tag ${s.type === 'BUY' ? 'buy-tag' : s.type === 'SELL' ? 'sell-tag' : 'neutral-tag'}">
                    ${s.name} (${s.score > 0 ? '+' : ''}${s.score})
                </span>`
            ).join(' ');
        }
        
        // الأنماط
        let patternHTML = '';
        if (data.pattern && data.pattern.name !== 'NONE') {
            patternHTML = `
                <div style="margin-top:10px;padding:10px 15px;border-radius:10px;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.05);">
                    <span style="color:#888;">🔍 النمط المكتشف:</span>
                    <span style="font-weight:700;color:#ffbb00;">${data.pattern.name}</span>
                    <span style="color:#666;font-size:13px;">(القوة: ${data.pattern.score}%)</span>
                </div>
            `;
        }
        
        // الاختراق
        let breakoutHTML = '';
        if (data.breakout && data.breakout.name !== 'NONE') {
            breakoutHTML = `
                <div style="margin-top:10px;padding:10px 15px;border-radius:10px;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.05);">
                    <span style="color:#888;">🚀 الاختراق:</span>
                    <span style="font-weight:700;color:#00d4ff;">${data.breakout.name}</span>
                    <span style="color:#666;font-size:13px;">(القوة: ${data.breakout.score}%)</span>
                </div>
            `;
        }
        
        // الارتداد
        let bounceHTML = '';
        if (data.bounce && data.bounce.name !== 'NONE') {
            bounceHTML = `
                <div style="margin-top:10px;padding:10px 15px;border-radius:10px;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.05);">
                    <span style="color:#888;">📌 الارتداد:</span>
                    <span style="font-weight:700;color:#7b2ffc;">${data.bounce.name}</span>
                    <span style="color:#666;font-size:13px;">(القوة: ${data.bounce.score}%)</span>
                </div>
            `;
        }
        
        container.innerHTML = `
            <div class="result-content">
                <div class="result-header">
                    <div>
                        <div class="result-symbol">${data.pair_name || data.symbol}</div>
                        <div style="font-size:13px;color:#888;margin-top:3px;">
                            <i class="fas fa-tag"></i> ${data.symbol} 
                            | <i class="fas fa-clock"></i> ${data.time_remaining_minutes?.toFixed(2) || '--'} دقيقة متبقية
                            | <i class="fas fa-coins"></i> العائد: ${data.payout || 92}%
                        </div>
                    </div>
                    <div class="result-action ${actionClass}">
                        ${actionText}
                        <div style="font-size:14px;font-weight:400;margin-top:3px;">
                            الثقة: ${confidence}%
                        </div>
                    </div>
                </div>
                
                <div class="result-stats">
                    <div class="stat-card">
                        <div class="label">🎯 قوة الإشارة</div>
                        <div class="value ${confidence >= 80 ? 'high' : confidence >= 50 ? 'mid' : 'low'}">
                            ${confidence >= 80 ? '🔥 ممتازة' : confidence >= 60 ? '✅ جيدة' : '⚠️ متوسطة'}
                        </div>
                    </div>
                    <div class="stat-card">
                        <div class="label">📊 درجة التحليل</div>
                        <div class="value ${data.score >= 40 ? 'high' : data.score <= -40 ? 'low' : 'mid'}">
                            ${data.score > 0 ? '+' : ''}${data.score}
                        </div>
                    </div>
                    <div class="stat-card">
                        <div class="label">📈 السعر الحالي</div>
                        <div class="value">${data.current_price?.toFixed(5) || '--'}</div>
                    </div>
                    <div class="stat-card">
                        <div class="label">🕒 وقت التحليل</div>
                        <div class="value" style="font-size:14px;">${new Date(data.timestamp).toLocaleTimeString('ar-EG')}</div>
                    </div>
                </div>
                
                ${suggestionHTML}
                
                ${signalsList ? `<div style="margin:10px 0;display:flex;flex-wrap:wrap;gap:5px;">${signalsList}</div>` : ''}
                
                ${indicatorsHTML}
                
                ${patternHTML}
                ${breakoutHTML}
                ${bounceHTML}
            </div>
        `;
    }
    
    showStrongSignals(signals) {
        const panel = document.getElementById('signalsPanel');
        const container = document.getElementById('strongSignalsContainer');
        
        panel.style.display = 'block';
        container.innerHTML = signals.map(data => {
            const isBuy = data.action.includes('BUY');
            return `
                <div class="strong-signal-card ${!isBuy ? 'sell' : ''}">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <strong>${data.pair_name || data.symbol}</strong>
                        <span style="font-weight:900;color:${isBuy ? '#00ff88' : '#ff4444'};">
                            ${isBuy ? '🟢 شراء' : '🔴 بيع'} 🔥
                        </span>
                    </div>
                    <div style="font-size:13px;color:#888;margin-top:5px;">
                        الثقة: ${data.confidence}% | السعر: ${data.current_price?.toFixed(5) || '--'}
                    </div>
                    <div style="font-size:12px;color:#666;">
                        الوقت المتبقي: ${data.time_remaining_minutes?.toFixed(2) || '--'} دقيقة
                    </div>
                    ${data.suggestion ? `
                        <div style="font-size:12px;color:#aaa;margin-top:3px;">
                            TP: ${data.suggestion.take_profit || '--'} | SL: ${data.suggestion.stop_loss || '--'}
                        </div>
                    ` : ''}
                </div>
            `;
        }).join('');
    }
    
    showLoading(message = 'جاري التحليل الخارق...') {
        document.getElementById('resultContainer').innerHTML = `
            <div class="loading">
                <i class="fas fa-spinner fa-spin" style="font-size:32px;"></i>
                <p style="margin-top:15px;color:#666;">${message}</p>
            </div>
        `;
    }
    
    showError(message) {
        document.getElementById('resultContainer').innerHTML = `
            <div style="text-align:center;color:#ff4444;padding:40px;">
                <i class="fas fa-exclamation-triangle" style="font-size:32px;"></i>
                <p style="margin-top:15px;">${message}</p>
            </div>
        `;
    }
    
    updateTime() {
        const now = new Date();
        document.getElementById('systemTime').textContent = 
            now.toLocaleTimeString('ar-EG', { hour12: false });
    }
}

// تشغيل التطبيق
document.addEventListener('DOMContentLoaded', () => {
    const app = new UltimateAnalyzer();
});