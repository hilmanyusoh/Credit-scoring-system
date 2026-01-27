from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from . import models, database, ml_engine

app = FastAPI()
ai = ml_engine.MLEngine()

@app.post("/predict")
def predict_credit(data: dict, db: Session = Depends(database.get_db)):
    # 1. คำนวณ Score ผ่าน AI Engine
    score, grade, approved = ai.predict(data)
    
    # 2. บันทึกลง Database (ตาราง logs)
    # (โค้ดส่วนการ Save ลง DB จะเชื่อมกับข้อมูลลูกค้าที่มีอยู่)
    
    return {
        "score": score,
        "grade": grade,
        "decision": "Approved" if approved else "Rejected"
    }