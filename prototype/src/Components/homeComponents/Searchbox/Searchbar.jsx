import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import Select from "react-select";
import "./Searchbox.css";

function Searchbar() {
  const navigate = useNavigate();
  const [selectedOption, setSelectedOption] = useState(null);

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

  const handleSearch = () => {
            if (selectedOption) {
            // pass both the canonical value and the display label so the Profession page
            // can use the value for API calls and the label for UI display
            navigate(`/profession`, { state: { careerValue: selectedOption.value, careerLabel: selectedOption.label } });
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
            backgroundColor: 'rgba(255,255,255,0)',
            fontFamily: "Arial, Helvetica, sans-serif",
            width: '470px',
            cursor: 'pointer',
        }),
        valueContainer: (provided) => ({
            ...provided,
            paddingLeft: '20px', 
        }),
        indicatorSeparator: () => ({ display: 'none' }),
        dropdownIndicator: () => ({ display: 'none' }),
        menu: (provided) => ({
            ...provided,
            width: '530px',
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