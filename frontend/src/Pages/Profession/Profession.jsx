import './Profession.css'
import Navbar from '../../Components/searchComponents/Navbar/Navbar'
import Chart from '../../Components/searchComponents/Chart/Chart'
import Quote from '../../Components/searchComponents/Quote/Quote'
import Title from '../../Components/searchComponents/Title/Title'


function Profession(){
    return (
        <div className="prof-page">
            <div className="prof-backgrounds">
                <div className="prof-background1"></div>
                <div className="prof-background2"></div>
                <div className="prof-background3"></div>
                <div className="prof-background4"></div>
            </div>
            <div className="prof-content">
                <Navbar></Navbar>
                <Title></Title>
                <div className="top-section">
                    <h1>Overview</h1>
                    <h2>"</h2>
                    <p>Data Analysts enjoy a stable career with positive growth in demand. 
                    However, there are occasional mentions of job stress and limited 
                    advancement opportunities. The work often involves problem-solving 
                    and can be intellectually rewarding.</p>
                </div>
                <div className="mid-section">
                    <Chart></Chart>
                </div>
                <div className="bot-section">
                    <Quote></Quote>
                </div>
            </div>
       </div>
    )
}

export default Profession