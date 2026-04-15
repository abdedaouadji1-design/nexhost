import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/authStore'

// Layouts
import DashboardLayout from './components/layouts/DashboardLayout'
import AuthLayout from './components/layouts/AuthLayout'

// Pages
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Projects from './pages/Projects'
import ReadyBots from './pages/ReadyBots'
import MyBots from './pages/MyBots'
import AIBotGenerator from './pages/AIBotGenerator'
import Users from './pages/Users'
import Settings from './pages/Settings'
import NotFound from './pages/NotFound'

// Protected Route Component
const ProtectedRoute = ({ children, requireAdmin = false }: { 
  children: React.ReactNode
  requireAdmin?: boolean 
}) => {
  const { isAuthenticated, user } = useAuthStore()
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }
  
  if (requireAdmin && user?.role !== 'admin' && user?.role !== 'superadmin') {
    return <Navigate to="/dashboard" replace />
  }
  
  return <>{children}</>
}

function App() {
  return (
    <div className="min-h-screen bg-cyber-bg text-text-primary font-arabic">
      {/* Animated Background Particles */}
      <div className="particles-container">
        {Array.from({ length: 30 }).map((_, i) => (
          <div
            key={i}
            className="particle"
            style={{
              left: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 15}s`,
              animationDuration: `${15 + Math.random() * 10}s`,
              background: i % 3 === 0 ? '#00ff88' : i % 3 === 1 ? '#00d8ff' : '#7c3aed',
            }}
          />
        ))}
      </div>
      
      <Routes>
        {/* Auth Routes */}
        <Route element={<AuthLayout />}>
          <Route path="/login" element={<Login />} />
        </Route>
        
        {/* Protected Routes */}
        <Route element={
          <ProtectedRoute>
            <DashboardLayout />
          </ProtectedRoute>
        }>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/projects" element={<Projects />} />
          <Route path="/ready-bots" element={<ReadyBots />} />
          <Route path="/my-bots" element={<MyBots />} />
          <Route path="/ai-generator" element={<AIBotGenerator />} />
          <Route path="/settings" element={<Settings />} />
        </Route>
        
        {/* Admin Routes */}
        <Route element={
          <ProtectedRoute requireAdmin>
            <DashboardLayout />
          </ProtectedRoute>
        }>
          <Route path="/users" element={<Users />} />
        </Route>
        
        {/* Redirects */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        
        {/* 404 */}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </div>
  )
}

export default App
