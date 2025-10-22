import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useNavigate } from 'react-router-dom'; 
import './ProfessionPage.css';

function ProfessionPage() {

  // Search bar stuff **

  const [searchQuery, setSearchQuery] = useState('');
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const navigate = useNavigate();
  
  // List of available professions
  const professions = [
    'Data Analyst',
    'Data Scientist',
    'HR / Management',
    'Physical Therapist',
    'Teacher',
    'Lawyer',
    'Police',
    'UX Designer',
    'Software Engineer',
    'Nurse',
    'Accountant',
  ];
  
  // This is to filter professions based on search query
  const filteredProfessions = professions.filter(profession =>
    profession.toLowerCase().includes(searchQuery.toLowerCase())
  );
  
  // Show selection of the professions we have
  const handleSelectProfession = (profession) => {
    const professionSlug = profession.toLowerCase().replace(/\s+/g, '-').replace(/\//g, '-');
    navigate(`/profession/${professionSlug}`);
    setSearchQuery('');
    setIsDropdownOpen(false);
  };

  // Close dropdown when clicking outside
  useEffect(() => {
  const handleClickOutside = (event) => {
    if (!event.target.closest('.hero-search-container')) {
      setIsDropdownOpen(false);
    }
  };
  
  document.addEventListener('mousedown', handleClickOutside);
  return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // 1. Hard coded data for now
  // 2.  Will later replace with API call to fetch real data


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

  const redditPosts = [
    { text: "Blah blah blah blah", author: "u/user1" },
    { text: "Blah blah blah blah blah", author: "u/user2" },
    { text: "Blah blah blah blah blah blah", author: "u/user3" },
    { text: "Blah blah blah blah blah blah blah", author: "u/user4" }
  ];

  
  return (
    <div className="profession-page">
      
      <div className="hero-section">
        <div className="hero-content">
          <div className="hero-left">
            <h1 className="profession-title">Data Analyst</h1>
            <div className="hero-vibe-circle">
              <div className="score-display">
                <span className="score-number">72</span>
                <span className="score-total">/100</span>
              </div>
            </div>
          </div>
    
    { /* Search bar dropdown */ }
    <div className="hero-search-container">
      <div className="search-wrapper">
        <input
          type="text"
          className="search-input"
          placeholder="Select a profession..."
          value={searchQuery}
          onChange={(e) => {
            setSearchQuery(e.target.value);
            setIsDropdownOpen(true);
          }}
          onFocus={() => setIsDropdownOpen(true)}
        />
        <button className="search-button">SEARCH</button>
      </div>
      
      {/* Dropdown menu part (to show professions) */}
      {isDropdownOpen && (
        <div className="dropdown-menu">
          {filteredProfessions.length > 0 ? (
            filteredProfessions.map((profession, index) => (
              <div
                key={index}
                className="dropdown-item"
                onClick={() => handleSelectProfession(profession)}
              >
                {profession}
              </div>
            ))
          ) : (
            <div className="dropdown-item no-results">No professions found</div>
          )}
        </div>
      )}
    </div>
  </div>
</div> 

<div className="content-container">
  
  <div className="left-column">


          <section className="breakdown-section">
            <h2>Breakdown of Vibe Score</h2>
            <div className="metrics-grid">
              
              <div className="metric-card">
                <h3>Sentiment</h3>
                <p className="metric-value">80</p>
              </div>
              
              <div className="metric-card">
                <h3>Regret</h3>
                <p className="metric-value">34</p>
              </div>
              
              <div className="metric-card">
                <h3>Volatility</h3>
                <p className="metric-value">70</p>
              </div>
              
            </div>
          </section>


          <section className="sentiment-trend-section">
            <h2>Sentiment Trend</h2>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={sentimentData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="week" />
                <YAxis domain={[-1, 1]} />
                <Tooltip />
                <Line 
                  type="monotone" 
                  dataKey="sentiment" 
                  stroke="#8884d8" 
                  strokeWidth={2}
                  dot={{ r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
            <p className="forecast-label">Forecast →</p>
          </section>

        </div>

        <div className="right-column">
          
          <section className="ai-summary-section">
            <h2>Overview</h2>
            <p className="ai-summary-text">
              Data Analysts enjoy a stable career with positive growth in demand. 
              However, there are occasional mentions of job stress and limited 
              advancement opportunities. The work often involves problem-solving 
              and can be intellectually rewarding.
            </p>
          </section>

          <section className="reddit-posts-section">
            <h2>Quoted Reddit Posts</h2>
            <div className="posts-container">
              {redditPosts.map((post, index) => (
                <div key={index} className="reddit-post-card">
                  <p className="post-text">"{post.text}"</p>
                  <p className="post-author">— {post.author}</p>
                </div>
              ))}
            </div>
          </section>

        </div>
      </div>
    </div>
  );
}

export default ProfessionPage;