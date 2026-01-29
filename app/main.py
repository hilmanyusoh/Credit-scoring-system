from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from . import models, database, ml_engine
from pydantic import BaseModel

app = FastAPI(title="iBank Credit Scoring API")
ai = ml_engine.MLEngine()

class ScoringRequest(BaseModel):
    customer_id: int
    net_monthly_income: float
    yearly_debt_payments: float
    account_tenure_months: int
    prev_defaults: int = 0
    mou_status: str = "N"

@app.post("/predict")
def predict_credit(request: ScoringRequest, db: Session = Depends(database.get_db)):
    input_data = {
        "income": request.net_monthly_income,
        "debt": request.yearly_debt_payments / 12,
        "tenure": request.account_tenure_months,
        "mou": request.mou_status,
        "defaults": request.prev_defaults
    }

    try:
        result = ai.predict(input_data)
        
        # บันทึกลง Database (CreditScoreLog)
        new_log = models.CreditScoreLog(
            customer_id=request.customer_id,
            record_id=None, # ข้าม Foreign Key ไปก่อน
            raw_input_data=input_data, # ส่ง dict ให้ JSON column
            final_score=result['score'],
            grade=result['grade'],
            is_approved=result['is_approved']
        )
        db.add(new_log)
        db.commit()
        db.refresh(new_log)
        
        return {
            "score": result['score'],
            "grade": result['grade'],
            "status": result['status'],
            "is_approved": result['is_approved'],
            "rate": result['rate'],
            "multiplier": result['multiplier']
        }
    except Exception as e:
        db.rollback()
        print(f"❌ API/DB ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))