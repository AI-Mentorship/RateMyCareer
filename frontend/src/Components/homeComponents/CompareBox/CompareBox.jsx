import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import './CompareBox.css'
import Select from 'react-select'

function CompareBox() {
    const navigate = useNavigate()
    const [first, setFirst] = useState(null)
    const [second, setSecond] = useState(null)

    const options = [
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

    const customStyles = {
        placeholder: (provided) => ({
            ...provided,
            fontFamily: "'Item', sans-serif",    
            textAlign: "left",
        }),
        control: (provided) => ({
            ...provided,
            borderRadius: "30px",
            backgroundColor: "white",
            width: "400px",
            fontSize: "15px",
            boxShadow: "0 10px 30px rgba(0, 0, 0, 0.2)",
            textAlign: "left",
            fontFamily: "Arial, Helvetica, sans-serif;", 
            cursor: "pointer",
        }),
        valueContainer: (provided) => ({
            ...provided,
            paddingLeft: '20px',
        }),
        indicatorSeparator: () => ({ display: 'none' }),
        dropdownIndicator: () => ({ display: 'none' }),
        menu: (provided) => ({
            ...provided,
            width: '400px',
            fontFamily: "Arial, Helvetica, sans-serif;",
            fontSize: "15px",
            textAlign: "left",
        }),
    };

    return (
        <div className="compare-container">
            <div className="compare-main">
                <h2>Compare</h2>
                <p>"Wanna know detailed comparisons between 2 Professions."</p>
                <div className="comparison">
                    <h4 className="first-prof">FIRST PROFESSION</h4>
                    <Select
                        className="select-box1"
                        options={options}
                        styles={customStyles}
                        placeholder="Select a profession..."
                        value={first}
                        onChange={setFirst}
                        isClearable
                    />
                    <h4 className="second-prof">SECOND PROFESSION</h4>
                    <Select
                        className="select-box2"
                        options={options}
                        styles={customStyles}
                        placeholder="Select a profession..."
                        value={second}
                        onChange={setSecond}
                        isClearable
                    />
                </div>
                <button className="compare" onClick={() => {
                    // require at least one selected profession
                    if(!first && !second) return
                    const payload = { compare: [first ? { value: first.value, label: first.label } : null, second ? { value: second.value, label: second.label } : null].filter(Boolean) }
                    navigate('/compare', { state: payload })
                }}>GO!!</button>
            </div>
        </div>
    )
}

export default CompareBox