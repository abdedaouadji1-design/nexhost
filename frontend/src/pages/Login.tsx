import { useState } from 'react'
import { motion } from 'framer-motion'
import { Terminal, Lock, User, Sparkles, Cpu, Zap } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { authApi } from '../utils/api'
import { useAuthStore } from '../store/authStore'

const Login = () => {
  const navigate = useNavigate()
  const { setAuth } = useAuthStore()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!username || !password) {
      toast.error('يرجى إدخال اسم المستخدم وكلمة المرور')
      return
    }
    
    setIsLoading(true)
    
    try {
      const response = await authApi.login(username, password)
      const { access_token, refresh_token, user } = response.data
      
      setAuth(user, access_token)
      toast.success(`مرحباً ${user.username}!`)
      navigate('/dashboard')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'فشل تسجيل الدخول')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden">
      {/* Animated Background */}
      <div className="absolute inset-0">
        {/* Grid Lines */}
        <div 
          className="absolute inset-0 opacity-20"
          style={{
            backgroundImage: `
              linear-gradient(rgba(0, 255, 136, 0.1) 1px, transparent 1px),
              linear-gradient(90deg, rgba(0, 255, 136, 0.1) 1px, transparent 1px)
            `,
            backgroundSize: '50px 50px',
          }}
        />
        
        {/* Floating Orbs */}
        {[...Array(5)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute rounded-full blur-3xl"
            style={{
              width: 200 + i * 50,
              height: 200 + i * 50,
              background: i % 2 === 0 
                ? 'radial-gradient(circle, rgba(0, 255, 136, 0.15) 0%, transparent 70%)'
                : 'radial-gradient(circle, rgba(0, 216, 255, 0.15) 0%, transparent 70%)',
              left: `${10 + i * 20}%`,
              top: `${20 + i * 15}%`,
            }}
            animate={{
              x: [0, 50, 0],
              y: [0, -30, 0],
              scale: [1, 1.2, 1],
            }}
            transition={{
              duration: 8 + i * 2,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
          />
        ))}
      </div>

      {/* Login Card */}
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="relative z-10 w-full max-w-md mx-4"
      >
        {/* Logo */}
        <motion.div 
          className="text-center mb-8"
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.2, duration: 0.5 }}
        >
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-gradient-to-br from-neon-cyan to-neon-green mb-4 shadow-neon-cyan relative overflow-hidden">
            <motion.div
              className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent"
              animate={{ x: ['-100%', '100%'] }}
              transition={{ duration: 2, repeat: Infinity, repeatDelay: 3 }}
            />
            <Terminal className="w-10 h-10 text-cyber-bg" />
          </div>
          <h1 className="text-4xl font-bold font-mono mb-2">
            <span className="text-neon-cyan">Nex</span>
            <span className="text-neon-green">Host</span>
          </h1>
          <p className="text-text-secondary text-sm">V6.0 - لوحة التحكم المتقدمة</p>
        </motion.div>

        {/* Card */}
        <motion.div
          className="cyber-card p-8"
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.3, duration: 0.5 }}
        >
          {/* Decorative Corner */}
          <div className="absolute top-0 right-0 w-20 h-20 overflow-hidden">
            <div className="absolute top-3 right-3 w-16 h-16 border-t-2 border-r-2 border-neon-cyan/30 rounded-tr-xl" />
          </div>
          <div className="absolute bottom-0 left-0 w-20 h-20 overflow-hidden">
            <div className="absolute bottom-3 left-3 w-16 h-16 border-b-2 border-l-2 border-neon-green/30 rounded-bl-xl" />
          </div>

          <h2 className="text-xl font-bold text-center mb-6 flex items-center justify-center gap-2">
            <Lock className="w-5 h-5 text-neon-cyan" />
            تسجيل الدخول
          </h2>

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Username */}
            <div className="space-y-2">
              <label className="text-sm text-text-secondary flex items-center gap-2">
                <User className="w-4 h-4" />
                اسم المستخدم
              </label>
              <div className="relative">
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="cyber-input pr-10"
                  placeholder="أدخل اسم المستخدم"
                  disabled={isLoading}
                />
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted" />
              </div>
            </div>

            {/* Password */}
            <div className="space-y-2">
              <label className="text-sm text-text-secondary flex items-center gap-2">
                <Lock className="w-4 h-4" />
                كلمة المرور
              </label>
              <div className="relative">
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="cyber-input pr-10"
                  placeholder="أدخل كلمة المرور"
                  disabled={isLoading}
                />
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted" />
              </div>
            </div>

            {/* Submit Button */}
            <motion.button
              type="submit"
              disabled={isLoading}
              className="w-full neon-btn neon-btn-primary py-4 flex items-center justify-center gap-2 disabled:opacity-50"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              {isLoading ? (
                <div className="cyber-loader w-6 h-6" />
              ) : (
                <>
                  <Sparkles className="w-5 h-5" />
                  دخول النظام
                </>
              )}
            </motion.button>
          </form>

          {/* Features */}
          <div className="mt-8 pt-6 border-t border-cyber-border">
            <div className="grid grid-cols-3 gap-4 text-center">
              <div className="flex flex-col items-center gap-2">
                <div className="w-10 h-10 rounded-lg bg-neon-cyan/10 flex items-center justify-center">
                  <Cpu className="w-5 h-5 text-neon-cyan" />
                </div>
                <span className="text-xs text-text-muted">AI Powered</span>
              </div>
              <div className="flex flex-col items-center gap-2">
                <div className="w-10 h-10 rounded-lg bg-neon-green/10 flex items-center justify-center">
                  <Zap className="w-5 h-5 text-neon-green" />
                </div>
                <span className="text-xs text-text-muted">Fast</span>
              </div>
              <div className="flex flex-col items-center gap-2">
                <div className="w-10 h-10 rounded-lg bg-neon-purple/10 flex items-center justify-center">
                  <Terminal className="w-5 h-5 text-neon-purple" />
                </div>
                <span className="text-xs text-text-muted">Secure</span>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Version */}
        <p className="text-center text-text-muted text-xs mt-6">
          NexHost V6.0 © 2024 - Powered by AI
        </p>
      </motion.div>
    </div>
  )
}

export default Login
