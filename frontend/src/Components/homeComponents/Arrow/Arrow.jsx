import './Arrow.css'

function Arrow () {
    function handleScroll(){
        const target = document.getElementById("target"); 
        target.scrollIntoView({ behavior: "smooth" });
    }

    return (
        <button className="arrow" onClick={handleScroll}> Explore More </button>
    )
}

export default Arrow