# NexHost V6 🚀

لوحة تحكم استضافة متقدمة مع دمج الذكاء الاصطناعي

## ✨ المميزات

### 🤖 الذكاء الاصطناعي
- **3 مزودين للـ AI** مع نظام fallback تلقائي
- صانع بوتات بالذكاء الاصطناعي
- تصحيح الأخطاء البرمجية بالـ AI
- شرح وتحليل الكود

### 🤖 البوتات الجاهزة
- إنشاء بوتات جاهزة من قبل الأدمن
- تخصيص البوتات بسهولة (Token, Chat ID)
- دمج التوكن تلقائياً بالـ AI
- وضع التصحيح (Debug Mode)

### 📊 إدارة المشاريع
- دعم Python و PHP
- تشغيل وإدارة العمليات
- سجلات ومتابعة الأداء

### 👥 إدارة المستخدمين
- نظام أدوار (Super Admin, Admin, User)
- تحكم في الحصص لكل مستخدم
- Rate limiting و protection

## 🛠️ التقنيات المستخدمة

### Backend
- **FastAPI** - إطار عمل Python سريع
- **PostgreSQL** - قاعدة بيانات إنتاجية
- **SQLAlchemy** - ORM
- **Redis** - للـ caching و rate limiting
- **JWT** - للمصادقة

### Frontend
- **React 18** + **TypeScript**
- **Tailwind CSS** - تصميم حديث
- **Framer Motion** - رسوم متحركة
- **Zustand** - إدارة الحالة

### AI Integration
- 3x DeepSeek APIs (غير رسمية)
- Smart Router مع fallback
- Response caching

## 🚀 التشغيل

### باستخدام Docker Compose

```bash
# Clone repository
git clone <repo-url>
cd nexhost-v6

# Create environment file
cp .env.example .env
# Edit .env with your settings

# Start services
docker-compose up -d

# Access the application
# Frontend: http://localhost
# API: http://localhost/api
# API Docs: http://localhost/docs
```

### متطلبات النظام

- Docker 20.10+
- Docker Compose 2.0+
- 2GB RAM minimum
- 10GB disk space

## 📁 هيكل المشروع

```
nexhost-v6/
├── backend/              # FastAPI Backend
│   ├── main.py          # Entry point
│   ├── api.py           # API routes
│   ├── ai_router.py     # AI integration
│   ├── database.py      # Database models
│   ├── auth.py          # Authentication
│   ├── ready_bots_service.py  # Bot service
│   ├── config.py        # Configuration
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/            # React Frontend
│   ├── src/
│   │   ├── pages/       # Page components
│   │   ├── components/  # Reusable components
│   │   ├── store/       # State management
│   │   └── utils/       # Utilities
│   ├── Dockerfile
│   └── package.json
├── nginx/               # Nginx configuration
├── docker-compose.yml
└── .env.example
```

## 🔐 الأمان

- ✅ JWT authentication
- ✅ Rate limiting
- ✅ Password hashing (bcrypt)
- ✅ SQL injection protection
- ✅ CORS configuration
- ✅ Input validation

## 📝 API Endpoints

### Authentication
- `POST /api/auth/login` - تسجيل الدخول
- `POST /api/auth/refresh` - تجديد التوكن
- `GET /api/auth/me` - معلومات المستخدم

### AI
- `POST /api/ai/chat` - محادثة مع AI
- `POST /api/ai/code/fix` - تصحيح كود
- `POST /api/ai/generate-bot` - إنشاء بوت
- `POST /api/ai/debug-bot` - تصحيح بوت

### Bots
- `GET /api/ready-bots` - قائمة البوتات الجاهزة
- `POST /api/my-bots` - إنشاء بوت
- `GET /api/my-bots` - بوتاتي
- `POST /api/my-bots/{id}/start` - تشغيل بوت
- `POST /api/my-bots/{id}/stop` - إيقاف بوت

## 🤝 المساهمة

نرحب بالمساهمات! يرجى اتباع الخطوات:

1. Fork المشروع
2. إنشاء فرع للميزة (`git checkout -b feature/amazing`)
3. Commit التغييرات (`git commit -m 'Add amazing feature'`)
4. Push للفرع (`git push origin feature/amazing`)
5. فتح Pull Request

## 📄 الترخيص

MIT License - راجع ملف LICENSE

## 👨‍💻 المطور

تم تطويره بـ ❤️ بواسطة NexHost Team

---

**ملاحظة**: هذا المشروع يستخدم APIs غير رسمية للـ AI. استخدمه على مسؤوليتك الخاصة.
