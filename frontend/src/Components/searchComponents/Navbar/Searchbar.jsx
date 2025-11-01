
import React, { useState } from 'react';
import './Navbar.css'
import Select from "react-select"

function Searchbar(props) {
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
            fontFamily: "Arial, Helvetica, sans-serif",
        }),
        control: (provided) => ({
            ...provided,
            border: 'none',
            boxShadow: 'none',
            backgroundColor: 'transparent',
            fontFamily: "Arial, Helvetica, sans-serif",
            width: '500px',
        }),
        valueContainer: (provided) => ({
            ...provided,
        }),
        indicatorSeparator: () => ({ display: 'none' }),
        dropdownIndicator: () => ({ display: 'none' }),
        menu: (provided) => ({
            ...provided,
            minWidth: '100%',
            fontFamily: "Arial, Helvetica, sans-serif",
            width: '580px',
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