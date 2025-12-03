import './Standing.css'
import Topbar from './Topbar.jsx'
import { useEffect, useState } from 'react'

function ordinal(n){
    if(typeof n !== 'number') return ''
    const rem100 = n % 100
    if(rem100 >= 11 && rem100 <= 13) return `${n}th`
    const rem10 = n % 10
    if(rem10 === 1) return `${n}st`
    if(rem10 === 2) return `${n}nd`
    if(rem10 === 3) return `${n}rd`
    return `${n}th`
}

function Standing() {
    const [rows, setRows] = useState(null)
    const [error, setError] = useState(null)
    const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'

    useEffect(()=>{
        let mounted = true
        async function load(){
            try{
                const res = await fetch(`${API_BASE}/api/rankings?limit=5`)
                const j = await res.json()
                // api returns { data: [...] }
                const data = j && (j.data || j.rows || j)
                if(!mounted) return
                if(Array.isArray(data) && data.length){
                    setRows(data)
                } else {
                    setRows([])
                }
            }catch(e){
                console.error('Could not load rankings', e)
                if(mounted){
                    setError(String(e))
                    setRows([])
                }
            }
        }
        load()
        return ()=>{ mounted = false }
    }, [API_BASE])

    const fallback = [
        { profession: 'Teacher', score: 5 },
        { profession: 'Lawyer', score: 4.8 },
        { profession: 'Police', score: 4.5 },
        { profession: 'Data Analyst', score: 4.5 },
        { profession: 'Nurse', score: 4.4 },
    ]

    const display = (rows && rows.length) ? rows : fallback

    return (
        <div className="standing">
            <div className="ranking-tilte">Leaderboard</div>
            {display.map((r, idx) => {
                const rankLabel = ordinal(idx + 1)
                // API row may present career_name or careerName
                const profession = r.career_name || r.careerName || r.profession || r.career || r.title || ''
                // prefer vibe_score, then avg_sentiment, then generic score
                const rawScore = r.vibe_score ?? r.avg_sentiment ?? r.score ?? r.value ?? null
                const score = (rawScore !== null && rawScore !== undefined && !Number.isNaN(Number(rawScore))) ? Number(rawScore) : null
                const scoreDisplay = score !== null ? Number(score).toFixed(1) : '—'
                return (
                    <Topbar key={profession + idx} rank={rankLabel} profession={profession} score={scoreDisplay}></Topbar>
                )
            })}
            {error && <div className="ranking-error">Error loading leaderboard</div>}
        </div>
    )
}

export default Standing