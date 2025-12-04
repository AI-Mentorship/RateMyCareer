import "./Title.css"

function Title({ name = 'Data Analyst', vibe = 72, sentiment = null, regret = null, volatility = null }){
    
    const getSentimentDesc = (val) => {
        if (val == null) return '—';
        const v = Number(val);
        // Heuristic for 0-10 or 0-100 scale
        if (v > 60 || (v > 6 && v <= 10)) return 'Positive';
        if (v < 40 || (v < 4 && v <= 10)) return 'Negative';
        return 'Mixed';
    }

    const getRegretDesc = (val) => {
        if (val == null) return '—';
        const v = Number(val);
        // Handle 0-10 scale (e.g. 6.4) vs 0-100 scale (e.g. 64)
        // If value is small (<10), assume it's 0-10 scale and normalize to 0-100
        const normalized = (v <= 10 && v > 1) ? v * 10 : v; // Heuristic: if between 1 and 10, treat as /10. If 0.x, treat as ratio.
        
        // Logic: > 50% is High, < 30% is Low
        if (normalized > 50 || (v > 0.5 && v <= 1)) return 'High';
        if (normalized < 30 || (v < 0.3 && v <= 1)) return 'Low';
        return 'Moderate';
    }

    const getVolatilityDesc = (val) => {
        if (val == null) return '—';
        const v = Number(val);
        // 0-10 scale
        if (v > 7) return 'High';
        if (v < 4) return 'Stable';
        return 'Moderate';
    }

    return (
        <div className="title-container">
            <div className="title-header">
                <h1 className="profession-name">{name}</h1>
                <p className="profession-meta">Reddit Source: r/{name.replace(/\s+/g, '').toLowerCase()} | Last Updated: 11/30/2025</p>
            </div>
            
            <div className="metrics-row">
                <div className="metric-box">
                    <p className="metric-label">Overall Sentiment</p>
                    <p className="metric-value">{sentiment !== null ? sentiment : '—'}</p>
                    <p className="metric-description">{getSentimentDesc(sentiment)}</p>
                </div>
                
                <div className="metric-box">
                    <p className="metric-label">Regret Detected</p>
                    <p className="metric-value">{regret !== null ? regret : '—'}</p>
                    <p className="metric-description">{getRegretDesc(regret)}</p>
                </div>
                
                <div className="metric-box">
                    <p className="metric-label">Emotion Volatility</p>
                    <p className="metric-value">{volatility !== null ? volatility : '—'}</p>
                    <p className="metric-description">{getVolatilityDesc(volatility)}</p>
                </div>
                
                <div className="metric-box vibe-box">
                    <p className="metric-label">Vibe Score</p>
                    <p className="metric-value">{vibe !== undefined && vibe !== null ? `${Number(vibe).toFixed(1)}/10` : "—"}</p>
                </div>
            </div>
        </div>
    )
}

export default Title