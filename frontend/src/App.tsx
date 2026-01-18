import { Routes, Route, Navigate } from 'react-router-dom'
import { Box } from '@mui/material'

import Layout from './components/common/Layout'
import Dashboard from './pages/Dashboard'
import SiteList from './pages/SiteList'
import SiteDetail from './pages/SiteDetail'
import VehicleTracking from './pages/VehicleTracking'
import Schedule from './pages/Schedule'
import Reports from './pages/Reports'
import Simulation from './pages/Simulation'
import Settings from './pages/Settings'

function App() {
  return (
    <Box sx={{ display: 'flex', height: '100vh' }}>
      <Layout>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/sites" element={<SiteList />} />
          <Route path="/sites/:id" element={<SiteDetail />} />
          <Route path="/vehicles" element={<VehicleTracking />} />
          <Route path="/schedule" element={<Schedule />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/simulation" element={<Simulation />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </Layout>
    </Box>
  )
}

export default App
