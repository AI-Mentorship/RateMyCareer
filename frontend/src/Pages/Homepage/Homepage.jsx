import './Homepage.css'
import Searchbox from '../../Components/homeComponents/Searchbox/Searchbox.jsx'
import CompareBox from '../../Components/homeComponents/CompareBox/CompareBox.jsx'
import Standing from '../../Components/homeComponents/Standing/Standing.jsx'
import Arrow from '../../Components/homeComponents/Arrow/Arrow.jsx'
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
              <div className="left">
                <CompareBox></CompareBox>
              </div>
              <div className="right">
                <Standing></Standing>
              </div>
            </div>
          </div>
        </div>
    )
}

export default Homepage