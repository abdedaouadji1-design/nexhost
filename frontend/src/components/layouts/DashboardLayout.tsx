import { Outlet, NavLink, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  LayoutDashboard,
  FolderOpen,
  Bot,
  Cpu,
  Users,
  Settings,
  LogOut,
  Terminal,
  Menu,
  X,
  Sparkles,
  ChevronLeft,
} from 'lucide-react'
import { useState } from 'react'
import { useAuthStore } from '../../store/authStore'

const DashboardLayout = () => {
  const { user, logout } = useAuthStore()
  const location = useLocation()
  const [isSidebarOpen, setIsSidebarOpen] = useState(true)
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)

  const navItems = [
    { path: '/dashboard', label: 'الرئيسية', icon: LayoutDashboard },
    { path: '/projects', label: 'المشاريع', icon: FolderOpen },
    { path: '/ready-bots', label: 'البوتات الجاهزة', icon: Bot },
    { path: '/my-bots', label: 'بوتاتي', icon: Cpu },
    { path: '/ai-generator', label: 'صانع البوتات', icon: Sparkles },
  ]

  const adminItems = [
    { path: '/users', label: 'المستخدمين', icon: Users },
  ]

  const handleLogout = () => {
    logout()
    window.location.href = '/login'
  }

  return (
    <div className="min-h-screen flex">
      {/* Sidebar - Desktop */}
      <motion.aside
        initial={{ x: 300, opacity: 0 }}
        animate={{ 
          x: isSidebarOpen ? 0 : 280,
          opacity: 1 
        }}
        transition={{ duration: 0.3 }}
        className={`fixed right-0 top-0 h-screen w-72 bg-cyber-surface/98 backdrop-blur-xl border-l border-cyber-border z-50 hidden lg:block`}
      >
        {/* Animated Border */}
        <div className="absolute left-0 top-0 w-px h-full overflow-hidden">
          <motion.div
            className="w-full h-32 bg-gradient-to-b from-transparent via-neon-cyan to-transparent"
            animate={{ y: ['-100%', '400%'] }}
            transition={{ duration: 4, repeat: Infinity, ease: 'linear' }}
          />
        </div>

        {/* Logo */}
        <div className="p-6 border-b border-cyber-border">
          <NavLink to="/dashboard" className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-neon-cyan to-neon-green flex items-center justify-center shadow-neon-cyan">
              <Terminal className="w-5 h-5 text-cyber-bg" />
            </div>
            <div>
              <h1 className="font-mono font-bold text-lg">
                <span className="text-neon-cyan">Nex</span>
                <span className="text-neon-green">Host</span>
              </h1>
              <p className="text-xs text-text-muted">V6.0</p>
            </div>
          </NavLink>
        </div>

        {/* Navigation */}
        <nav className="p-4 space-y-1 overflow-y-auto h-[calc(100vh-200px)]">
          {/* Main Items */}
          <div className="mb-4">
            <p className="text-xs text-text-muted px-3 mb-2 font-mono uppercase tracking-wider">
              القائمة الرئيسية
            </p>
            {navItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) => `
                  flex items-center gap-3 px-3 py-3 rounded-lg transition-all duration-200
                  ${isActive 
                    ? 'bg-neon-cyan/10 text-neon-cyan border-r-2 border-neon-cyan' 
                    : 'text-text-secondary hover:text-text-primary hover:bg-cyber-surface2'
                  }
                `}
              >
                <item.icon className="w-5 h-5" />
                <span className="text-sm font-medium">{item.label}</span>
                {location.pathname === item.path && (
                  <motion.div
                    layoutId="activeIndicator"
                    className="mr-auto w-1.5 h-1.5 rounded-full bg-neon-cyan"
                  />
                )}
              </NavLink>
            ))}
          </div>

          {/* Admin Items */}
          {user?.role === 'admin' || user?.role === 'superadmin' ? (
            <div className="mb-4">
              <p className="text-xs text-text-muted px-3 mb-2 font-mono uppercase tracking-wider">
                الإدارة
              </p>
              {adminItems.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) => `
                    flex items-center gap-3 px-3 py-3 rounded-lg transition-all duration-200
                    ${isActive 
                      ? 'bg-neon-purple/10 text-neon-purple border-r-2 border-neon-purple' 
                      : 'text-text-secondary hover:text-text-primary hover:bg-cyber-surface2'
                    }
                  `}
                >
                  <item.icon className="w-5 h-5" />
                  <span className="text-sm font-medium">{item.label}</span>
                </NavLink>
              ))}
            </div>
          ) : null}

          {/* Settings */}
          <div>
            <p className="text-xs text-text-muted px-3 mb-2 font-mono uppercase tracking-wider">
              النظام
            </p>
            <NavLink
              to="/settings"
              className={({ isActive }) => `
                flex items-center gap-3 px-3 py-3 rounded-lg transition-all duration-200
                ${isActive 
                  ? 'bg-neon-green/10 text-neon-green border-r-2 border-neon-green' 
                  : 'text-text-secondary hover:text-text-primary hover:bg-cyber-surface2'
                }
              `}
            >
              <Settings className="w-5 h-5" />
              <span className="text-sm font-medium">الإعدادات</span>
            </NavLink>
          </div>
        </nav>

        {/* User & Logout */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-cyber-border bg-cyber-surface/98">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-neon-cyan to-neon-purple flex items-center justify-center text-cyber-bg font-bold">
                {user?.username?.[0]?.toUpperCase()}
              </div>
              <div>
                <p className="text-sm font-medium">{user?.username}</p>
                <p className="text-xs text-text-muted">{user?.role}</p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="p-2 rounded-lg text-neon-red hover:bg-neon-red/10 transition-colors"
              title="تسجيل الخروج"
            >
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </div>
      </motion.aside>

      {/* Mobile Sidebar */}
      <AnimatePresence>
        {isMobileMenuOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/50 z-40 lg:hidden"
              onClick={() => setIsMobileMenuOpen(false)}
            />
            <motion.aside
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ type: 'spring', damping: 25 }}
              className="fixed right-0 top-0 h-screen w-72 bg-cyber-surface z-50 lg:hidden"
            >
              {/* Mobile menu content - similar to desktop */}
              <div className="p-4 border-b border-cyber-border flex items-center justify-between">
                <h1 className="font-mono font-bold text-lg">
                  <span className="text-neon-cyan">Nex</span>
                  <span className="text-neon-green">Host</span>
                </h1>
                <button 
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="p-2 rounded-lg hover:bg-cyber-surface2"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              {/* ... same nav items ... */}
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      {/* Main Content */}
      <main className={`flex-1 transition-all duration-300 ${isSidebarOpen ? 'lg:mr-72' : 'mr-0'}`}>
        {/* Top Bar */}
        <header className="sticky top-0 z-30 bg-cyber-bg/80 backdrop-blur-lg border-b border-cyber-border">
          <div className="flex items-center justify-between px-6 py-4">
            <div className="flex items-center gap-4">
              {/* Toggle Sidebar */}
              <button
                onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                className="hidden lg:flex p-2 rounded-lg hover:bg-cyber-surface2 transition-colors"
              >
                <ChevronLeft className={`w-5 h-5 transition-transform ${!isSidebarOpen && 'rotate-180'}`} />
              </button>
              
              {/* Mobile Menu Button */}
              <button
                onClick={() => setIsMobileMenuOpen(true)}
                className="lg:hidden p-2 rounded-lg hover:bg-cyber-surface2"
              >
                <Menu className="w-5 h-5" />
              </button>

              {/* Breadcrumb */}
              <nav className="hidden md:flex items-center gap-2 text-sm text-text-muted">
                <span>الرئيسية</span>
                <ChevronLeft className="w-4 h-4" />
                <span className="text-text-primary">
                  {navItems.find(i => i.path === location.pathname)?.label || 
                   adminItems.find(i => i.path === location.pathname)?.label ||
                   'الإعدادات'}
                </span>
              </nav>
            </div>

            {/* Right Side */}
            <div className="flex items-center gap-4">
              {/* AI Status */}
              <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full bg-neon-green/10 border border-neon-green/30">
                <div className="w-2 h-2 rounded-full bg-neon-green animate-pulse" />
                <span className="text-xs text-neon-green font-mono">AI Online</span>
              </div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <div className="p-6">
          <Outlet />
        </div>
      </main>
    </div>
  )
}

export default DashboardLayout
