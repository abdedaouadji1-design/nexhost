import { motion } from 'framer-motion'
import {
  Settings,
  User,
  Lock,
  Bell,
  Shield,
  Save,
} from 'lucide-react'

const SettingsPage = () => {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold mb-2">الإعدادات</h1>
        <p className="text-text-muted">تخصيص إعدادات حسابك والنظام</p>
      </div>

      {/* Settings Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Profile Settings */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="cyber-card p-6"
        >
          <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
            <User className="w-5 h-5 text-neon-cyan" />
            الملف الشخصي
          </h2>
          <div className="space-y-4">
            <div>
              <label className="text-sm text-text-secondary mb-2 block">
                اسم المستخدم
              </label>
              <input type="text" className="cyber-input" disabled />
            </div>
            <div>
              <label className="text-sm text-text-secondary mb-2 block">
                البريد الإلكتروني
              </label>
              <input type="email" className="cyber-input" disabled />
            </div>
          </div>
        </motion.div>

        {/* Security Settings */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="cyber-card p-6"
        >
          <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
            <Lock className="w-5 h-5 text-neon-green" />
            الأمان
          </h2>
          <div className="space-y-4">
            <div>
              <label className="text-sm text-text-secondary mb-2 block">
                كلمة المرور الحالية
              </label>
              <input type="password" className="cyber-input" />
            </div>
            <div>
              <label className="text-sm text-text-secondary mb-2 block">
                كلمة المرور الجديدة
              </label>
              <input type="password" className="cyber-input" />
            </div>
            <motion.button
              className="w-full neon-btn neon-btn-primary"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <Save className="w-4 h-4 inline ml-2" />
              حفظ التغييرات
            </motion.button>
          </div>
        </motion.div>

        {/* Notifications */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="cyber-card p-6"
        >
          <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
            <Bell className="w-5 h-5 text-neon-purple" />
            الإشعارات
          </h2>
          <div className="space-y-3">
            {[
              'إشعارات البريد الإلكتروني',
              'إشعارات المتصفح',
              'تنبيهات الأمان',
              'تحديثات النظام',
            ].map((item) => (
              <label key={item} className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  className="w-4 h-4 rounded border-cyber-border bg-cyber-surface2 text-neon-cyan"
                />
                <span className="text-sm">{item}</span>
              </label>
            ))}
          </div>
        </motion.div>
      </div>

      {/* System Info */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="cyber-card p-6"
      >
        <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
          <Shield className="w-5 h-5 text-neon-yellow" />
          معلومات النظام
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-4 rounded-lg bg-cyber-surface2">
            <p className="text-sm text-text-muted mb-1">الإصدار</p>
            <p className="font-mono font-bold">6.0.0</p>
          </div>
          <div className="p-4 rounded-lg bg-cyber-surface2">
            <p className="text-sm text-text-muted mb-1">Backend</p>
            <p className="font-mono font-bold">FastAPI</p>
          </div>
          <div className="p-4 rounded-lg bg-cyber-surface2">
            <p className="text-sm text-text-muted mb-1">Database</p>
            <p className="font-mono font-bold">PostgreSQL</p>
          </div>
          <div className="p-4 rounded-lg bg-cyber-surface2">
            <p className="text-sm text-text-muted mb-1">AI Providers</p>
            <p className="font-mono font-bold text-neon-green">3 Active</p>
          </div>
        </div>
      </motion.div>
    </div>
  )
}

export default SettingsPage
