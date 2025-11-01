import './Profession.css'
import Navbar from '../../Components/searchComponents/Navbar'
import Chart from '../../Components/searchComponents/Chart'
import Quote from '../../Components/searchComponents/Quote'
import Title from '../../Components/searchComponents/Title'


function Profession(){
    return (
        <div className="page">
            <div className="backgrounds">
                <div className="background1"></div>
                <div className="background2"></div>
                <div className="background3"></div>
                <div className="background4"></div>
            </div>
            <div className="content">
                <Navbar></Navbar>
                <Title></Title>
                <div className="first-section">
                    <h1>Overview</h1>
                    <h2>"</h2>
                    <p>Data Analysts enjoy a stable career with positive growth in demand. 
                    However, there are occasional mentions of job stress and limited 
                    advancement opportunities. The work often involves problem-solving 
                    and can be intellectually rewarding.</p>
                </div>
                <div className="second-section">
                    <Chart></Chart>
                </div>
                <div className="third-section">
                    <Quote></Quote>
                </div>
            </div>
       </div>
    )
}

export default Profession