import './CompareBox.css'
import Select from 'react-select'

function CompareBox() {
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
            fontFamily: "Arial, Helvetica, sans-serif;",    
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
                    />
                    <h4 className="second-prof">SECOND PROFESSION</h4>
                    <Select
                        className="select-box2"
                        options={options}
                        styles={customStyles}
                        placeholder="Select a profession..."
                    />
                </div>
                <button className="compare">GO!!</button>
            </div>
        </div>
    )
}

export default CompareBox