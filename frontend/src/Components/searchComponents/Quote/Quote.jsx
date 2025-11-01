import './Quote.css'
import { useState } from 'react';

function Quote() {
    const quote1 = "Data Analysts enjoy a stable career with positive growth in demand. However, there are occasional mentions of job stress and limited advancement opportunities. The work often involves problem-solving and can be intellectually rewarding1.";
    const quote2 = "Data Analysts enjoy a stable career with positive growth in demand. However, there are occasional mentions of job stress and limited advancement opportunities. The work often involves problem-solving and can be intellectually rewarding2.";
    const quote3 = "Data Analysts enjoy a stable career with positive growth in demand. However, there are occasional mentions of job stress and limited advancement opportunities. The work often involves problem-solving and can be intellectually rewarding3.";
    const quote4 = "Data Analysts enjoy a stable career with positive growth in demand. However, there are occasional mentions of job stress and limited advancement opportunities. The work often involves problem-solving and can be intellectually rewarding4.";
    const quote5 = "Data Analysts enjoy a stable career with positive growth in demand. However, there are occasional mentions of job stress and limited advancement opportunities. The work often involves problem-solving and can be intellectually rewarding5.";

    const quotes = [quote1,quote2,quote3,quote4,quote5]
    const [index,setIndex] = useState(1);
    const [name,setName] = useState("");

    function handleClickLeft(){
        if (index > 0){
            setName("slideRight");
            setTimeout(()=>{
                setIndex(i=>i-1);
                setName("initialLeft");
                setTimeout(() => {
                    setName("replaceLeft");
                }, 50);
            },
            300);
        }
    }

    function handleClickRight(){
        if (index < quotes.length-1){
            setName("slideLeft");
            setTimeout(()=>{
                setIndex(i=>i+1);
                setName("initialRight");
                setTimeout(() => {
                    setName("replaceRight");
                }, 50);
            },
            300);
        }
    }

    return (
        <div className="quote-container">
            <h1>Quotes</h1>
            <div className="slideBar">
                <p className={name}>{quotes[index]}</p>
            </div>
            <div className="leftArrow" onClick={handleClickLeft}>‹</div>
            <div className="rightArrow" onClick={handleClickRight}>›</div>
        </div>
    )
}

export default Quote