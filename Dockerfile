FROM python:3.11-slim

# تثبيت التبعيات
RUN apt-get update -qq && apt-get install -y git gcc -qq && rm -rf /var/lib/apt/lists/*

# تعيين مجلد العمل
WORKDIR /app

# نسخ ملفات المشروع
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# إنشاء المجلدات اللازمة مع الصلاحيات الصحيحة
RUN mkdir -p /app/data /app/uploads /app/logs && chmod 777 /app/data /app/uploads /app/logs

# تعيين متغيرات البيئة
ENV PYTHONPATH=/app
ENV JWT_SECRET_KEY=nexhost_secret_2026
ENV PORT=5000
ENV DB_PATH=/app/data/nexhost.db

# فتح المنفذ
EXPOSE 5000

# تشغيل التطبيق
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "backend.app:app"]
