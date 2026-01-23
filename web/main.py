from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from database.connection import engine, Base, get_db
# นำเข้า models เพื่อให้ Base.metadata รู้จัก table
from database import models 

# พยายามสร้างตาราง
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"Database connection error: {e}")

app = FastAPI(title="ibank Credit Scoring API 2026")

@app.get("/")
def read_root():
    return {"message": "Hello ibank, Docker is working!"}

@app.get("/healthcheck")
def healthcheck(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"database": "connected"}
    except Exception as e:
        return {"database": "error", "detail": str(e)}