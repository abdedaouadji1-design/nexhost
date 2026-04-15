import { useState } from 'react'
import { motion } from 'framer-motion'
import {
  Sparkles,
  Send,
  Bot,
  Code,
  Wand2,
  Bug,
  Copy,
  Check,
  Play,
  Download,
  MessageSquare,
  Settings,
  Loader2,
} from 'lucide-react'
import toast from 'react-hot-toast'
import { aiApi } from '../utils/api'

const AIBotGenerator = () => {
  const [description, setDescription] = useState('')
  const [botType, setBotType] = useState('telegram')
  const [features, setFeatures] = useState<string[]>([])
  const [generatedCode, setGeneratedCode] = useState('')
  const [requirements, setRequirements] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [copied, setCopied] = useState(false)
  
  // Debug mode
  const [debugCode, setDebugCode] = useState('')
  const [debugError, setDebugError] = useState('')
  const [isDebugging, setIsDebugging] = useState(false)
  const [fixedCode, setFixedCode] = useState('')

  const botTypes = [
    { value: 'telegram', label: 'Telegram', icon: MessageSquare },
    { value: 'discord', label: 'Discord', icon: Bot },
  ]

  const featureOptions = [
    'ردود تلقائية',
    'قاعدة بيانات',
    'لوحة تحكم',
    'إشعارات',
    'أوامر مخصصة',
    'تخزين ملفات',
    'تكامل AI',
    'مصادقة مستخدمين',
  ]

  const handleGenerate = async () => {
    if (!description.trim()) {
      toast.error('يرجى وصف البوت الذي تريده')
      return
    }

    setIsGenerating(true)
    setGeneratedCode('')
    setRequirements('')

    try {
      const response = await aiApi.generateBot(description, botType, features)
      setGeneratedCode(response.data.code)
      setRequirements(response.data.requirements)
      toast.success('تم إنشاء البوت بنجاح!')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'فشل إنشاء البوت')
    } finally {
      setIsGenerating(false)
    }
  }

  const handleDebug = async () => {
    if (!debugCode.trim()) {
      toast.error('يرجى إدخال الكود للتصحيح')
      return
    }

    setIsDebugging(true)
    setFixedCode('')

    try {
      const response = await aiApi.debugBot(debugCode, debugError)
      setFixedCode(response.data.fixed_code)
      toast.success('تم تصحيح الكود!')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'فشل التصحيح')
    } finally {
      setIsDebugging(false)
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    setCopied(true)
    toast.success('تم النسخ!')
    setTimeout(() => setCopied(false), 2000)
  }

  const downloadCode = () => {
    const blob = new Blob([generatedCode], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'bot.py'
    a.click()
    URL.revokeObjectURL(url)
    toast.success('تم التحميل!')
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center mb-8">
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-gradient-to-br from-neon-purple to-neon-cyan mb-4 shadow-neon-purple"
        >
          <Sparkles className="w-10 h-10 text-white" />
        </motion.div>
        <h1 className="text-3xl font-bold mb-2">صانع البوتات بالذكاء الاصطناعي</h1>
        <p className="text-text-muted">صف بوتك وسنقوم بإنشائه لك</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Generator Section */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="cyber-card p-6"
        >
          <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
            <Wand2 className="w-5 h-5 text-neon-cyan" />
            إنشاء بوت جديد
          </h2>

          {/* Bot Type */}
          <div className="mb-4">
            <label className="text-sm text-text-secondary mb-2 block">نوع البوت</label>
            <div className="flex gap-2">
              {botTypes.map((type) => (
                <button
                  key={type.value}
                  onClick={() => setBotType(type.value)}
                  className={`flex-1 flex items-center justify-center gap-2 p-3 rounded-lg border transition-all ${
                    botType === type.value
                      ? 'bg-neon-cyan/10 border-neon-cyan text-neon-cyan'
                      : 'bg-cyber-surface2 border-cyber-border hover:border-neon-cyan/50'
                  }`}
                >
                  <type.icon className="w-4 h-4" />
                  {type.label}
                </button>
              ))}
            </div>
          </div>

          {/* Features */}
          <div className="mb-4">
            <label className="text-sm text-text-secondary mb-2 block">الميزات المطلوبة</label>
            <div className="flex flex-wrap gap-2">
              {featureOptions.map((feature) => (
                <button
                  key={feature}
                  onClick={() => {
                    setFeatures((prev) =>
                      prev.includes(feature)
                        ? prev.filter((f) => f !== feature)
                        : [...prev, feature]
                    )
                  }}
                  className={`px-3 py-1.5 rounded-full text-sm transition-all ${
                    features.includes(feature)
                      ? 'bg-neon-green/20 text-neon-green border border-neon-green/50'
                      : 'bg-cyber-surface2 text-text-muted border border-cyber-border hover:border-neon-cyan/30'
                  }`}
                >
                  {feature}
                </button>
              ))}
            </div>
          </div>

          {/* Description */}
          <div className="mb-4">
            <label className="text-sm text-text-secondary mb-2 block">
              وصف البوت
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="cyber-input h-32 resize-none"
              placeholder="مثال: بوت Telegram لإدارة المجموعات يقوم بحظر المستخدمين المزعجين تلقائياً..."
            />
          </div>

          {/* Generate Button */}
          <motion.button
            onClick={handleGenerate}
            disabled={isGenerating}
            className="w-full neon-btn neon-btn-primary py-4 flex items-center justify-center gap-2"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            {isGenerating ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                جاري الإنشاء...
              </>
            ) : (
              <>
                <Sparkles className="w-5 h-5" />
                إنشاء البوت
              </>
            )}
          </motion.button>
        </motion.div>

        {/* Debug Section */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="cyber-card p-6"
        >
          <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
            <Bug className="w-5 h-5 text-neon-red" />
            تصحيح الأخطاء
          </h2>

          {/* Code Input */}
          <div className="mb-4">
            <label className="text-sm text-text-secondary mb-2 block">
              الكود
            </label>
            <textarea
              value={debugCode}
              onChange={(e) => setDebugCode(e.target.value)}
              className="cyber-input h-32 resize-none font-mono text-sm"
              placeholder="الصق الكود هنا..."
              dir="ltr"
            />
          </div>

          {/* Error Message */}
          <div className="mb-4">
            <label className="text-sm text-text-secondary mb-2 block">
              رسالة الخطأ (اختياري)
            </label>
            <input
              type="text"
              value={debugError}
              onChange={(e) => setDebugError(e.target.value)}
              className="cyber-input"
              placeholder="الصق رسالة الخطأ هنا..."
              dir="ltr"
            />
          </div>

          {/* Debug Button */}
          <motion.button
            onClick={handleDebug}
            disabled={isDebugging}
            className="w-full neon-btn bg-neon-red/10 border border-neon-red/50 text-neon-red hover:bg-neon-red/20 py-4 flex items-center justify-center gap-2"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            {isDebugging ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                جاري التصحيح...
              </>
            ) : (
              <>
                <Bug className="w-5 h-5" />
                تصحيح الكود
              </>
            )}
          </motion.button>

          {/* Fixed Code */}
          {fixedCode && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-4"
            >
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm text-neon-green">الكود المصحح</label>
                <button
                  onClick={() => copyToClipboard(fixedCode)}
                  className="text-xs text-neon-cyan hover:underline"
                >
                  نسخ
                </button>
              </div>
              <pre className="bg-cyber-surface2 p-3 rounded-lg overflow-x-auto text-xs font-mono" dir="ltr">
                {fixedCode}
              </pre>
            </motion.div>
          )}
        </motion.div>
      </div>

      {/* Generated Code Display */}
      {generatedCode && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="cyber-card"
        >
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-cyber-border">
            <div className="flex items-center gap-3">
              <Code className="w-5 h-5 text-neon-cyan" />
              <h3 className="font-bold">الكود المُنشأ</h3>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => copyToClipboard(generatedCode)}
                className="p-2 rounded-lg hover:bg-cyber-surface2 transition-colors"
                title="نسخ"
              >
                {copied ? <Check className="w-4 h-4 text-neon-green" /> : <Copy className="w-4 h-4" />}
              </button>
              <button
                onClick={downloadCode}
                className="p-2 rounded-lg hover:bg-cyber-surface2 transition-colors"
                title="تحميل"
              >
                <Download className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Code */}
          <div className="p-4 overflow-x-auto">
            <pre className="text-sm font-mono" dir="ltr">
              <code>{generatedCode}</code>
            </pre>
          </div>

          {/* Requirements */}
          {requirements && (
            <div className="p-4 border-t border-cyber-border bg-cyber-surface2/50">
              <h4 className="text-sm font-bold mb-2 flex items-center gap-2">
                <Settings className="w-4 h-4" />
                المتطلبات (requirements.txt)
              </h4>
              <pre className="text-xs font-mono text-text-muted" dir="ltr">
                {requirements}
              </pre>
            </div>
          )}

          {/* Actions */}
          <div className="p-4 border-t border-cyber-border flex gap-3">
            <motion.button
              className="flex-1 neon-btn neon-btn-success py-3 flex items-center justify-center gap-2"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <Play className="w-4 h-4" />
              تشغيل البوت
            </motion.button>
            <motion.button
              className="flex-1 neon-btn neon-btn-primary py-3 flex items-center justify-center gap-2"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <Bot className="w-4 h-4" />
              حفظ كبوت جاهز
            </motion.button>
          </div>
        </motion.div>
      )}
    </div>
  )
}

export default AIBotGenerator
