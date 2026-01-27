FROM python:3.10-slim

# ตั้งค่า Working Directory
WORKDIR /app

# ติดตั้ง System Dependencies (เพิ่ม libgomp1 สำหรับ XGBoost)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# ติดตั้ง Python Libraries (ทำก่อน Copy code เพื่อใช้ Cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# คัดลอกไฟล์ทั้งหมด (รวมถึงโฟลเดอร์ app/)
COPY . .

# เปิด Port 8000
EXPOSE 8000

# คำสั่งรัน (ตรวจสอบว่าในโปรเจกต์มีไฟล์ app/__init__.py ด้วย)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]