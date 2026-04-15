import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  Bot,
  Play,
  Square,
  Trash2,
  FileText,
  Terminal,
  RefreshCw,
} from 'lucide-react'
import toast from 'react-hot-toast'
import { userBotsApi } from '../utils/api'

interface BotInstance {
  id: number
  name: string
  status: string
  template_name: string
  debug_mode: boolean
  created_at: string
  started_at: string | null
}

const MyBots = () => {
  const [bots, setBots] = useState<BotInstance[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedBot, setSelectedBot] = useState<BotInstance | null>(null)
  const [logs, setLogs] = useState<string[]>([])
  const [showLogs, setShowLogs] = useState(false)

  useEffect(() => {
    loadBots()
  }, [])

  const loadBots = async () => {
    try {
      const response = await userBotsApi.list()
      setBots(response.data)
    } catch (error) {
      toast.error('فشل تحميل البوتات')
    } finally {
      setLoading(false)
    }
  }

  const handleStart = async (botId: number) => {
    try {
      await userBotsApi.start(botId)
      toast.success('تم تشغيل البوت')
      loadBots()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'فشل التشغيل')
    }
  }

  const handleStop = async (botId: number) => {
    try {
      await userBotsApi.stop(botId)
      toast.success('تم إيقاف البوت')
      loadBots()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'فشل الإيقاف')
    }
  }

  const handleDelete = async (botId: number) => {
    if (!confirm('هل أنت متأكد من حذف هذا البوت؟')) return

    try {
      await userBotsApi.delete(botId)
      toast.success('تم حذف البوت')
      loadBots()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'فشل الحذف')
    }
  }

  const viewLogs = async (bot: BotInstance) => {
    try {
      const response = await userBotsApi.logs(bot.id, 100)
      setLogs(response.data.logs)
      setSelectedBot(bot)
      setShowLogs(true)
    } catch (error) {
      toast.error('فشل تحميل السجلات')
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="cyber-loader" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold mb-2">بوتاتي</h1>
          <p className="text-text-muted">إدارة بوتاتك المنشأة</p>
        </div>
        <motion.button
          onClick={loadBots}
          className="p-2 rounded-lg bg-cyber-surface2 border border-cyber-border hover:border-neon-cyan/50 transition-colors"
          whileHover={{ rotate: 180 }}
          transition={{ duration: 0.5 }}
        >
          <RefreshCw className="w-5 h-5" />
        </motion.button>
      </div>

      {/* Bots Grid */}
      {bots.length === 0 ? (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="cyber-card p-12 text-center"
        >
          <div className="w-20 h-20 rounded-full bg-neon-cyan/10 flex items-center justify-center mx-auto mb-4">
            <Bot className="w-10 h-10 text-neon-cyan" />
          </div>
          <h3 className="text-xl font-bold mb-2">لا توجد بوتات</h3>
          <p className="text-text-muted">اذهب إلى البوتات الجاهزة لإنشاء بوت</p>
        </motion.div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {bots.map((bot, index) => (
            <motion.div
              key={bot.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="cyber-card p-5"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                    bot.status === 'running'
                      ? 'bg-neon-green/10'
                      : 'bg-cyber-surface2'
                  }`}>
                    <Bot className={`w-6 h-6 ${
                      bot.status === 'running' ? 'text-neon-green' : 'text-text-muted'
                    }`} />
                  </div>
                  <div>
                    <h3 className="font-bold">{bot.name}</h3>
                    <p className="text-sm text-text-muted">{bot.template_name}</p>
                  </div>
                </div>
                <span className={`status-badge ${
                  bot.status === 'running' ? 'status-running' : 'status-stopped'
                }`}>
                  {bot.status === 'running' ? 'يعمل' : 'متوقف'}
                </span>
              </div>

              {/* Info */}
              <div className="flex items-center gap-4 text-sm text-text-muted mb-4">
                <span className="flex items-center gap-1">
                  <Terminal className="w-4 h-4" />
                  {bot.debug_mode ? 'Debug ON' : 'Debug OFF'}
                </span>
                <span>
                  تم الإنشاء: {new Date(bot.created_at).toLocaleDateString('ar-SA')}
                </span>
              </div>

              {/* Actions */}
              <div className="flex gap-2">
                {bot.status === 'running' ? (
                  <button
                    onClick={() => handleStop(bot.id)}
                    className="flex-1 py-2 rounded-lg bg-neon-red/10 text-neon-red border border-neon-red/30 hover:bg-neon-red/20 transition-colors flex items-center justify-center gap-2"
                  >
                    <Square className="w-4 h-4" />
                    إيقاف
                  </button>
                ) : (
                  <button
                    onClick={() => handleStart(bot.id)}
                    className="flex-1 py-2 rounded-lg bg-neon-green/10 text-neon-green border border-neon-green/30 hover:bg-neon-green/20 transition-colors flex items-center justify-center gap-2"
                  >
                    <Play className="w-4 h-4" />
                    تشغيل
                  </button>
                )}
                <button
                  onClick={() => viewLogs(bot)}
                  className="px-3 py-2 rounded-lg bg-cyber-surface2 border border-cyber-border hover:border-neon-cyan/50 transition-colors"
                >
                  <FileText className="w-4 h-4" />
                </button>
                <button
                  onClick={() => handleDelete(bot.id)}
                  className="px-3 py-2 rounded-lg bg-cyber-surface2 border border-cyber-border hover:border-neon-red/50 text-neon-red transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </motion.div>
          ))}
        </div>
      )}

      {/* Logs Modal */}
      {showLogs && selectedBot && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="absolute inset-0 bg-black/70 backdrop-blur-sm"
            onClick={() => setShowLogs(false)}
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="cyber-card w-full max-w-3xl max-h-[80vh] flex flex-col relative z-10"
          >
            <div className="p-4 border-b border-cyber-border flex items-center justify-between">
              <h3 className="font-bold flex items-center gap-2">
                <Terminal className="w-5 h-5 text-neon-cyan" />
                سجلات {selectedBot.name}
              </h3>
              <button
                onClick={() => setShowLogs(false)}
                className="p-2 rounded-lg hover:bg-cyber-surface2"
              >
                ✕
              </button>
            </div>
            <div className="flex-1 overflow-auto p-4 bg-black font-mono text-sm">
              {logs.length === 0 ? (
                <p className="text-text-muted text-center py-8">لا توجد سجلات</p>
              ) : (
                logs.map((log, i) => (
                  <div key={i} className="py-1 border-b border-cyber-border/30">
                    {log}
                  </div>
                ))
              )}
            </div>
          </motion.div>
        </div>
      )}
    </div>
  )
}

export default MyBots
