import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import Select from "react-select";
import "./Searchbox.css";

function Searchbar() {
  const navigate = useNavigate();
  const [selectedOption, setSelectedOption] = useState(null);

  const options = [
    { value: "dataScientist", label: "Data Scientist" },
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
      navigate(`/profession`);
    }
  };


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
                value={selectedOption}
                onChange={(opt) => setSelectedOption(opt)}
            />
            <button className="search-button" onClick={handleSearch}>SEARCH</button>
        </div>
    )
}

export default Searchbar