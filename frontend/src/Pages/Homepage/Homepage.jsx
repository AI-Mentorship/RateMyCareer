import './Homepage.css'
import Searchbox from '../../Components/Searchbox/Searchbox'
import CompareBox from '../../Components/CompareBox/CompareBox'
import Standing from '../../Components/Standing/Standing'
import Arrow from '../../Components/Arrow/Arrow'
import image1 from '../../assets/background1.jpg'

function Homepage() {
    return (
        <div className="page">
          <div className="backgrounds">
            <div className="background1"></div>
            <div className="background2"></div>
            <div className="background3"></div>
            <div className="background4"></div>
          </div>
          <div className="content">
            <div className="firstSection">
              <Searchbox></Searchbox>
              <img className="image1" src={image1}></img>
            </div>
            <Arrow></Arrow>
            <div id="secondSection" className="secondSection">
              <CompareBox></CompareBox>
              <Standing></Standing>
            </div>
          </div>
        </div>
    )
}

export default Homepage