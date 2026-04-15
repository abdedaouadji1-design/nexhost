import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  Users,
  Plus,
  Search,
  Edit2,
  Trash2,
  UserPlus,
} from 'lucide-react'
import toast from 'react-hot-toast'
import { usersApi } from '../utils/api'

interface User {
  id: number
  username: string
  email: string
  role: string
  is_active: boolean
  max_python_files: number
  max_php_files: number
  max_ready_bots: number
  created_at: string
  last_login: string | null
}

const Users = () => {
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    loadUsers()
  }, [])

  const loadUsers = async () => {
    try {
      const response = await usersApi.list()
      setUsers(response.data)
    } catch (error) {
      toast.error('فشل تحميل المستخدمين')
    } finally {
      setLoading(false)
    }
  }

  const filteredUsers = users.filter(user =>
    user.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
    user.email.toLowerCase().includes(searchQuery.toLowerCase())
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
          <h1 className="text-2xl font-bold mb-2">المستخدمين</h1>
          <p className="text-text-muted">إدارة مستخدمي النظام</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted" />
            <input
              type="text"
              placeholder="البحث..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="cyber-input pr-10 w-64"
            />
          </div>
          <motion.button
            className="neon-btn neon-btn-primary flex items-center gap-2"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <UserPlus className="w-4 h-4" />
            مستخدم جديد
          </motion.button>
        </div>
      </div>

      {/* Users Table */}
      <div className="cyber-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-cyber-surface2">
              <tr>
                <th className="px-4 py-3 text-right text-sm font-medium text-text-muted">المستخدم</th>
                <th className="px-4 py-3 text-right text-sm font-medium text-text-muted">الدور</th>
                <th className="px-4 py-3 text-right text-sm font-medium text-text-muted">الحصص</th>
                <th className="px-4 py-3 text-right text-sm font-medium text-text-muted">الحالة</th>
                <th className="px-4 py-3 text-right text-sm font-medium text-text-muted">آخر دخول</th>
                <th className="px-4 py-3 text-right text-sm font-medium text-text-muted">الإجراءات</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-cyber-border">
              {filteredUsers.map((user) => (
                <tr key={user.id} className="hover:bg-cyber-surface2/50 transition-colors">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-neon-cyan to-neon-purple flex items-center justify-center text-cyber-bg font-bold">
                        {user.username[0].toUpperCase()}
                      </div>
                      <div>
                        <p className="font-medium">{user.username}</p>
                        <p className="text-sm text-text-muted">{user.email}</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded-full text-xs ${
                      user.role === 'superadmin'
                        ? 'bg-neon-red/10 text-neon-red'
                        : user.role === 'admin'
                        ? 'bg-neon-purple/10 text-neon-purple'
                        : 'bg-neon-cyan/10 text-neon-cyan'
                    }`}>
                      {user.role}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="text-sm space-y-1">
                      <p>Python: {user.max_python_files}</p>
                      <p>PHP: {user.max_php_files}</p>
                      <p>بوتات: {user.max_ready_bots}</p>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded-full text-xs ${
                      user.is_active
                        ? 'bg-neon-green/10 text-neon-green'
                        : 'bg-neon-red/10 text-neon-red'
                    }`}>
                      {user.is_active ? 'نشط' : 'معطل'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-text-muted">
                    {user.last_login
                      ? new Date(user.last_login).toLocaleDateString('ar-SA')
                      : 'لم يسبق له'}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <button className="p-2 rounded-lg hover:bg-cyber-surface2 text-neon-cyan">
                        <Edit2 className="w-4 h-4" />
                      </button>
                      <button className="p-2 rounded-lg hover:bg-cyber-surface2 text-neon-red">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default Users
