import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  Bot,
  Plus,
  Search,
  Filter,
  Star,
  ChevronLeft,
  Play,
  Settings,
  Code,
} from 'lucide-react'
import toast from 'react-hot-toast'
import { userBotsApi } from '../utils/api'

interface BotTemplate {
  id: number
  name: string
  description: string
  bot_type: string
  image_url?: string
  icon: string
  is_premium: boolean
  config_fields: Array<{
    name: string
    label: string
    type: string
    required: boolean
  }>
}

const ReadyBots = () => {
  const [bots, setBots] = useState<BotTemplate[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedBot, setSelectedBot] = useState<BotTemplate | null>(null)
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [botConfig, setBotConfig] = useState<Record<string, string>>({})
  const [botName, setBotName] = useState('')
  const [debugMode, setDebugMode] = useState(false)
  const [creating, setCreating] = useState(false)

  useEffect(() => {
    loadBots()
  }, [])

  const loadBots = async () => {
    try {
      const response = await userBotsApi.listAvailable()
      setBots(response.data)
    } catch (error) {
      toast.error('فشل تحميل البوتات')
    } finally {
      setLoading(false)
    }
  }

  const handleCreateBot = async () => {
    if (!selectedBot || !botName) {
      toast.error('يرجى إدخال اسم للبوت')
      return
    }

    // Check required fields
    for (const field of selectedBot.config_fields) {
      if (field.required && !botConfig[field.name]) {
        toast.error(`الحقل ${field.label} مطلوب`)
        return
      }
    }

    setCreating(true)
    try {
      await userBotsApi.create({
        template_id: selectedBot.id,
        name: botName,
        config: botConfig,
        debug_mode: debugMode,
      })
      toast.success('تم إنشاء البوت بنجاح!')
      setIsCreateModalOpen(false)
      setSelectedBot(null)
      setBotConfig({})
      setBotName('')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'فشل إنشاء البوت')
    } finally {
      setCreating(false)
    }
  }

  const filteredBots = bots.filter(bot =>
    bot.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    bot.description.toLowerCase().includes(searchQuery.toLowerCase())
  )

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
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold mb-2">البوتات الجاهزة</h1>
          <p className="text-text-muted">اختر بوتاً جاهزاً وقم بتخصيصه</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted" />
            <input
              type="text"
              placeholder="البحث في البوتات..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="cyber-input pr-10 w-64"
            />
          </div>
          <button className="p-2 rounded-lg bg-cyber-surface2 border border-cyber-border hover:border-neon-cyan/50 transition-colors">
            <Filter className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Bots Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredBots.map((bot, index) => (
          <motion.div
            key={bot.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="cyber-card group cursor-pointer"
            onClick={() => {
              setSelectedBot(bot)
              setIsCreateModalOpen(true)
            }}
          >
            {/* Image */}
            <div className="h-40 bg-cyber-surface2 relative overflow-hidden">
              {bot.image_url ? (
                <img
                  src={bot.image_url}
                  alt={bot.name}
                  className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-neon-cyan/10 to-neon-green/10">
                  <span className="text-6xl">{bot.icon}</span>
                </div>
              )}
              
              {/* Premium Badge */}
              {bot.is_premium && (
                <div className="absolute top-3 left-3 px-2 py-1 rounded-full bg-neon-yellow/20 border border-neon-yellow/50 flex items-center gap-1">
                  <Star className="w-3 h-3 text-neon-yellow fill-neon-yellow" />
                  <span className="text-xs text-neon-yellow">Premium</span>
                </div>
              )}

              {/* Hover Overlay */}
              <div className="absolute inset-0 bg-cyber-bg/80 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                <motion.button
                  className="neon-btn neon-btn-primary"
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <Plus className="w-4 h-4" />
                  إنشاء بوت
                </motion.button>
              </div>
            </div>

            {/* Content */}
            <div className="p-4">
              <div className="flex items-start justify-between mb-2">
                <h3 className="font-bold">{bot.name}</h3>
                <span className="text-xs px-2 py-1 rounded-full bg-cyber-surface2 text-text-muted">
                  {bot.bot_type}
                </span>
              </div>
              <p className="text-sm text-text-muted line-clamp-2">{bot.description}</p>
              
              {/* Config Fields Preview */}
              <div className="mt-3 flex flex-wrap gap-2">
                {bot.config_fields.slice(0, 3).map((field) => (
                  <span
                    key={field.name}
                    className="text-xs px-2 py-1 rounded bg-cyber-surface2 text-text-secondary"
                  >
                    {field.label}
                  </span>
                ))}
                {bot.config_fields.length > 3 && (
                  <span className="text-xs px-2 py-1 rounded bg-cyber-surface2 text-text-muted">
                    +{bot.config_fields.length - 3}
                  </span>
                )}
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Create Bot Modal */}
      {isCreateModalOpen && selectedBot && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="absolute inset-0 bg-black/70 backdrop-blur-sm"
            onClick={() => setIsCreateModalOpen(false)}
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            className="cyber-card w-full max-w-lg max-h-[90vh] overflow-y-auto relative z-10"
          >
            {/* Header */}
            <div className="p-6 border-b border-cyber-border">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-xl bg-neon-cyan/10 flex items-center justify-center text-2xl">
                  {selectedBot.icon}
                </div>
                <div>
                  <h2 className="text-xl font-bold">{selectedBot.name}</h2>
                  <p className="text-sm text-text-muted">{selectedBot.description}</p>
                </div>
              </div>
            </div>

            {/* Form */}
            <div className="p-6 space-y-4">
              {/* Bot Name */}
              <div>
                <label className="text-sm text-text-secondary mb-2 block">
                  اسم البوت
                </label>
                <input
                  type="text"
                  value={botName}
                  onChange={(e) => setBotName(e.target.value)}
                  className="cyber-input"
                  placeholder="أدخل اسم البوت"
                />
              </div>

              {/* Config Fields */}
              {selectedBot.config_fields.map((field) => (
                <div key={field.name}>
                  <label className="text-sm text-text-secondary mb-2 block">
                    {field.label}
                    {field.required && <span className="text-neon-red mr-1">*</span>}
                  </label>
                  <input
                    type={field.type === 'password' ? 'password' : 'text'}
                    value={botConfig[field.name] || ''}
                    onChange={(e) =>
                      setBotConfig((prev) => ({
                        ...prev,
                        [field.name]: e.target.value,
                      }))
                    }
                    className="cyber-input"
                    placeholder={`أدخل ${field.label}`}
                  />
                </div>
              ))}

              {/* Debug Mode */}
              <div className="flex items-center gap-3 p-3 rounded-lg bg-cyber-surface2">
                <input
                  type="checkbox"
                  id="debug"
                  checked={debugMode}
                  onChange={(e) => setDebugMode(e.target.checked)}
                  className="w-4 h-4 rounded border-cyber-border bg-cyber-surface2 text-neon-cyan focus:ring-neon-cyan"
                />
                <label htmlFor="debug" className="flex items-center gap-2 cursor-pointer">
                  <Code className="w-4 h-4 text-neon-yellow" />
                  <span className="text-sm">وضع التصحيح (Debug Mode)</span>
                </label>
              </div>
            </div>

            {/* Actions */}
            <div className="p-6 border-t border-cyber-border flex gap-3">
              <button
                onClick={() => setIsCreateModalOpen(false)}
                className="flex-1 py-3 rounded-lg border border-cyber-border hover:bg-cyber-surface2 transition-colors"
              >
                إلغاء
              </button>
              <motion.button
                onClick={handleCreateBot}
                disabled={creating}
                className="flex-1 neon-btn neon-btn-primary py-3 flex items-center justify-center gap-2"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                {creating ? (
                  <div className="cyber-loader w-5 h-5" />
                ) : (
                  <>
                    <Play className="w-4 h-4" />
                    إنشاء البوت
                  </>
                )}
              </motion.button>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  )
}

export default ReadyBots
