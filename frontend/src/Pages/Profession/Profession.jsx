
import './Profession.css'
import { useEffect, useState } from 'react'
import Select from 'react-select'
import { useLocation } from 'react-router-dom'
import Navbar from '../../Components/searchComponents/Navbar/Navbar'
import Chart from '../../Components/searchComponents/Chart/Chart'
import Quote from '../../Components/searchComponents/Quote/Quote'
import Title from '../../Components/searchComponents/Title/Title'


function Profession(){
    const [timeline, setTimeline] = useState([])
    const [score, setScore] = useState(null)
    const [summary, setSummary] = useState(null)
    const [quotesList, setQuotesList] = useState([])
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

    // canonical options (keep in sync with Searchbar/CompareBox)
    const canonicalOptions = [
        { value: "police", label: "Police" },
        { value: "humanresources", label: "HR" },
        { value: "Teachers", label: "Teacher" },
        { value: "nursing", label: "Nurse" },
        { value: "physicaltherapy", label: "Physical Therapy" },
        { value: "Lawyertalk", label: "Lawyer" },
        { value: "DataScienceJobs", label: "Data Scientist" },
        { value: "dataanalytics", label: "Data Analyst" },
        { value: "UXResearch", label: "UX Designer" },
    ];

    // UI: compare sidebar state
    const [compareOpen, setCompareOpen] = useState(false)
    const [compareSelected, setCompareSelected] = useState([])
    const [compareMergedFull, setCompareMergedFull] = useState(null)
    const [compareMerged, setCompareMerged] = useState(null)
    const [compareSeries, setCompareSeries] = useState([])
    const [compareAllowedMax, setCompareAllowedMax] = useState(null)
    const [compareDisplayCount, setCompareDisplayCount] = useState(null)
    const [compareInputCount, setCompareInputCount] = useState('')

    useEffect(()=>{
        let mounted = true
        console.debug('Profession mounted', { careerValue, careerLabel, career })
        async function tryFetchFor(name){
            // fetch timeline and scores for a given career name
            try{
                const tRes = await fetch(`${API_BASE}/api/timeline?career=${encodeURIComponent(name)}`)
                const tJson = await tRes.json()
                console.debug('timeline response', { career: name, ok: tRes.ok, body: tJson })
                const sRes = await fetch(`${API_BASE}/api/scores?career=${encodeURIComponent(name)}`)
                const sJson = await sRes.json()
                console.debug('scores response', { career: name, ok: sRes.ok, body: sJson })
                const latestRow = (sJson && sJson.rows && sJson.rows.length) ? sJson.rows[0] : (Array.isArray(sJson) && sJson.length ? sJson[0] : (sJson.row || sJson));
                console.debug('latestRow parsed', { career: name, latestRow })
                return { name, timeline: (tJson.timeline || []), score: latestRow }
            }catch(err){
                console.error('tryFetchFor error', { career: name, err })
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

                console.debug('trying variants for career', { career, variants })
                let result = null
                for(const name of variants){
                    const r = await tryFetchFor(name)
                    console.debug('variant result', { tried: name, hasScore: !!(r.score && Object.keys(r.score).length>0), timelineLen: (r.timeline || []).length })
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
                // Append a one-month-ahead forecast point (4 weekly ticks ahead).
                try{
                    const mostRecentDateStr = chartData.length ? chartData[chartData.length-1].week : null
                    const forecastVal = result.score && (result.score.forecasted_sentiment_avg ?? result.score.forecastedSentimentAvg ?? null)
                    if(forecastVal !== null && forecastVal !== undefined){
                        // compute weekly ticks after the most recent date: +1w, +2w, +3w (gaps), +4w (forecast)
                        let baseDate = null
                        if(mostRecentDateStr){
                            const d = new Date(mostRecentDateStr)
                            if(!isNaN(d.getTime())) baseDate = d
                        }
                        if(!baseDate){
                            baseDate = new Date()
                        }

                        // create 3 gap points (sentiment=null) and then the forecast point at +4 weeks
                        for(let i=1;i<=4;i++){
                            const ptDate = new Date(baseDate)
                            ptDate.setDate(ptDate.getDate() + (7 * i))
                            const iso = ptDate.toISOString().slice(0,10)
                            // skip if a point with the same week already exists
                            if(chartData.find(pt => pt.week === iso)) continue
                            if(i < 4){
                                chartData.push({ week: iso, sentiment: null, isGap: true })
                            } else {
                                chartData.push({ week: iso, sentiment: Number(forecastVal), isForecast: true })
                            }
                        }
                    }
                }catch(e){
                    console.info('Could not compute future forecast point', e)
                }
                setTimeline(chartData)
                setScore(result.score || null)
                setEffectiveCareer(result.name || career)
                console.debug('final chosen career result', { resultName: result.name, effective: result.name || career, score: result.score, timelineLen: chartData.length })

                // Fetch career summary (if available) and show it in the Overview
                try{
                    const summaryRes = await fetch(`${API_BASE}/api/career_summaries?career=${encodeURIComponent(result.name || career)}&limit=1`)
                    const summaryJson = await summaryRes.json()
                    console.debug('career_summaries response', { career: result.name || career, ok: summaryRes.ok, body: summaryJson })
                    // prefer top-level summary when provided
                    if(summaryJson && summaryJson.summary !== undefined){
                        setSummary(summaryJson.summary)
                        console.debug('set summary (top-level)', summaryJson.summary)
                    } else {
                        const rows = summaryJson && (summaryJson.rows || summaryJson.data || summaryJson)
                        if(Array.isArray(rows) && rows.length){
                            setSummary(rows[0].summary || null)
                            console.debug('set summary (rows[0].summary)', rows[0].summary)
                        } else {
                            setSummary(null)
                            console.debug('no summary rows found')
                        }
                    }
                }catch(e){
                    // don't block the page if summary fetch fails
                    console.info('Could not fetch career summary', e)
                    setSummary(null)
                }

                // Fetch quotes for the career and pass to the Quote component
                try{
                    const qRes = await fetch(`${API_BASE}/api/quotes?career=${encodeURIComponent(result.name || career)}&limit=5&random=true`)
                    const qJson = await qRes.json()
                    console.debug('quotes response', { career: result.name || career, ok: qRes.ok, body: qJson })
                    const qrows = qJson && (qJson.rows || qJson.data || qJson)
                    if(Array.isArray(qrows) && qrows.length){
                        // map to quote text (quote_body or quote)
                        const mapped = qrows.map(r => r.quote_body || r.quote || r.quoteBody || '')
                        setQuotesList(mapped.filter(Boolean))
                        console.debug('set quotesList', mapped)
                    } else {
                        setQuotesList([])
                        console.debug('no quotes rows found')
                    }
                }catch(e){
                    console.info('Could not fetch quotes', e)
                    setQuotesList([])
                }
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

    // Display raw data only — don't perform any scaling or math on values.
    const rawScore = score || null
    const breakdown = rawScore ? `${rawScore.avg_sentiment ?? '-'} sentiment  |  ${rawScore.regret_ratio ?? '-'} regret  |  ${rawScore.sentiment_volatility ?? '-'} volatility` : '—'
    const vibeToShow = rawScore && rawScore.vibe_score !== undefined ? rawScore.vibe_score : undefined

    return (
        <div className="prof-page">
            <div className="prof-backgrounds">
                <div className="prof-background0"></div>
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
                    {summary ? (
                        <p>{summary}</p>
                    ) : (
                        <p>Data Analysts enjoy a stable career with positive growth in demand. 
                        However, there are occasional mentions of job stress and limited 
                        advancement opportunities. The work often involves problem-solving 
                        and can be intellectually rewarding.</p>
                    )}

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
                    <div style={{ position: 'relative', width: '100%' }}>
                        <button className="chart-compare-toggle" onClick={() => setCompareOpen(v => !v)} title="Compare">▶</button>
                        <Chart data={timeline} compareData={compareMerged} compareSeries={compareSeries}></Chart>
                    </div>

                    {/* Compare sidebar */}
                    <div className={`compare-sidebar ${compareOpen ? 'open' : ''}`}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px' }}>
                            <strong style={{ fontFamily: "'Itim', cursive" }}>Quick Compare</strong>
                            <button onClick={() => setCompareOpen(false)} style={{ border: 'none', background: 'transparent', cursor: 'pointer' }}>✕</button>
                        </div>
                        <div style={{ padding: '0 16px 16px 16px' }}>
                            <Select
                                isMulti
                                options={canonicalOptions.filter(o => (o.label !== (careerLabel || effectiveCareer || career)))}
                                value={compareSelected}
                                onChange={setCompareSelected}
                                placeholder="Select professions to compare"
                            />
                            <div className="compare-controls" style={{ marginTop: 12 }}>
                                <div className="compare-datapoint" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                    <label style={{ fontFamily: "'Itim', cursive", fontSize: 13, color: '#333' }}>Datapoints:</label>
                                    <input type="number" min={1} value={compareInputCount} onChange={(e)=>setCompareInputCount(e.target.value)} style={{ width: 80, padding: '6px 8px', borderRadius: 6, border: '1px solid #ddd' }} />
                                    <button onClick={() => {
                                        const parsed = Number(compareInputCount) || 0
                                        if(!compareMergedFull) return
                                        const clamped = Math.max(1, Math.min(parsed, compareAllowedMax || compareMergedFull.length))
                                        setCompareDisplayCount(clamped)
                                        setCompareMerged(compareMergedFull.slice(-clamped))
                                        try{ if(typeof window !== 'undefined') window.localStorage.setItem('prof_compare_display_count', String(clamped)) }catch(e){}
                                    }} style={{ padding: '6px 10px', borderRadius: 6, border: 'none', background: '#667eea', color: 'white', cursor: 'pointer' }}>Apply</button>
                                </div>
                                <div className="compare-max-note" style={{ display: 'flex', alignItems: 'center', fontSize: 12, color:'#666' }}>{compareAllowedMax ? `(max ${compareAllowedMax})` : ''}</div>
                                <button onClick={async () => {
                                            // fetch timelines for selected options and merge; always include the current career timeline
                                            if(!compareSelected || compareSelected.length === 0) return
                                            const per = {}
                                            // include base career timeline (map existing `timeline` state to same shape)
                                            const baseName = careerLabel || effectiveCareer || career
                                            per[baseName] = (timeline || []).map(pt => ({ date: pt.week, value: pt.sentiment, raw: pt, isForecast: pt.isForecast }))
                                            for(const s of compareSelected){
                                                const candidates = [s.value, s.label].filter(Boolean)
                                                let tl = null
                                                for(const c of candidates){
                                                    try{
                                                        const res = await fetch(`${API_BASE}/api/timeline?career=${encodeURIComponent(c)}&include_forecast=true&include_aggregate=true`)
                                                        if(!res.ok) continue
                                                        const j = await res.json()
                                                        if(j && Array.isArray(j.timeline) && j.timeline.length){ tl = j.timeline; break }
                                                    }catch(e){ continue }
                                                }
                                                per[s.label || s.value] = tl || []
                                            }
                                            // merge timelines by date
                                            const merged = {}
                                            Object.keys(per).forEach(profName => {
                                                const t = per[profName] || []
                                                t.forEach(pt => {
                                                    const dt = pt.date || pt.record_date || pt.week || null
                                                    if(!dt) return
                                                    if(!merged[dt]) merged[dt] = { date: dt }
                                                    const rawVal = pt.value !== undefined ? pt.value : (pt.sentiment_average !== undefined ? pt.sentiment_average : (pt.raw && (pt.raw.forecasted_sentiment_avg ?? pt.raw.avg_sentiment)))
                                                    const num = rawVal === null || rawVal === undefined ? null : Number(rawVal)
                                                    merged[dt][profName] = Number.isNaN(num) ? null : num
                                                })
                                            })
                                            const mergedArray = Object.keys(merged).sort().map(k => merged[k])

                                            // compute per-prof counts to enforce allowed-max rule (max difference 5)
                                            const counts = Object.keys(per).map(k => (per[k] || []).length).sort((a,b)=>b-a)
                                            const top = counts[0] || 0
                                            const second = counts.length >= 2 ? counts[1] : 0
                                            const computedAllowed = counts.length >=2 ? Math.min(top, second + 5) : top

                                            // prepare series colors (ensure base career appears first)
                                            const colors = ["#57AAC8", "#FF6B6B", "#4ECDC4", "#FFD93D", "#6BCF7F", "#A78BFA"]
                                            const baseSeries = [{ name: baseName, color: colors[0] }]
                                            const otherSeries = compareSelected.map((s,i)=>({ name: s.label || s.value, color: colors[(i+1) % colors.length] }))
                                            const series = [...baseSeries, ...otherSeries]

                                            // set states: store full merged array, computed allowed max, and default display count = allowed max
                                            setCompareSeries(series)
                                            setCompareMergedFull(mergedArray)
                                            setCompareAllowedMax(computedAllowed)
                                            const chosen = Math.min(computedAllowed || mergedArray.length, mergedArray.length)
                                            setCompareDisplayCount(chosen)
                                            setCompareInputCount(String(chosen))
                                            setCompareMerged(mergedArray.slice(-chosen))
                                            try{ if(typeof window !== 'undefined') window.localStorage.setItem('prof_compare_display_count', String(chosen)) }catch(e){}
                                            }} style={{ padding: '8px 12px', borderRadius: 8, border: 'none', background: '#667eea', color: 'white', cursor: 'pointer' }} className="compare-action">Compare</button>
                                        <button className="compare-clear" onClick={() => { setCompareSelected([]); setCompareMerged(null); setCompareSeries([]); }} style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid #ccc', background: 'white', cursor: 'pointer' }}>Clear</button>
                                    </div>
                        </div>
                    </div>
                </div>
                <div className="bot-section">
                    <Quote quotes={quotesList}></Quote>
                </div>
            </div>
       </div>
    )
}

export default Profession