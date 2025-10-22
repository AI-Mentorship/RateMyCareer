import './Standing.css'
import Topbar from './Topbar.jsx'

function Standing() {


    return (
        <div className="standing">
            <div className="tilte">Leaderboard</div>
            <Topbar rank="1st" profession="Teacher" score={5}></Topbar>
            <Topbar rank="2nd" profession="Lawyer" score={4.8}></Topbar>
            <Topbar rank="3rd" profession="Police" score={4.5}></Topbar>
            <Topbar rank="4th" profession="UX" score={3.9}></Topbar>
            <Topbar rank="5th" profession="Graphic Designer" score={3.7}></Topbar>
        </div>
    )
}

export default Standing 