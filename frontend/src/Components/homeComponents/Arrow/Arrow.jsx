import './Arrow.css'

function Arrow () {
    function handleScroll(){
        const target = document.getElementById("secondSection"); 
        target.scrollIntoView({ behavior: "smooth" });
    }

    return (
        <button className="arrow" onClick={handleScroll}> Explore More </button>
    )
}

export default Arrow