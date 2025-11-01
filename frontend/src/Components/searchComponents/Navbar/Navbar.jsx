import "./Navbar.css"
import Searchbar from "./Searchbar"

function Navbar() {
    return (

        <div className='navBar'>
            <div className="left">
                <div className="tilte">Ratemycareer</div>
                <Searchbar></Searchbar>
            </div>
            <button className="returnHome">Homepage</button>
        </div>
    )
}

export default Navbar