import './Topbar.css'

function Topbar({rank, profession, score}) {
    if (rank == "1st"){
        return (
            <div className='topbar'>
                <div className="bar-container">
                    <div className="name">{profession}</div>
                    <div className="vibeScore">{score}</div>
                    <div className="top-container">
                        <div className='ranking'
                        >{rank}</div>
                    </div>
                </div>
            </div>
        )
    }
    else {
        return (
            <div className='topbar'>
                <div className="bar-container"
                    style={{
                        backgroundColor: "white",
                        color: "black",
                    }}
                >
                    <div className="name">{profession}</div>
                    <div className="vibeScore">{score}</div>
                    <div className="top-container"
                        style={{
                            backgroundColor: "#828080ff",
                            color: "white",
                        }}
                    >
                        <div className='ranking'
                        >{rank}</div>
                    </div>
                </div>
            </div>
        )
    }
}

export default Topbar