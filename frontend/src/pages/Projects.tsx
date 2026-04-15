import { motion } from 'framer-motion'
import {
  FolderOpen,
  Plus,
  Play,
  Square,
  Settings,
  Trash2,
  FileCode,
  Terminal,
} from 'lucide-react'

const Projects = () => {
  const projects = [] // Will be populated from API

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold mb-2">المشاريع</h1>
          <p className="text-text-muted">إدارة مشاريعك البرمجية</p>
        </div>
        <motion.button
          className="neon-btn neon-btn-primary flex items-center gap-2"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <Plus className="w-4 h-4" />
          مشروع جديد
        </motion.button>
      </div>

      {/* Empty State */}
      {projects.length === 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="cyber-card p-12 text-center"
        >
          <div className="w-20 h-20 rounded-full bg-neon-cyan/10 flex items-center justify-center mx-auto mb-4">
            <FolderOpen className="w-10 h-10 text-neon-cyan" />
          </div>
          <h3 className="text-xl font-bold mb-2">لا توجد مشاريع</h3>
          <p className="text-text-muted mb-6">ابدأ بإنشاء مشروعك الأول</p>
          <motion.button
            className="neon-btn neon-btn-primary"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <Plus className="w-4 h-4 inline ml-2" />
            إنشاء مشروع
          </motion.button>
        </motion.div>
      )}
    </div>
  )
}

export default Projects
