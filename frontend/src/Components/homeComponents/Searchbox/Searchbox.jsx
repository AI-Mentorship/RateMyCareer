import './Searchbox.css'
import Searchbar from './Searchbar'
import bubble1 from '../../../assets/bubble1.png'
import bubble2 from '../../../assets/bubble2.png'
import bubble3 from '../../../assets/bubble3.png'


function Searchbox() {
    return (
        <div className="searchbox">
            <h1> RateMyCareer</h1>
            <p className="intro">"The emotional realities of different professions."</p>
            <Searchbar></Searchbar>
            <div className="information">
                <div className="info1">
                    <h1>500K</h1>
                    <p>Comments</p>
                </div>
                <div className="info2">
                    <h1>100+</h1>
                    <p>Countries</p>
                </div>
                <div className="info3">
                    <h1>30+</h1>
                    <p>Professions</p>
                </div>
            </div>
        </div>
    )
}
export default Searchbox