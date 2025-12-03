import './Quote.css'
import { useState } from 'react';

function Quote({ quotes: propQuotes }) {
    const fallback1 = "Data Analysts enjoy a stable career with positive growth in demand. However, there are occasional mentions of job stress and limited advancement opportunities. The work often involves problem-solving and can be intellectually rewarding1.";
    const fallback2 = "Data Analysts enjoy a stable career with positive growth in demand. However, there are occasional mentions of job stress and limited advancement opportunities. The work often involves problem-solving and can be intellectually rewarding2.";
    const fallback3 = "Data Analysts enjoy a stable career with positive growth in demand. However, there are occasional mentions of job stress and limited advancement opportunities. The work often involves problem-solving and can be intellectually rewarding3.";
    const fallback4 = "Data Analysts enjoy a stable career with positive growth in demand. However, there are occasional mentions of job stress and limited advancement opportunities. The work often involves problem-solving and can be intellectually rewarding4.";
    const fallback5 = "Data Analysts enjoy a stable career with positive growth in demand. However, there are occasional mentions of job stress and limited advancement opportunities. The work often involves problem-solving and can be intellectually rewarding5.";

    const defaultQuotes = [fallback1,fallback2,fallback3,fallback4,fallback5]
    const quotes = Array.isArray(propQuotes) && propQuotes.length ? propQuotes : defaultQuotes
    const [index,setIndex] = useState(0);
    const [name,setName] = useState("");
    const [check,setCheck] = useState(0);

    function handleClickLeft(){
        if (check > 0){
            setCheck(c=>c-1);
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
        if (check < quotes.length-1){
            setCheck(c=>c+1);
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