import "./Title.css"

function Title(){
    return (
        <div className="title-container">
            <div className="vibeScore">
                <span className="bigger">72<span className="smaller">/100</span></span>
            </div>
            <div className="name">Data Analyst</div>
            <div className="breakdown">80 setiment  |  34 regert  |  70 volatility</div>
        </div>
    )
}

export default Title