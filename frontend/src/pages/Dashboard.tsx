import { motion } from 'framer-motion'
import {
  FolderOpen,
  Bot,
  Cpu,
  Activity,
  TrendingUp,
  Zap,
  Terminal,
  Clock,
} from 'lucide-react'
import { useAuthStore } from '../store/authStore'

const Dashboard = () => {
  const { user } = useAuthStore()

  const stats = [
    {
      title: 'المشاريع',
      value: '0',
      icon: FolderOpen,
      color: 'cyan',
      trend: '+0%',
    },
    {
      title: 'البوتات النشطة',
      value: '0',
      icon: Bot,
      color: 'green',
      trend: '+0%',
    },
    {
      title: 'استخدام CPU',
      value: '0%',
      icon: Cpu,
      color: 'purple',
      trend: 'مستقر',
    },
    {
      title: 'طلبات AI',
      value: '0',
      icon: Zap,
      color: 'yellow',
      trend: 'اليوم',
    },
  ]

  const recentActivity = [
    { action: 'تسجيل دخول', time: 'الآن', icon: Terminal },
  ]

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
      },
    },
  }

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.5 },
    },
  }

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* Welcome Section */}
      <motion.div variants={itemVariants} className="cyber-card p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold mb-2">
              مرحباً،{' '}
              <span className="text-neon-cyan">{user?.username}</span>
              <span className="text-neon-green">!</span>
            </h1>
            <p className="text-text-secondary">
              نظرة عامة على نظامك ونشاطاتك
            </p>
          </div>
          <div className="hidden md:flex items-center gap-2 px-4 py-2 rounded-full bg-neon-cyan/10 border border-neon-cyan/30">
            <Activity className="w-4 h-4 text-neon-cyan" />
            <span className="text-sm text-neon-cyan font-mono">النظام يعمل</span>
          </div>
        </div>
      </motion.div>

      {/* Stats Grid */}
      <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat, index) => (
          <motion.div
            key={stat.title}
            className="cyber-card p-5 group cursor-pointer"
            whileHover={{ scale: 1.02, y: -2 }}
            transition={{ duration: 0.2 }}
          >
            <div className="flex items-start justify-between mb-4">
              <div className={`w-12 h-12 rounded-xl bg-neon-${stat.color}/10 flex items-center justify-center group-hover:scale-110 transition-transform`}>
                <stat.icon className={`w-6 h-6 text-neon-${stat.color}`} />
              </div>
              <div className="flex items-center gap-1 text-xs text-neon-green">
                <TrendingUp className="w-3 h-3" />
                {stat.trend}
              </div>
            </div>
            <h3 className="text-2xl font-bold font-mono mb-1">{stat.value}</h3>
            <p className="text-sm text-text-muted">{stat.title}</p>
          </motion.div>
        ))}
      </motion.div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Quick Actions */}
        <motion.div variants={itemVariants} className="cyber-card p-6">
          <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
            <Zap className="w-5 h-5 text-neon-yellow" />
            إجراءات سريعة
          </h2>
          <div className="space-y-3">
            <motion.button
              className="w-full p-4 rounded-lg bg-cyber-surface2 border border-cyber-border hover:border-neon-cyan/50 transition-all group"
              whileHover={{ x: 4 }}
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-neon-cyan/10 flex items-center justify-center group-hover:bg-neon-cyan/20 transition-colors">
                  <Bot className="w-5 h-5 text-neon-cyan" />
                </div>
                <div className="text-right">
                  <p className="font-medium">إنشاء بوت جديد</p>
                  <p className="text-xs text-text-muted">استخدم صانع البوتات بالذكاء الاصطناعي</p>
                </div>
              </div>
            </motion.button>

            <motion.button
              className="w-full p-4 rounded-lg bg-cyber-surface2 border border-cyber-border hover:border-neon-green/50 transition-all group"
              whileHover={{ x: 4 }}
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-neon-green/10 flex items-center justify-center group-hover:bg-neon-green/20 transition-colors">
                  <FolderOpen className="w-5 h-5 text-neon-green" />
                </div>
                <div className="text-right">
                  <p className="font-medium">مشروع جديد</p>
                  <p className="text-xs text-text-muted">ابدأ مشروع Python أو PHP جديد</p>
                </div>
              </div>
            </motion.button>

            <motion.button
              className="w-full p-4 rounded-lg bg-cyber-surface2 border border-cyber-border hover:border-neon-purple/50 transition-all group"
              whileHover={{ x: 4 }}
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-neon-purple/10 flex items-center justify-center group-hover:bg-neon-purple/20 transition-colors">
                  <Terminal className="w-5 h-5 text-neon-purple" />
                </div>
                <div className="text-right">
                  <p className="font-medium">فتح Terminal</p>
                  <p className="text-xs text-text-muted">وصول مباشر للسطر الأوامر</p>
                </div>
              </div>
            </motion.button>
          </div>
        </motion.div>

        {/* Recent Activity */}
        <motion.div variants={itemVariants} className="cyber-card p-6">
          <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
            <Clock className="w-5 h-5 text-neon-cyan" />
            النشاط الأخير
          </h2>
          <div className="space-y-4">
            {recentActivity.map((activity, index) => (
              <div
                key={index}
                className="flex items-center gap-3 p-3 rounded-lg bg-cyber-surface2/50"
              >
                <div className="w-8 h-8 rounded-lg bg-neon-cyan/10 flex items-center justify-center">
                  <activity.icon className="w-4 h-4 text-neon-cyan" />
                </div>
                <div className="flex-1">
                  <p className="text-sm">{activity.action}</p>
                </div>
                <span className="text-xs text-text-muted">{activity.time}</span>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Quota Info */}
        <motion.div variants={itemVariants} className="cyber-card p-6">
          <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
            <Cpu className="w-5 h-5 text-neon-green" />
            حصصك
          </h2>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-text-muted">ملفات Python</span>
                <span className="font-mono">0 / {user?.max_python_files}</span>
              </div>
              <div className="h-2 bg-cyber-surface2 rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-neon-cyan rounded-full"
                  initial={{ width: 0 }}
                  animate={{ width: '0%' }}
                  transition={{ duration: 1, delay: 0.5 }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-text-muted">ملفات PHP</span>
                <span className="font-mono">0 / {user?.max_php_files}</span>
              </div>
              <div className="h-2 bg-cyber-surface2 rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-neon-green rounded-full"
                  initial={{ width: 0 }}
                  animate={{ width: '0%' }}
                  transition={{ duration: 1, delay: 0.6 }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-text-muted">البوتات الجاهزة</span>
                <span className="font-mono">0 / {user?.max_ready_bots}</span>
              </div>
              <div className="h-2 bg-cyber-surface2 rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-neon-purple rounded-full"
                  initial={{ width: 0 }}
                  animate={{ width: '0%' }}
                  transition={{ duration: 1, delay: 0.7 }}
                />
              </div>
            </div>
          </div>
        </motion.div>
      </div>

      {/* AI Status Banner */}
      <motion.div
        variants={itemVariants}
        className="cyber-card p-4 bg-gradient-to-r from-neon-cyan/5 via-neon-green/5 to-neon-purple/5"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-neon-cyan/10 flex items-center justify-center animate-pulse">
              <Zap className="w-6 h-6 text-neon-cyan" />
            </div>
            <div>
              <h3 className="font-bold">الذكاء الاصطناعي متصل</h3>
              <p className="text-sm text-text-muted">
                3 مزودين نشطين | وقت الاستجابة: ~500ms
              </p>
            </div>
          </div>
          <div className="hidden md:flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-neon-green animate-pulse" />
            <span className="text-sm text-neon-green font-mono">ONLINE</span>
          </div>
        </div>
      </motion.div>
    </motion.div>
  )
}

export default Dashboard
