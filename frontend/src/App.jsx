import { BrowserRouter, Routes, Route } from "react-router-dom";
import Homepage from './Pages/Homepage/Homepage.jsx';
import Profession from './Pages/Profession/Profession.jsx';
import ComparisonPage from './Pages/Compare/ComparisonPage.jsx';
import './App.css';
import LoadingOverlay from './Components/LoadingOverlay/LoadingOverlay.jsx';

function App() {
  return (
    <BrowserRouter>
      <LoadingOverlay />
      <Routes>
        <Route path="/" element={<Homepage />} />
        <Route path="/profession" element={<Profession />} />
        <Route path="/compare" element={<ComparisonPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;