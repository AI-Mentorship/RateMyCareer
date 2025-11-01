import './Chart.css'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

function Chart() {
    const sentimentData = [
        { week: 'Week 1', sentiment: 0.2 },
        { week: 'Week 2', sentiment: 0.4 },
        { week: 'Week 3', sentiment: 0.3 },
        { week: 'Week 4', sentiment: 0.5 },
        { week: 'Week 5', sentiment: 0.6 },
        { week: 'Week 6', sentiment: 0.7 },
        { week: 'Week 7', sentiment: 0.65 },
        { week: 'Week 8', sentiment: 0.8 },
    ];
    return (
        <div className="graph">
            <h1>sentiment trend</h1>
            <ResponsiveContainer width="85%" height={250}>
                <LineChart data={sentimentData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="week" />
                    <YAxis domain={[-1, 1]} />
                    <Tooltip />
                    <Line
                        type="monotone"
                        dataKey="sentiment"
                        stroke="#57AAC8"
                        strokeWidth={2}
                        dot={{ r: 4 }}
                    />
                </LineChart>
            </ResponsiveContainer>
        </div>
    )
}

export default Chart