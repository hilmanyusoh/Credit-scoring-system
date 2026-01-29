import pandas as pd
import joblib
import os

class MLEngine:
    def __init__(self):
        # 1. กำหนด Absolute Path เพื่อป้องกันปัญหาหาไฟล์ไม่เจอ
        base_path = "/Users/hilmanyusoh/Desktop/Credit-Scoring-System/models"
        
        try:
            self.xgb = joblib.load(f"{base_path}/xgb_model.pkl")
            self.log = joblib.load(f"{base_path}/log_model.pkl")
            self.scaler = joblib.load(f"{base_path}/scaler.pkl")
            self.le_dict = joblib.load(f"{base_path}/le_dict.pkl")
            self.config = joblib.load(f"{base_path}/scoring_config.pkl")
            print("✅ [MLEngine] Loaded all models and configurations successfully.")
        except Exception as e:
            print(f"❌ [MLEngine] Error loading models: {e}")
            raise e

    def predict(self, data):
        # 2. ดึงข้อมูลแบบปลอดภัย (Safe Get) พร้อมแปลง Type
        income = float(data.get('income', 0))
        monthly_debt = float(data.get('debt', 0))
        tenure = int(data.get('tenure', 0))
        mou = str(data.get('mou', 'N'))
        defaults = int(data.get('defaults', 0))

        # 3. คำนวณ Features พื้นฐาน
        yearly_debt = monthly_debt * 12
        dti = (yearly_debt / (income * 12)) if income > 0 else 0
        
        # 4. จัดการ Unseen Labels (ป้องกัน Error 500 จากค่าที่ Model ไม่รู้จัก)
        # ดึงค่าแรกที่ LabelEncoder รู้จักมาใช้เป็นค่าเริ่มต้น
        def_occ = self.le_dict['occupation_type'].classes_[0]
        
        # ตรวจสอบ mou_status (ต้องเป็น 'Y' หรือ 'N' ตามที่เคย Train)
        mou_valid = mou if mou in self.le_dict['mou_status'].classes_ else self.le_dict['mou_status'].classes_[0]

        ml_input = {
            "net_monthly_income": income,
            "dti_ratio": dti,
            "credit_limit_used_pct": 0.3, # ค่าสมมติฐานมาตรฐาน
            "prev_defaults": defaults,
            "account_tenure_months": tenure,
            "occupation_type": def_occ,
            "mou_status": mou_valid
        }

        # 5. ML Prediction (40% Weight)
        X_df = pd.DataFrame([ml_input])
        
        # ทำ Label Encoding
        for col, le in self.le_dict.items():
            if col in X_df.columns:
                X_df[col] = le.transform(X_df[col].astype(str))
        
        # คำนวณความน่าจะเป็นของความเสี่ยง (Probability of Risk)
        prob_xgb = self.xgb.predict_proba(X_df)[0][1]
        X_scaled = self.scaler.transform(X_df)
        prob_log = self.log.predict_proba(X_scaled)[0][1]
        
        # แปลงเป็นคะแนนช่วง 450 - 850
        ml_score = int((1 - ((prob_xgb + prob_log) / 2)) * 400) + 450

        # 6. Logic Scoring (60% Weight) - อ้างอิงเกณฑ์ FICO
        logic_score = 0
        logic_score += 0.35 * (1 - min(defaults/1, 1)) * 850    # ประวัติชำระเงิน
        logic_score += 0.30 * max(0, 1 - dti) * 850             # ภาระหนี้ (DTI)
        logic_score += 0.15 * min(tenure / 120, 1) * 850       # อายุงาน (ความมั่นคง)
        logic_score += 0.10 * (1.0 if mou_valid == 'Y' else 0.8) * 850 # พันธมิตรธุรกิจ
        logic_score += 0.10 * 0.8 * 850                        # ปัจจัยเสริมอื่นๆ

        # 7. ผสมคะแนน (Hybrid Score)
        final_score = int(0.6 * logic_score + 0.4 * ml_score)
        
        # 8. สรุปผล Grade และ เงื่อนไขการอนุมัติ
        # ค้นหา Grade จาก config ถ้าไม่เจอให้ใช้เกรดต่ำสุด
        result = next((g for g in self.config['grade_map'] if final_score >= g['min']), self.config['grade_map'][-1])

        # กฎการอนุมัติ (Hard Rules)
        is_approved = True
        if income < 20000: is_approved = False      # รายได้ขั้นต่ำ
        if tenure < 12: is_approved = False         # อายุงานขั้นต่ำ 1 ปี
        if result.get('grade') in ["C", "HH"]: is_approved = False # เกรดความเสี่ยงสูง

        return {
            "score": final_score,
            "grade": result.get('grade', 'N/A'),
            "status": result.get('status', result.get('label', 'N/A')),
            "is_approved": is_approved,
            "multiplier": float(result.get('mult', 0)),
            "rate": float(result.get('rate', 15.0))
        }