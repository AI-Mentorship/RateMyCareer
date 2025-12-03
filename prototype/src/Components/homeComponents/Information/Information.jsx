
import "./Information.css"
import pilot from "../../../assets/pilot.png"
import plane from "../../../assets/plane.jpg"

function Information() {
    return (
    <div className="information-container">
        <div className="image-container">
            <img src={pilot} className="information-pilot"></img>
            <img src={plane} className="information-plane"></img>
        </div>
        <div className="info-content">
            <div className="information-header">What is RateMyCareer?</div>
            <div className="information-subheader"> <span className="highlight">Emotionally</span> Contextualized Insights</div>
            <div className="info-detail">RateMyCareer utilizes AI to surface the genuine, emotional experiences of careers through unfiltered Reddit discussions, enabling students, career switchers, and HR teams to go beyond salary data and make more informed, human-centered career decisions.</div>
        </div>
    </div>
    )
}

export default Information
