import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { Box } from '@mui/material'

import { useAuth } from './contexts/AuthContext'
import Layout from './components/Layout/Layout'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import ScansPage from './pages/ScansPage'
import ScanDetailPage from './pages/ScanDetailPage'
import ReportsPage from './pages/ReportsPage'

import AgenticPage from './pages/AgenticPage'
import ValidationPage from './pages/ValidationPage'
import MonitorPage from './pages/MonitorPage'
import AIEmailNotificationPage from './pages/AIEmailNotificationPage'
import EmailManagementPage from './pages/EmailManagementPage'
import SettingsPage from './pages/SettingsPage'
import ComplianceFrameworksPage from './pages/ComplianceFrameworksPage'
import NotFoundPage from './pages/NotFoundPage'

// Protected route component
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="100vh"
      >
        Loading...
      </Box>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

const App: React.FC = () => {
  return (
    <Box sx={{ minHeight: '100vh', backgroundColor: 'background.default' }}>
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<LoginPage />} />
        
        {/* Protected routes */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="scans" element={<ScansPage />} />
          <Route path="scans/:scanId" element={<ScanDetailPage />} />
          <Route path="reports" element={<ReportsPage />} />
          <Route path="email-management" element={<EmailManagementPage />} />

          <Route path="agentic" element={<AgenticPage />} />
          <Route path="validation" element={<ValidationPage />} />
          <Route path="monitor" element={<MonitorPage />} />
          <Route path="ai-email" element={<AIEmailNotificationPage />} />
          <Route path="compliance" element={<ComplianceFrameworksPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>

        {/* 404 route */}
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </Box>
  )
}

export default App
