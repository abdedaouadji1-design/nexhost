import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { Home, AlertTriangle } from 'lucide-react'

const NotFound = () => {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="text-center"
      >
        <div className="w-24 h-24 rounded-full bg-neon-red/10 flex items-center justify-center mx-auto mb-6">
          <AlertTriangle className="w-12 h-12 text-neon-red" />
        </div>
        <h1 className="text-6xl font-bold font-mono mb-4">
          <span className="text-neon-red">404</span>
        </h1>
        <p className="text-xl text-text-muted mb-8">الصفحة غير موجودة</p>
        <Link
          to="/dashboard"
          className="neon-btn neon-btn-primary inline-flex items-center gap-2"
        >
          <Home className="w-4 h-4" />
          العودة للرئيسية
        </Link>
      </motion.div>
    </div>
  )
}

export default NotFound
