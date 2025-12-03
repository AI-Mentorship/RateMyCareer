import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts';
import Select from 'react-select';
import './ComparisonPage.css';
import '../../Components/searchComponents/Chart/Chart.css';
import Navbar from '../../Components/searchComponents/Navbar/Navbar';
import Footer from '../../Components/Footer/Footer';
import comparisonBg from "../../assets/background.jpg";
import { localData } from '../../utils/localData';

function ComparisonPage() {
  const availableProfessions = [
    "Data Scientist",
    "HR/Management",
    "Physical Therapist",
    "Teacher",
    "Lawyer",
    "Police",
    "UX",
    "Data Analyst",
    "Nursing"
  ];

  // Canonical options - keep in sync with Searchbar.jsx
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

  // State to manage professions being compared
  const location = useLocation()
  const incoming = location && location.state && Array.isArray(location.state.compare) ? location.state.compare : null
  const defaultColors = ["#FF6B6B", "#4ECDC4", "#FFD93D", "#6BCF7F", "#A78BFA", "#FB923C", "#F472B6"]
  // incoming may be array of strings or objects {value,label}
  const initialProfessions = incoming && incoming.length ? incoming.map((item, i) => {
    let displayName = ''
    let apiValue = null
    if(typeof item === 'string'){
      displayName = item
      apiValue = item
    } else if(item && typeof item === 'object'){
      displayName = item.label || item.value || ''
      apiValue = item.value || item.label || null
    }
    return ({ id: i+1, name: displayName, apiValue, vibeScore: 50, sentiment: 50, regret: 40, volatility: 40, color: defaultColors[i % defaultColors.length] })
  }) : [
    {
      id: 1,
      name: "Data Scientist",
      vibeScore: 72,
      sentiment: 68,
      regret: 25,
      volatility: 45,
      color: "#FF6B6B" 
    },
    {
      id: 2,
      name: "Teacher",
      vibeScore: 58,
      sentiment: 55,
      regret: 42,
      volatility: 38,
      color: "#4ECDC4" 
    }
  ];

  const [professions, setProfessions] = useState(initialProfessions);

  // NOTE: Do not change formatting of numeric values returned from the API.
  // We preserve the raw values from the backend for display in the comparison table.

  // fetch latest scores for a career using /api/scores and update professions state
  // accepts either a string (career) or an object { value, label }
  async function fetchAndUpdateMetrics(nameOrObj){
    try{
      const candidates = []
      if(!nameOrObj) return null
      if(typeof nameOrObj === 'string') candidates.push(nameOrObj)
      else if(typeof nameOrObj === 'object'){
        if(nameOrObj.apiValue) candidates.push(nameOrObj.apiValue)
        if(nameOrObj.value) candidates.push(nameOrObj.value)
        if(nameOrObj.label) candidates.push(nameOrObj.label)
      }
      // also accept when called with a profession object that has apiValue
      if(typeof nameOrObj === 'object' && nameOrObj.apiValue) {
        // already included above
      }

      // dedupe candidates and remove falsy
      let uniq = [...new Set(candidates.filter(Boolean))]
      if(uniq.length === 0 && typeof nameOrObj === 'object' && nameOrObj.name) uniq.push(nameOrObj.name)
      let row = null
      for(const c of uniq){
        const j = await localData.getScores(c)
        const rows = j && (j.rows || j.data || j)
        const candidateRow = Array.isArray(rows) && rows.length ? rows[0] : null
        if(candidateRow){ row = candidateRow; break }
      }
      if(!row) return null
      // Preserve raw API values (no rounding or scaling) so the UI shows exactly what the backend returned
      return {
        vibeScore: row.vibe_score !== undefined ? row.vibe_score : null,
        sentiment: row.avg_sentiment !== undefined ? row.avg_sentiment : null,
        regret: row.regret_ratio !== undefined ? row.regret_ratio : null,
        volatility: row.sentiment_volatility !== undefined ? row.sentiment_volatility : null,
      }
    }catch(e){
      console.debug('Could not fetch scores for', nameOrObj, e)
      return null
    }
  }

  // On mount, try to replace the hardcoded metrics with live data from the API
  useEffect(()=>{
    let mounted = true
    async function loadAll(){
      const updated = []
      for(const prof of professions){
        const metrics = await fetchAndUpdateMetrics(prof)
        if(metrics && mounted){
          updated.push({ ...prof, ...metrics })
        } else {
          updated.push(prof)
        }
      }
      if(mounted) setProfessions(updated)
    }
    loadAll()
    return ()=>{ mounted = false }
  }, [])

  const [selectedProfession, setSelectedProfession] = useState(null);
  // Sentiment timeline data (merged per-week/date across compared professions)
  const [sentimentData, setSentimentData] = useState([]);
  // cache timelines per profession to avoid re-fetching when changing view
  const [perProfTimelines, setPerProfTimelines] = useState({});
  const [displayCount, setDisplayCount] = useState(() => {
    try{
      const v = window.localStorage.getItem('compare_display_count')
      return v ? Number(v) : null
    }catch(e){ return null }
  });
  const [allowedMax, setAllowedMax] = useState(null);
  const [inputCount, setInputCount] = useState(() => {
    try{ const v = window.localStorage.getItem('compare_display_count'); return v ? String(v) : '' }catch(e){ return '' }
  });
  const [topCount, setTopCount] = useState(null);

  // compute median and yDomain for the comparison chart similar to Chart.jsx
  let numericVals = [];
  let nonForecastVals = [];
  if (sentimentData && sentimentData.length) {
    sentimentData.forEach(row => {
      Object.keys(row).forEach(k => {
        if (k === 'date') return;
        const v = row[k];
        if (v === null || v === undefined || Number.isNaN(Number(v))) return;
        numericVals.push(Number(v));
        // no forecast flag available here, include all values as non-forecast
        nonForecastVals.push(Number(v));
      });
    });
  }

  let yDomain = [-0.25, 0.25];
  let median = null;
  if (nonForecastVals.length) {
    const sorted = nonForecastVals.slice().sort((a, b) => a - b);
    const mlen = sorted.length;
    const mid = Math.floor(mlen / 2);
    median = (mlen % 2 === 1) ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
    const min = sorted[0];
    const max = sorted[sorted.length - 1];
    if (min === max) {
      const pad = Math.abs(min) * 0.1 || 0.05;
      yDomain = [min - pad, max + pad];
    } else {
      const delta = Math.max(Math.abs(median - min), Math.abs(max - median));
      const pad = delta * 0.1;
      yDomain = [median - delta - pad, median + delta + pad];
    }
    yDomain[0] = Math.max(-1, yDomain[0]);
    yDomain[1] = Math.min(1, yDomain[1]);
  } else if (numericVals.length) {
    const min = Math.min(...numericVals);
    const max = Math.max(...numericVals);
    if (min === max) {
      const pad = Math.abs(min) * 0.1 || 0.05;
      yDomain = [min - pad, max + pad];
    } else {
      const range = max - min;
      const pad = range * 0.1;
      yDomain = [min - pad, max + pad];
    }
    yDomain[0] = Math.max(-1, yDomain[0]);
    yDomain[1] = Math.min(1, yDomain[1]);
    const sorted = numericVals.slice().sort((a, b) => a - b);
    const mlen = sorted.length;
    const mid = Math.floor(mlen / 2);
    median = (mlen % 2 === 1) ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
  }

  // Fetch weekly timelines for each profession and merge into a single dataset
  // Fetch and cache timelines per profession (runs when `professions` change)
  useEffect(() => {
    let mounted = true;
    async function loadTimelines() {
      try {
        const fetched = {};
        for (const prof of professions) {
          const candidates = [];
          if (prof.apiValue) candidates.push(prof.apiValue);
          if (prof.value) candidates.push(prof.value);
          if (prof.name) candidates.push(prof.name);
          const uniq = [...new Set(candidates.filter(Boolean))];
          let timeline = null;
          for (const c of uniq) {
            try {
              const j = await localData.getTimeline(c)
              if (j && Array.isArray(j.timeline) && j.timeline.length) {
                timeline = j.timeline;
                break;
              }
            } catch (e) {
              continue;
            }
          }
          fetched[prof.name] = timeline || [];
        }
        if (mounted) setPerProfTimelines(fetched);
      } catch (e) {
        console.debug('Error loading timelines', e);
      }
    }
    loadTimelines();
    return () => { mounted = false };
  }, [professions]);

  // Compute merged mergedArray and allowedMax and set sentimentData when timelines or displayCount change
  useEffect(() => {
    // helper to merge timelines
    const merged = {};
    Object.keys(perProfTimelines).forEach((profName) => {
      const t = perProfTimelines[profName] || [];
      t.forEach(pt => {
        const dt = pt.date || pt.record_date || pt.week || null;
        if (!dt) return;
        if (!merged[dt]) merged[dt] = { date: dt };
        const rawVal = pt.value !== undefined ? pt.value : (pt.sentiment_average !== undefined ? pt.sentiment_average : (pt.raw && (pt.raw.forecasted_sentiment_avg ?? pt.raw.avg_sentiment)));
        const num = rawVal === null || rawVal === undefined ? null : Number(rawVal);
        merged[dt][profName] = Number.isNaN(num) ? null : num;
      });
    });

    let mergedArray = Object.keys(merged).sort().map(k => merged[k]);

    // fallback if no timelines available
    if (mergedArray.length === 0) {
      const fallback = [];
      for (let i = 1; i <= 8; i++) {
        const row = { date: `Week ${i}` };
        professions.forEach(prof => {
          const v = prof.sentiment;
          row[prof.name] = typeof v === 'number' ? v : (v ? Number(v) : null);
        });
        fallback.push(row);
      }
      mergedArray = fallback;
    }

    // compute counts per profession
    const counts = Object.keys(perProfTimelines).map(k => perProfTimelines[k]?.length || 0).sort((a,b) => b-a);
    const top = counts[0] || 0;
    const second = counts.length >= 2 ? counts[1] : null;
    const computedAllowedMax = counts.length >= 2 ? Math.min(top, (second || 0) + 5) : top;
    // store top count (career with most datapoints)
    const topVal = top || mergedArray.length;
    setTopCount(topVal);
    setAllowedMax(computedAllowedMax || mergedArray.length);

    // Always set displayCount to the computed allowed max when timelines refresh (e.g., after adding a career)
    const chosen = Math.min(computedAllowedMax || mergedArray.length, mergedArray.length);
    setAllowedMax(chosen);
    setDisplayCount(chosen);
    setSentimentData(mergedArray.slice(-chosen));
    try { if (typeof window !== 'undefined') window.localStorage.setItem('compare_display_count', String(chosen)); } catch (e) {}
  }, [perProfTimelines]);

  // keep local input in sync when allowedMax/displayCount change
  useEffect(() => {
    if (displayCount !== null) setInputCount(String(displayCount));
  }, [displayCount]);

  // when displayCount changes (by user), recompute sentimentData slice without re-fetching
  useEffect(() => {
    if (!perProfTimelines || Object.keys(perProfTimelines).length === 0 || displayCount == null) return;
    const merged = {};
    Object.keys(perProfTimelines).forEach((profName) => {
      const t = perProfTimelines[profName] || [];
      t.forEach(pt => {
        const dt = pt.date || pt.record_date || pt.week || null;
        if (!dt) return;
        if (!merged[dt]) merged[dt] = { date: dt };
        const rawVal = pt.value !== undefined ? pt.value : (pt.sentiment_average !== undefined ? pt.sentiment_average : (pt.raw && (pt.raw.forecasted_sentiment_avg ?? pt.raw.avg_sentiment)));
        const num = rawVal === null || rawVal === undefined ? null : Number(rawVal);
        merged[dt][profName] = Number.isNaN(num) ? null : num;
      });
    });
    let mergedArray = Object.keys(merged).sort().map(k => merged[k]);
    if (mergedArray.length === 0) return;
    const clamped = Math.min(displayCount, allowedMax || mergedArray.length);
    setSentimentData(mergedArray.slice(-clamped));
  }, [displayCount, perProfTimelines, allowedMax]);

  const getAvailableOptions = () => {
    // Prevent selecting professions that are already shown by checking both label and value
    const comparedLabels = professions.map(p => String(p.name).trim());
    const comparedValues = professions.map(p => (p.apiValue ? String(p.apiValue).trim() : null));
    return canonicalOptions.filter(opt => {
      if (!opt) return false;
      if (comparedLabels.includes(opt.label)) return false;
      if (opt.value && comparedValues.includes(opt.value)) return false;
      return true;
    });
  };

  // Function to add a new profession
  const handleAddProfession = (selectedOption) => {
    if (!selectedOption) return;

    const colors = ["#FFD93D", "#6BCF7F", "#A78BFA", "#FB923C", "#F472B6"];
    
    (async ()=>{
      const base = {
        id: professions.length + 1,
        name: selectedOption.label || selectedOption.value,
        apiValue: selectedOption.value,
        color: colors[(professions.length - 2) % colors.length]
      }
      const metrics = await fetchAndUpdateMetrics(selectedOption.value)
      const newProfession = metrics ? { ...base, ...metrics } : { ...base,
        vibeScore: Math.floor(Math.random() * 40 + 40),
        sentiment: Math.floor(Math.random() * 40 + 40),
        regret: Math.floor(Math.random() * 60 + 20),
        volatility: Math.floor(Math.random() * 50 + 25),
      }
      setProfessions(prev => [...prev, newProfession])
      setSelectedProfession(null)
    })()
  };

  const customSelectStyles = {
    control: (provided) => ({
      ...provided,
      border: 'none',
      boxShadow: 'none',
      backgroundColor: 'white',
      minHeight: '40px',
      borderRadius: '40px',
    }),
    placeholder: (provided) => ({
      ...provided,
      fontFamily: "'Itim', cursive",
      fontSize: '14px',
      color: '#999',
    }),
    singleValue: (provided) => ({
      ...provided,
      fontFamily: "'Itim', cursive",
      fontSize: '14px',
    }),
    menu: (provided) => ({
      ...provided,
      borderRadius: '12px',
      overflow: 'hidden',
    }),
    // Make the options list scrollable if it grows too tall
    menuList: (provided) => ({
      ...provided,
      maxHeight: '220px',
      overflowY: 'auto',
    }),
    option: (provided, state) => ({
      ...provided,
      fontFamily: "'Itim', cursive",
      fontSize: '14px',
      backgroundColor: state.isSelected ? '#667eea' : state.isFocused ? '#f0f0f0' : 'white',
      color: state.isSelected ? 'white' : '#333',
    // Ensure the menu displays above other content when rendered inline
    menu: (provided) => ({
      ...provided,
      zIndex: 9999,
    }),
    }),
  };

  return (
    <div className="comparison-page">
      {/* Diagonal split background with blue and yellow */}
      <div className="comparison-background">
        <div className="nav-background"></div>
        <div className="blue-half" style={{ backgroundImage: `url(${comparisonBg})` }}></div>
        <div className="yellow-half"></div>
        <div className="gray-half"></div>
      </div>

      <div className="comparison-content">
        <Navbar></Navbar>
        <div className="comparison-main-container">
          
          {/* Comparison Table */}
          <div className="comparison-table-section">
          <div className="table-header-label">Comparison Table</div>
          <div className="comparison-table">
            
            {/* Header row with profession names */}
            <div className="table-header-row">
              <div className="table-header-cell metric-name-header">Metrics</div>
              {professions.map((prof) => (
                <div 
                  key={prof.id} 
                  className="table-header-cell profession-header"
                  style={{ backgroundColor: prof.color }}
                >
                  {prof.name}
                </div>
              ))}
            </div>

            {/* Vibe score row */}
            <div className="table-row">
              <div className="table-cell metric-name">Vibe Score</div>
              {professions.map((prof) => (
                <div key={prof.id} className="table-cell metric-value">{prof.vibeScore}</div>
              ))}
            </div>

            {/* Sentiment row */}
            <div className="table-row alt-row">
              <div className="table-cell metric-name">Sentiment</div>
              {professions.map((prof) => (
                <div key={prof.id} className="table-cell metric-value">{prof.sentiment}</div>
              ))}
            </div>

            {/* Regret row */}
            <div className="table-row">
              <div className="table-cell metric-name">Regret</div>
              {professions.map((prof) => (
                <div key={prof.id} className="table-cell metric-value">{prof.regret}</div>
              ))}
            </div>

            {/* Volatility row */}
            <div className="table-row alt-row">
              <div className="table-cell metric-name">Volatility</div>
              {professions.map((prof) => (
                <div key={prof.id} className="table-cell metric-value">{prof.volatility}</div>
              ))}
            </div>
          </div>

          {/* "Add Profession" dropdown */}
          <div className="add-profession-container">
            <Select
              value={selectedProfession}
              onChange={handleAddProfession}
              options={getAvailableOptions()}
              placeholder="+ Add Profession to Compare"
              styles={customSelectStyles}
              className="add-profession-select"
              isClearable
              menuPlacement="auto"
              menuPosition="absolute"
              menuShouldScrollIntoView={true}
            />
          </div>
        </div>

        {/* Sentiment trend graph with multiple professions */}
        <div className="sentiment-graph-section">
          <h2 className="graph-title">Sentiment Trend</h2>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '12px', marginBottom: '8px' }}>
            <label style={{ fontFamily: "'Itim', cursive", fontSize: 14, color: '#333' }}>Datapoints to show:</label>
            <input
              type="number"
              min={1}
              max={allowedMax || 1000}
              value={inputCount}
              onChange={(e) => setInputCount(e.target.value)}
              style={{ width: 80, padding: '6px 8px', borderRadius: 8, border: '1px solid #ddd' }}
            />
            <button
              onClick={() => {
                const parsed = Number(inputCount) || 0;
                const clamped = Math.max(1, Math.min(parsed, allowedMax || parsed));
                setDisplayCount(clamped);
                try { window.localStorage.setItem('compare_display_count', String(clamped)); } catch (e) {}
              }}
              style={{ padding: '6px 10px', borderRadius: 8, border: 'none', background: '#667eea', color: 'white', cursor: 'pointer' }}
            >Apply</button>
            <div style={{ fontSize: 12, color: '#666' }}>{allowedMax ? `(max ${allowedMax} by rule)` : ''}</div>
          </div>

          <div className="graph">
            <h1 style={{display:'none'}}>sentiment trend</h1>
            <div className="mood-label-left mood-label-top">Happiness</div>
            <div className="mood-label-left mood-label-median">Median</div>
            <div className="mood-label-left mood-label-bottom">Frustration</div>
            <ResponsiveContainer width="100%" height={360}>
              <LineChart data={sentimentData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                <XAxis
                  dataKey="date"
                  tick={{ fill: '#666', fontSize: 12 }}
                  stroke="#999"
                />
                <YAxis
                  tick={false}
                  tickLine={false}
                  stroke="#999"
                  domain={yDomain}
                />
                <Tooltip />
                <Legend />
                {median !== null && !Number.isNaN(Number(median)) && (
                  <ReferenceLine y={median} stroke="#999" strokeDasharray="4 4" strokeWidth={1} />
                )}
                {professions.map((prof) => (
                  <Line
                    key={prof.id}
                    type="monotone"
                    dataKey={prof.name}
                    stroke={prof.color}
                    strokeWidth={3}
                    dot={{ r: 4 }}
                    activeDot={{ r: 6 }}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>

        </div>
      </div>
      <Footer />
    </div>
  </div>
  );
}

export default ComparisonPage;