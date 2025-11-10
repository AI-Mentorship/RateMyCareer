// import './Profession.css'
// import { useEffect, useState } from 'react'
// import { useLocation } from 'react-router-dom'
// import Navbar from '../../Components/searchComponents/Navbar/Navbar'
// import Chart from '../../Components/searchComponents/Chart/Chart'
// import Quote from '../../Components/searchComponents/Quote/Quote'
// import Title from '../../Components/searchComponents/Title/Title'


// function Profession(){
//     const [timeline, setTimeline] = useState([])
//     const [score, setScore] = useState(null)
//     const [loading, setLoading] = useState(true)
//     const [error, setError] = useState(null)

//     // determine career from navigation state (sent by homepage search) or fallback
//     const location = useLocation()
//     const career = location?.state?.career || 'Data Analyst'
//     // Vite exposes env vars via import.meta.env and requires the VITE_ prefix for user vars.
//     // If you're running under a different tool that exposes process.env, adjust accordingly.
//     const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'

//     useEffect(()=>{
//         let mounted = true
//         async function load(){
//             try{
//                 setLoading(true)
//                 // timeline
//                 const tRes = await fetch(`${API_BASE}/api/timeline?career=${encodeURIComponent(career)}`)
//                 const tJson = await tRes.json()
//                 // scores (latest)
//                 const sRes = await fetch(`${API_BASE}/api/scores?career=${encodeURIComponent(career)}`)
//                 const sJson = await sRes.json()

//                 if(!mounted) return

//                 // transform timeline into Chart-friendly data: { week: date, sentiment: value }
//                 const chartData = (tJson.timeline || []).map(pt => ({ week: pt.date, sentiment: Number(pt.value) }))
//                 setTimeline(chartData)

//                 // score endpoint returns { career, rows: [...] }
//                 const latestRow = (sJson.rows && sJson.rows.length) ? sJson.rows[0] : null
//                 setScore(latestRow)
//             }catch(e){
//                 console.error(e)
//                 setError(String(e))
//             }finally{
//                 setLoading(false)
//             }
//         }
//         load()
//         return ()=>{ mounted = false }
//     }, [API_BASE, career])

//     return (
//         <div className="prof-page">
//             <div className="prof-backgrounds">
//                 <div className="prof-background1"></div>
//                 <div className="prof-background2"></div>
//                 <div className="prof-background3"></div>
//                 <div className="prof-background4"></div>
//             </div>
//             <div className="prof-content">
//                 <Navbar></Navbar>
//                 {(() => {
//                     const vibePercent = score && score.vibe_score ? Math.round(score.vibe_score * 20) : 72
//                     const sentimentPercent = (score && typeof score.avg_sentiment === 'number') ? Math.round((score.avg_sentiment + 1) * 50) : 80
//                     const regretPercent = (score && typeof score.regret_ratio === 'number') ? Math.round(score.regret_ratio * 100) : 34
//                     const volatilityPercent = (score && typeof score.sentiment_volatility === 'number') ? Math.round(score.sentiment_volatility * 100) : 70
//                     const breakdown = `${sentimentPercent} sentiment  |  ${regretPercent} regret  |  ${volatilityPercent} volatility`
//                     return <Title name={career} vibe={vibePercent} breakdown={breakdown} />
//                 })()}
//                 <div className="top-section">
//                     <h1>Overview</h1>
//                     <h2>"</h2>
//                     <p>Data Analysts enjoy a stable career with positive growth in demand. 
//                     However, there are occasional mentions of job stress and limited 
//                     advancement opportunities. The work often involves problem-solving 
//                     and can be intellectually rewarding.</p>

//                     {/* injected API stats - keep class names */}
//                     <div className="api-stats">
//                         {loading && <div>Loading latest data...</div>}
//                         {error && <div className="error">Error: {error}</div>}
//                         {!loading && score && (
//                             <div>
//                                 <div>Latest record date: {score.record_date || '—'}</div>
//                                 <div>Vibe score: {score.vibe_score ?? '—'}</div>
//                                 <div>Average sentiment: {score.avg_sentiment ?? '—'}</div>
//                                 <div>Forecasted sentiment (avg): {score.forecasted_sentiment_avg ?? '—'}</div>
//                             </div>
//                         )}
//                         {!loading && !score && <div>No score data available</div>}
//                     </div>
//                 </div>
//                 <div className="mid-section">
//                     <Chart data={timeline}></Chart>
//                 </div>
//                 <div className="bot-section">
//                     <Quote></Quote>
//                 </div>
//             </div>
//        </div>
//     )
// }

