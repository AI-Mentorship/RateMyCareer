import "./Title.css"

function Title({ name = 'Data Analyst', vibe = 72, breakdown = '80 setiment  |  34 regert  |  70 volatility' }){
    return (
        <div className="title-container">
            <div className="vibeScore">
                <span className="bigger">{vibe}<span className="smaller">/100</span></span>
            </div>
            <div className="name">{name}</div>
            <div className="breakdown">{breakdown}</div>
        </div>
    )
}

export default Title