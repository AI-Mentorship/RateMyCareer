import React, { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import Select from 'react-select';
import './ComparisonPage.css';
import comparisonBg from './assets/images/ComparisonPicture.png';
import Navbar from './Navbar/Navbar.jsx';

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

  // State to manage professions being compared
  const [professions, setProfessions] = useState([
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
  ]);

  const [selectedProfession, setSelectedProfession] = useState(null);

  // Mock sentiment trend data for the graph
  const generateSentimentData = () => {
    const data = [];
    for (let i = 1; i <= 8; i++) {
      const weekData = { week: `Week ${i}` };
      professions.forEach(prof => {
        weekData[prof.name] = prof.sentiment + Math.floor(Math.random() * 10 - 5);
      });
      data.push(weekData);
    }
    return data;
  };

  const sentimentData = generateSentimentData();

  const getAvailableOptions = () => {
    const comparedNames = professions.map(p => p.name);
    return availableProfessions
      .filter(name => !comparedNames.includes(name))
      .map(name => ({ value: name, label: name }));
  };

  // Function to add a new profession
  const handleAddProfession = (selectedOption) => {
    if (!selectedOption) return;

    const colors = ["#FFD93D", "#6BCF7F", "#A78BFA", "#FB923C", "#F472B6"];
    
    // Generate random metrics for the new profession (for now because this is hardcoded)
    const newProfession = {
      id: professions.length + 1,
      name: selectedOption.value,
      vibeScore: Math.floor(Math.random() * 40 + 40),
      sentiment: Math.floor(Math.random() * 40 + 40),
      regret: Math.floor(Math.random() * 60 + 20),
      volatility: Math.floor(Math.random() * 50 + 25),
      color: colors[(professions.length - 2) % colors.length]
    };
    
    setProfessions([...professions, newProfession]);
    setSelectedProfession(null);
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
    option: (provided, state) => ({
      ...provided,
      fontFamily: "'Itim', cursive",
      fontSize: '14px',
      backgroundColor: state.isSelected ? '#667eea' : state.isFocused ? '#f0f0f0' : 'white',
      color: state.isSelected ? 'white' : '#333',
    }),
  };

 return(

    <div className="comparison-page">
      {/* Diagonal split background with blue and yellow */}
      <div className="comparison-background">
        <div className="nav-background"></div>
        <div className="blue-half" style={{ backgroundImage: `url(${comparisonBg})` }}></div>
        <div className="yellow-half"></div>
        <div className="gray-half"></div>
      </div>
    

      <div className="comparison-main-container">

      
        <Navbar></Navbar>
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
            />
          </div>
        </div>

        {/* Sentiment trend graph with multiple professions */}
        <div className="sentiment-graph-section">
          <h2 className="graph-title">Sentiment Trend</h2>
          <ResponsiveContainer width="100%" height="90%">
            <LineChart data={sentimentData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
              <XAxis 
                dataKey="week" 
                tick={{ fill: '#666', fontSize: 12 }}
                stroke="#999"
              />
              <YAxis 
                tick={{ fill: '#666', fontSize: 12 }}
                stroke="#999"
                domain={[0, 100]}
              />
              <Tooltip />
              <Legend />
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
  );
}

export default ComparisonPage;