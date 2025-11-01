import './Searchbox.css'
import React, { useState } from 'react';
import Select from "react-select"

function Searchbar() {
    const options = [
        { value: "dataScienetist", label: "Data Scientist" },
        { value: "management", label: "HR / Management" },
        { value: "physicalTherapist", label: "Physical Therapist" },
        { value: "teacher", label: "Teacher" },
        { value: "lawyer", label: "Lawyer" },
        { value: "police", label: "Police" },
        { value: "ux", label: "UX" },
        { value: "dataAnalyst", label: "Data Analyst" },
        { value: "graphicDesign", label: "Graphic Design" },
        { value: "csCareer", label: "CS Career" },
    ];

    const customStyles = {
        placeholder: (provided) => ({
            ...provided,
            fontFamily: "'Inter', sans-serif",
        }),
        control: (provided) => ({
            ...provided,
            border: 'none',
            boxShadow: 'none',
            backgroundColor: 'transparent',
            fontFamily: "Arial, Helvetica, sans-serif;",
        }),
        valueContainer: (provided) => ({
            ...provided,
            paddingLeft: '20px', 
        }),
        indicatorSeparator: () => ({ display: 'none' }),
        dropdownIndicator: () => ({ display: 'none' }),
        menu: (provided) => ({
            ...provided,
            width: '576px',
            fontFamily: "'Inter', sans-serif",
        }),
    };

    return (
        <div className="search-container">
            <Select
                className="select-component"
                options={options}
                styles={customStyles}
                placeholder="Select a profession..."
            />
            <button className="search-button">SEARCH</button>
        </div>
    )
}

export default Searchbar