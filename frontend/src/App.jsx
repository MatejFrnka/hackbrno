import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import PatientSelection from './pages/PatientSelection';
import PatientInformation from './pages/PatientInformation';

function App() {
    return (
        <Router>
            <Routes>
                <Route path="/" element={<PatientSelection />} />
                <Route path="/patient/:id" element={<PatientInformation />} />
            </Routes>
        </Router>
    );
}

export default App;

