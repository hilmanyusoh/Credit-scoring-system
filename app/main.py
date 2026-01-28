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
    credit_limit_used_pct: float = 0.3
    occupation_type: str = "พนักงานบริษัท"
    mou_status: str = "N"

@app.post("/predict")
def predict_credit(request: ScoringRequest, db: Session = Depends(database.get_db)):
    input_data = request.dict()
    try:
        # เรียกใช้ Engine
        result = ai.predict(input_data)
        
        # บันทึกลง Database
        new_log = models.CreditScoreLog(
            customer_id=request.customer_id,
            final_score=result['score'],
            grade=result['grade'],
            is_approved=result['is_approved'],
            raw_input_data=input_data
        )
        db.add(new_log)
        db.commit()
        db.refresh(new_log)
        
        return {
            "log_id": new_log.log_id,
            "type_of_score": result['type_of_score'],
            "score": result['score'],
            "grade": result['grade'],
            "repay_probability": result['repay_probability'],
            "decision": "Approved" if result['is_approved'] else "Rejected",
            "status": result['status']
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/logs/{customer_id}")
def get_history(customer_id: int, db: Session = Depends(database.get_db)):
    return db.query(models.CreditScoreLog).filter(models.CreditScoreLog.customer_id == customer_id).all()