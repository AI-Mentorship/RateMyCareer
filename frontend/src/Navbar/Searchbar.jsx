
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import Select from "react-select";
import "./Navbar.css";

function Searchbar(props) {
    const navigate = useNavigate();
    const [selectedOption, setSelectedOption] = useState(null);

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

    const handleSearch = () => {
        if (selectedOption) {
        navigate(`/profession`, { state: { careerValue: selectedOption.value, careerLabel: selectedOption.label } });
        }
    };

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
            height: '30px',
            cursor: 'pointer',
            textAlign: "left",
        }),
        valueContainer: (provided) => ({
            ...provided,
        }),
        indicatorSeparator: () => ({ display: 'none' }),
        dropdownIndicator: () => ({ display: 'none' }),
        menu: (provided) => ({
            ...provided,
            fontFamily: "Arial, Helvetica, sans-serif",
            width: '450px',
            textAlign: "left",
        }),
    };

    return (
        <div className="search-container">
            
            <Select
                className="select-component"
                options={options}
                styles={customStyles}
                placeholder="Select a profession..."
                value={selectedOption}
                onChange={(opt) => setSelectedOption(opt)}
            />
            <button className="search-button" onClick={handleSearch}>SEARCH</button>
        </div>
    )
}

export default Searchbar