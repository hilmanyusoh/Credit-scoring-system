from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Numeric, JSON
from sqlalchemy.sql import func
from .database import Base

class Customer(Base):
    __tablename__ = "customers"
    customer_id = Column(Integer, primary_key=True, index=True)
    member_id = Column(String(20), unique=True, index=True)
    first_name = Column(String(100))
    age = Column(Integer)
    gender = Column(String(20))
    province = Column(String(100))
    owns_car = Column(Boolean, default=False) 
    owns_house = Column(Boolean, default=False)
    registration_date = Column(DateTime, server_default=func.now())

class FinancialRecord(Base):
    __tablename__ = "financial_records"
    record_id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"))
    net_monthly_income = Column(Numeric(15, 2))
    yearly_debt_payments = Column(Numeric(15, 2))
    credit_limit_used_pct = Column(Float)
    credit_limit_used_pct = Column(Float)
    prev_defaults = Column(Integer)
    account_tenure_months = Column(Integer)  
    occupation_type = Column(String)
    created_at = Column(DateTime, server_default=func.now())

class CreditScoreLog(Base):
    __tablename__ = "credit_score_logs"
    log_id = Column(Integer, primary_key=True, index=True)
    record_id = Column(Integer, ForeignKey("financial_records.record_id"))
    raw_input_data = Column(JSON) # สำหรับเก็บข้อมูลทั้งหมดที่ลูกค้ากรอก
    final_score = Column(Integer)
    grade = Column(String(5))
    is_approved = Column(Boolean)
    calculated_at = Column(DateTime, server_default=func.now())