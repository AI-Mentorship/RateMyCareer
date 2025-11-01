import './Arrow.css'

function Arrow () {
    const target = document.getElementById("secondSection");

    return (
        <button className="arrow" onClick={()=>target.scrollIntoView({ behavior: "smooth" })}> Explore More </button>
    )
}

export default Arrow