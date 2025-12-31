import './Chart.css'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, Legend } from 'recharts';

function Chart({ data, compareData, compareSeries }) {
    // If compareData is provided (merged series), render multi-line chart using compareData
    const sentimentData = (compareData && compareData.length) ? compareData : (data && data.length ? data : [
        { week: 'Week 1', sentiment: 0.2 },
        { week: 'Week 2', sentiment: 0.4 },
        { week: 'Week 3', sentiment: 0.3 },
        { week: 'Week 4', sentiment: 0.5 },
        { week: 'Week 5', sentiment: 0.6 },
        { week: 'Week 6', sentiment: 0.7 },
        { week: 'Week 7', sentiment: 0.65 },
        { week: 'Week 8', sentiment: 0.8 },
    ]);
    // numeric values (including forecast) and non-forecast values (for median & centering)
    // Support both single-series shape (week/sentiment) and multi-series merged shape (date + keys)
    let numericVals = [];
    let nonForecastVals = [];
    if (compareData && compareData.length) {
        // merged objects: loop keys except 'date'
        compareData.forEach(row => {
            Object.keys(row).forEach(k => {
                if (k === 'date') return;
                const v = row[k];
               if (v === null || v === undefined || Number.isNaN(Number(v))) return;
                numericVals.push(Number(v));
                // no forecast/ isForecast flag in merged data currently, so include all in nonForecastVals
                nonForecastVals.push(Number(v));
            });
        });
    } else {
        numericVals = sentimentData
            .map(p => (p && p.sentiment !== null && p.sentiment !== undefined && !Number.isNaN(Number(p.sentiment))) ? Number(p.sentiment) : null)
            .filter(v => v !== null);

        nonForecastVals = sentimentData
            .filter(p => p && p.sentiment !== null && p.sentiment !== undefined && !Number.isNaN(Number(p.sentiment)) && !p.isForecast)
            .map(p => Number(p.sentiment));
    }

    let yDomain = [-0.25, 0.25]
    // compute median from non-forecast values (so forecast doesn't affect center)
    let median = null
    if(nonForecastVals.length){
        const sorted = nonForecastVals.slice().sort((a,b)=>a-b)
        const mlen = sorted.length
        const mid = Math.floor(mlen/2)
        median = (mlen % 2 === 1) ? sorted[mid] : (sorted[mid-1] + sorted[mid]) / 2

        const min = sorted[0]
        const max = sorted[sorted.length - 1]
        if(min === max){
            const pad = Math.abs(min) * 0.1 || 0.05
            yDomain = [min - pad, max + pad]
        } else {
            // center domain around the median: use the larger distance to min/max and add padding
            const delta = Math.max(Math.abs(median - min), Math.abs(max - median))
            const pad = delta * 0.1
            yDomain = [median - delta - pad, median + delta + pad]
        }
        // clamp to reasonable bounds
        yDomain[0] = Math.max(-1, yDomain[0])
        yDomain[1] = Math.min(1, yDomain[1])
    } else if(numericVals.length){
        // fallback: compute domain from all numeric values (including forecast) if no non-forecast points
        const min = Math.min(...numericVals)
        const max = Math.max(...numericVals)
        if(min === max){
            const pad = Math.abs(min) * 0.1 || 0.05
            yDomain = [min - pad, max + pad]
        } else {
            const range = max - min
            const pad = range * 0.1
            yDomain = [min - pad, max + pad]
        }
        yDomain[0] = Math.max(-1, yDomain[0])
        yDomain[1] = Math.min(1, yDomain[1])
        // compute median from numericVals as a best-effort
        const sorted = numericVals.slice().sort((a,b)=>a-b)
        const mlen = sorted.length
        const mid = Math.floor(mlen/2)
        median = (mlen % 2 === 1) ? sorted[mid] : (sorted[mid-1] + sorted[mid]) / 2
    }
    return (
        <div className="graph">
            <h1>sentiment trend</h1>
            {/* Left-side mood labels: top (Happiness), middle (Median), bottom (Frustration) */}
            <div className="mood-label-left mood-label-top">Happiness</div>
            <div className="mood-label-left mood-label-median">Median</div>
            <div className="mood-label-left mood-label-bottom">Frustration</div>
            {/* increase vertical space and focus Y axis on a tighter sentiment range */}
            {/* use 100% width so the chart fills the parent .graph area */}
            <ResponsiveContainer width="100%" height={360}>
                <LineChart data={sentimentData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey={compareData && compareData.length ? 'date' : 'week'} />
                    {/* remove tick labels as requested; axis line kept */}
                    <YAxis domain={yDomain} tick={false} tickLine={false} />
                    <Tooltip />
                    <Legend verticalAlign="bottom" align="center" />
                    {/* median line (dotted) across chart excluding forecast point */}
                    {median !== null && !Number.isNaN(Number(median)) && (
                        <ReferenceLine y={median} stroke="#999" strokeDasharray="4 4" strokeWidth={1} />
                    )}
                    {
                        // custom dot renderer to color forecast points red
                    }
                    {
                        (compareData && compareData.length && Array.isArray(compareSeries) && compareSeries.length) ? (
                            (() => {
                                // compute last non-null index for each series so we only place one label per line
                                const lastIndexBySeries = {};
                                compareSeries.forEach((s) => {
                                    let idx = -1;
                                    for (let i = sentimentData.length - 1; i >= 0; i--) {
                                        const v = sentimentData[i] && sentimentData[i][s.name];
                                        if (v !== null && v !== undefined && !Number.isNaN(Number(v))) { idx = i; break; }
                                    }
                                    lastIndexBySeries[s.name] = idx;
                                });

                                return compareSeries.map((s, seriesIdx) => {
                                    // vertical offset to reduce label overlap (stagger by index)
                                    const stagger = (seriesIdx - ((compareSeries.length - 1) / 2)) * 14;
                                    const labelRenderer = (props) => {
                                        const { x, y, index } = props || {};
                                        if (index !== lastIndexBySeries[s.name]) return null;
                                        if (x == null || y == null) return null;
                                        const tx = x + 8;
                                        const ty = y + stagger;
                                        // render a white stroke underlay for readability, then colored text
                                        return (
                                            <g pointerEvents="none">
                                                <text x={tx} y={ty} fontSize={12} fontWeight={700} textAnchor="start" stroke="#ffffff" strokeWidth={3} paintOrder="stroke">{s.name}</text>
                                                <text x={tx} y={ty} fontSize={12} fontWeight={700} textAnchor="start" fill={s.color}>{s.name}</text>
                                            </g>
                                        );
                                    };

                                    return (
                                        <Line
                                            key={s.name}
                                            name={s.name}
                                            type="monotone"
                                            dataKey={s.name}
                                            stroke={s.color}
                                            strokeWidth={2}
                                            dot={{ r: 3 }}
                                            label={labelRenderer}
                                            isAnimationActive={true}
                                        />
                                    );
                                });
                            })()
                        ) : (
                            <Line
                                name="Sentiment"
                                type="monotone"
                                dataKey="sentiment"
                                stroke="#57AAC8"
                                strokeWidth={2}
                                dot={(props) => {
                                    const { cx, cy, payload } = props;
                                    // don't draw a dot for gap points (sentiment null)
                                    if(!payload || payload.sentiment === null || payload.sentiment === undefined || Number.isNaN(Number(payload.sentiment))){
                                        return null
                                    }
                                    if(payload.isForecast){
                                        return <circle key={`dot-${props.index}`} cx={cx} cy={cy} r={5} fill="#ff4d4f" stroke="#ff4d4f" />
                                    }
                                    return <circle key={`dot-${props.index}`} cx={cx} cy={cy} r={4} fill="#57AAC8" stroke="#57AAC8" />
                                }}
                                label={(props) => {
                                    // place single-series label at last non-null point
                                    const lastIdx = (() => {
                                        for (let i = sentimentData.length - 1; i >= 0; i--) {
                                            const v = sentimentData[i] && sentimentData[i].sentiment;
                                            if (v !== null && v !== undefined && !Number.isNaN(Number(v))) return i;
                                        }
                                        return -1;
                                    })();
                                    const { index, x, y } = props || {};
                                    if (index !== lastIdx || x == null || y == null) return null;
                                    const tx = x + 8;
                                    const ty = y;
                                    return (
                                        <g pointerEvents="none">
                                            <text x={tx} y={ty} fontSize={12} fontWeight={700} textAnchor="start" stroke="#ffffff" strokeWidth={3} paintOrder="stroke">Sentiment</text>
                                            <text x={tx} y={ty} fontSize={12} fontWeight={700} textAnchor="start" fill="#57AAC8">Sentiment</text>
                                        </g>
                                    );
                                }}
                            />
                        )
                    }
                </LineChart>
            </ResponsiveContainer>
        </div>
    )
}

export default Chart