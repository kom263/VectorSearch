import { Routes, Route, Navigate } from 'react-router-dom'
import Navbar from './components/Navbar'
import Dashboard from './pages/Dashboard'
import CandidateApply from './pages/CandidateApply'
import CandidateHistory from './pages/CandidateHistory'

function App() {
  return (
    <div className="app-container">
      <Navbar />
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Navigate to="/apply" replace />} />
          <Route path="/apply" element={<CandidateApply />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/candidate/:phone" element={<CandidateHistory />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
