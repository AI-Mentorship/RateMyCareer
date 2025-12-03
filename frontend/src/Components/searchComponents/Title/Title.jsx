import "./Title.css"

function Title({ name = 'Data Analyst', vibe = 72, breakdown = '80 sentiment  |  34 regret  |  70 volatility' }){
    return (
        <div className="title-container">
            <div className="title-header">
                <h1 className="profession-name">{name}</h1>
                <p className="profession-meta">Reddit Source: r/humanresources | Last Updated: 11/30/2025</p>
            </div>
            
            <div className="metrics-row">
                <div className="metric-box">
                    <p className="metric-label">Overall Sentiment</p>
                    <p className="metric-value">80%</p>
                    <p className="metric-description">Positive</p>
                </div>
                
                <div className="metric-box">
                    <p className="metric-label">Regret Detected</p>
                    <p className="metric-value">53%</p>
                    <p className="metric-description">Moderate</p>
                </div>
                
                <div className="metric-box">
                    <p className="metric-label">Emotion Volatility</p>
                    <p className="metric-value">23%</p>
                    <p className="metric-description">Stable</p>
                </div>
                
                <div className="metric-box vibe-box">
                    <p className="metric-label">Vibe Score</p>
                    <p className="metric-value">{vibe !== undefined ? `${vibe}/100` : "72/100"}</p>
                </div>
            </div>
        </div>
    )
}

export default Title