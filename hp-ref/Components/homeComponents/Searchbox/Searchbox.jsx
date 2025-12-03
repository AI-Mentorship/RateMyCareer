import './Searchbox.css'
import Searchbar from './Searchbar'
import bubble1 from '../../../assets/bubble1.png'
import bubble2 from '../../../assets/bubble2.png'
import bubble3 from '../../../assets/bubble3.png'


function Searchbox() {
    return (
        <div className="searchbox">
            <h1> RateMyCareer</h1>
            <p className="intro">Real Careers. Real Emotions. Real Stories.</p>
            <Searchbar></Searchbar>
            <div className="information">
                <div className="info1">
                    <h1>10K+</h1>
                    <p>Posts</p>
                </div>
                <div className="info2">
                    <h1>30+</h1>
                    <p>Careers</p>
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