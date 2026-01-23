FROM python:3.10-slim

# ตั้งค่า Working Directory ใน Container
WORKDIR /app

# ติดตั้ง System Dependencies สำหรับ PostgreSQL
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# ติดตั้ง Python Libraries
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# คัดลอก Code ทั้งหมดเข้าไป
COPY . .

# สั่งให้รัน API เมื่อ Container เริ่มทำงาน
CMD ["uvicorn", "web.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]