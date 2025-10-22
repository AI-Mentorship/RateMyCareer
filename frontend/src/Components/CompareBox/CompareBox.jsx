import './CompareBox.css'
import Select from 'react-select'
import job1 from '../../assets/job1.png'
import job2 from '../../assets/job2.png'
import job3 from '../../assets/job3.png'
import job4 from '../../assets/job4.png'
import job5 from '../../assets/job5.png'

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
            fontFamily: "'Itim', cursive",
        }),
        control: (provided) => ({
            ...provided,
            borderRadius: "30px",
            backgroundColor: "#D9D9D9",
            fontFamily: "'Itim', cursive",
            width: "195px",
            fontSize: "13px",
        }),
        valueContainer: (provided) => ({
            ...provided,
            paddingLeft: '20px',
        }),
        indicatorSeparator: () => ({ display: 'none' }),
        dropdownIndicator: () => ({ display: 'none' }),
        menu: (provided) => ({
            ...provided,
            width: '195px',
            fontFamily: "'Itim', cursive",
            fontSize: "13px",
        }),
    };

    return (
        <div className="compare-container">
            <div className="frame">
                <img className="job1" src={job1}></img>
                <img className="job2" src={job2}></img>
                <img className="job3" src={job3}></img>
                <img className="job4" src={job4}></img>
                <img className="job5" src={job5}></img>
            </div>
            <div className="compare-main">
                <h2>Compare</h2>
                <p>Wanna know detailed comparisons between 2 Professions</p>
                <div className="comparison">
                    <Select
                        className="select-box1"
                        options={options}
                        styles={customStyles}
                        placeholder="Select a profession..."
                    />
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