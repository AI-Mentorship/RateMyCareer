import './Arrow.css'

function Arrow () {
    const target = document.getElementById("secondSection");
    function handleClick(){  
    }
    return (
        <button className="arrow" onClick={handleClick}> Explore More</button>
    )
}

export default Arrow