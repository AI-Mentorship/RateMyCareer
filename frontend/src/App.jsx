import { BrowserRouter, Routes, Route } from "react-router-dom";
import Homepage from './Pages/Homepage/Homepage.jsx';
import Profession from './Pages/Profession/Profession.jsx';
import './App.css';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Homepage />} />
        <Route path="/profession" element={<Profession />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;