// export default Profession

import './Profession.css'
import { useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'
import Navbar from '../../Components/searchComponents/Navbar/Navbar'
import Chart from '../../Components/searchComponents/Chart/Chart'
import Quote from '../../Components/searchComponents/Quote/Quote'
import Title from '../../Components/searchComponents/Title/Title'


function Profession(){
    const [timeline, setTimeline] = useState([])
    const [score, setScore] = useState(null)
    const [effectiveCareer, setEffectiveCareer] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    // determine career from navigation state (sent by homepage search) or fallback
    // Searchbox now passes { careerValue, careerLabel } where `careerValue` should be
    // the canonical DB career_name (use this for API calls) and `careerLabel` is the
    // human-friendly label for display.
    const location = useLocation()
    const careerValue = location?.state?.careerValue || location?.state?.career || null
    const careerLabel = location?.state?.careerLabel || location?.state?.career || null
    const career = careerValue || careerLabel || 'Data Analyst'
    // Vite exposes env vars via import.meta.env and requires the VITE_ prefix for user vars.
    // If you're running under a different tool that exposes process.env, adjust accordingly.
    const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'

    useEffect(()=>{
        let mounted = true
        async function tryFetchFor(name){
            // fetch timeline and scores for a given career name
            try{
                const tRes = await fetch(`${API_BASE}/api/timeline?career=${encodeURIComponent(name)}`)
                const tJson = await tRes.json()
                const sRes = await fetch(`${API_BASE}/api/scores?career=${encodeURIComponent(name)}`)
                const sJson = await sRes.json()
                const latestRow = (sJson && sJson.rows && sJson.rows.length) ? sJson.rows[0] : (Array.isArray(sJson) && sJson.length ? sJson[0] : (sJson.row || sJson));
                return { name, timeline: (tJson.timeline || []), score: latestRow }
            }catch(err){
                return { name, timeline: [], score: null }
            }
        }

        async function load(){
            try{
                setLoading(true)
                setError(null)

                // variants to try if initial career doesn't match DB values
                const variants = [career]
                // try pluralization/singularization
                if(!career.toLowerCase().endsWith('s')) variants.push(career + 's')
                if(career.toLowerCase().endsWith('s')) variants.push(career.replace(/s$/i, ''))
                // capitalization variants
                variants.push(career.replace(/\b\w/, c=>c.toUpperCase()))
                variants.push(career.toLowerCase())

                let result = null
                for(const name of variants){
                    const r = await tryFetchFor(name)
                    // accept if we have a non-empty score row, or a non-empty timeline
                    if((r.score && Object.keys(r.score).length>0) || (r.timeline && r.timeline.length>0)){
                        result = r
                        break
                    }
                }

                // fallback: try original career if nothing found
                if(!result){
                    result = await tryFetchFor(career)
                }

                if(!mounted) return

                const chartData = (result.timeline || []).map(pt => ({ week: pt.date, sentiment: Number(pt.value) }))
                setTimeline(chartData)
                setScore(result.score || null)
                setEffectiveCareer(result.name || career)
            }catch(e){
                console.error(e)
                setError(String(e))
            }finally{
                setLoading(false)
            }
        }
        load()
        return ()=>{ mounted = false }
    }, [API_BASE, career])

    // helper: normalize numeric fields with multiple possible keys
    function getNumber(obj, ...keys){
        if(!obj) return undefined
        for(const k of keys){
            if(Object.prototype.hasOwnProperty.call(obj, k)){
                const v = obj[k]
                if(typeof v === 'number') return v
                const asNum = Number(v)
                if(!Number.isNaN(asNum)) return asNum
            }
        }
        return undefined
    }

    // compute display-friendly values from the returned score row (robust defaults)
    const normalized = (() => {
        if(!score) return null
        const v = getNumber(score, 'vibe_score', 'vibe', 'vibes')
        const avg_sent = getNumber(score, 'avg_sentiment', 'avgSentiment', 'avg_sent', 'sentiment_average', 'sentiment_avg', 'sentiment')
        const forecasted_avg = getNumber(score, 'forecasted_sentiment_avg', 'forecasted_sentiment', 'forecast_avg', 'forecasted')
        const regret = getNumber(score, 'regret_ratio', 'regret', 'regret_ratio_percent')
        const volatility = getNumber(score, 'sentiment_volatility', 'volatility', 'sentiment_std', 'sentiment_vol')

        // vibePercent: try to guess scale intelligently
        let vibePercent = undefined
        if(typeof v === 'number'){
            if(v >= 0 && v <= 5) vibePercent = Math.round(v * 20)            // 0-5 -> 0-100
            else if(v > 5 && v <= 10) vibePercent = Math.round(v * 10)      // 0-10 -> 0-100
            else if(v > 10 && v <= 100) vibePercent = Math.round(v)         // already percent-ish
            else vibePercent = Math.round(v)                                // fallback
        }

        // sentiment: avg_sent in -1..1 -> 0..100
        let sentimentPercent = undefined
        if(typeof avg_sent === 'number'){
            sentimentPercent = Math.round((avg_sent + 1) * 50)
        } else if(typeof forecasted_avg === 'number'){
            sentimentPercent = Math.round((forecasted_avg + 1) * 50)
        }

        // regret and volatility: if 0..1 -> *100, if 0..100 assume already percent
        const normPercent = (x) => {
            if(typeof x !== 'number') return undefined
            if(x >= 0 && x <= 1) return Math.round(x * 100)
            return Math.round(x)
        }
        const regretPercent = normPercent(regret)
        const volatilityPercent = normPercent(volatility)

        return {
            vibeRaw: v,
            vibePercent,
            avg_sent,
            forecasted_avg,
            sentimentPercent,
            regretPercent,
            volatilityPercent,
            raw: score
        }
    })()

    // Compose breakdown string with sensible fallbacks
    const breakdown = (() => {
        if(!normalized) return '80 sentiment  |  34 regret  |  70 volatility'
        const sentiment = (typeof normalized.sentimentPercent === 'number') ? normalized.sentimentPercent : 80
        const regret = (typeof normalized.regretPercent === 'number') ? normalized.regretPercent : 34
        const vol = (typeof normalized.volatilityPercent === 'number') ? normalized.volatilityPercent : 70
        return `${sentiment} sentiment  |  ${regret} regret  |  ${vol} volatility`
    })()

    // compute vibe value to pass to Title (0-100)
    const vibeToShow = (() => {
        if(normalized && typeof normalized.vibePercent === 'number') return normalized.vibePercent
        return 72
    })()

    return (
        <div className="prof-page">
            <div className="prof-backgrounds">
                <div className="prof-background1"></div>
                <div className="prof-background2"></div>
                <div className="prof-background3"></div>
                <div className="prof-background4"></div>
            </div>
            <div className="prof-content">
                <Navbar></Navbar>

                {/* Title receives the selected career and computed values */}
                <Title name={careerLabel || effectiveCareer || career} vibe={vibeToShow} breakdown={breakdown} />

                <div className="top-section">
                    <h1>Overview</h1>
                    <h2>"</h2>
                    <p>Data Analysts enjoy a stable career with positive growth in demand. 
                    However, there are occasional mentions of job stress and limited 
                    advancement opportunities. The work often involves problem-solving 
                    and can be intellectually rewarding.</p>

                    {/* injected API stats - keep class names */}
                    {/* <div className="api-stats">
                        {loading && <div>Loading latest data...</div>}
                        {error && <div className="error">Error: {error}</div>}
                        {!loading && score && (
                            <div>
                                <div>Latest record date: {score.record_date || score.recordDate || '—'}</div>
                                <div>Vibe score (raw): {normalized?.vibeRaw ?? '—'}</div>
                                <div>Vibe (0-100): {vibeToShow}</div>
                                <div>Average sentiment (raw): {normalized?.avg_sent ?? '—'}</div>
                                <div>Forecasted sentiment (raw): {normalized?.forecasted_avg ?? '—'}</div>
                                <div>Breakdown: {breakdown}</div>
                                <div style={{marginTop:8, fontSize:12, color:'#666'}}>Full score object (debug):</div>
                                <pre style={{whiteSpace:'pre-wrap', fontSize:11, maxHeight:180, overflow:'auto'}}>{JSON.stringify(normalized?.raw, null, 2)}</pre>
                            </div>
                        )}
                        {!loading && !score && <div>No score data available</div>}
                    </div> */}
                </div>
                <div className="mid-section">
                    <Chart data={timeline}></Chart>
                </div>
                <div className="bot-section">
                    <Quote></Quote>
                </div>
            </div>
       </div>
    )
}

export default Profession