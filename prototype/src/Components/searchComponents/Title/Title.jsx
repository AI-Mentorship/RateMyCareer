import "./Title.css"

function Title({ name = 'Data Analyst', vibe = 72, sentiment = null, regret = null, volatility = null }){
    
    const getSentimentDesc = (val) => {
        if (val == null) return '—';
        const v = Number(val);
        // Heuristic for 0-10 or 0-100 scale
        if (v > 70 || (v > 7 && v <= 10)) return 'Positive';
        if (v < 40 || (v < 4 && v <= 10)) return 'Negative';
        return 'Neutral';
    }

    const getRegretDesc = (val) => {
        if (val == null) return '—';
        const v = Number(val);
        // Heuristic for 0-1 ratio or 0-100 percent
        if ((v > 0.5 && v <= 1) || v > 50) return 'High';
        if ((v < 0.2 && v <= 1) || v < 20) return 'Low';
        return 'Moderate';
    }

    const getVolatilityDesc = (val) => {
        if (val == null) return '—';
        const v = Number(val);
        if ((v > 0.5 && v <= 1) || v > 50) return 'Volatile';
        return 'Stable';
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