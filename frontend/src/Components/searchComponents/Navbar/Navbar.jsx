import "./Navbar.css"
import Searchbar from "./Searchbar"
import { useNavigate } from "react-router-dom";

function Navbar() {
    const navigate = useNavigate();
 
    function handleOnClick() {
        navigate('/');
    }

    return (
        <div className='navBar'>
            <div className="left-side">
                <div className="tilte">Ratemycareer</div>
                <Searchbar></Searchbar>
            </div>
            <button className="returnHome" onClick={handleOnClick}>Homepage</button>
        </div>
    )
}

export default Navbar