import pandas as pd
import joblib
import os

class MLEngine:
    def __init__(self):
        # เปลี่ยนจากการ Fix ชื่อ User มาเป็นหาตำแหน่งโปรเจกต์อัตโนมัติ
        # 1. หาตำแหน่งไฟล์ ml_engine.py นี้
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # 2. ถอยออกจากโฟลเดอร์ app ไปยัง Root เพื่อเข้าโฟลเดอร์ models
        base_path = os.path.join(os.path.dirname(current_dir), "models")
        
        print(f"🔍 [MLEngine] Loading models from: {base_path}")
        
        try:
            self.xgb = joblib.load(os.path.join(base_path, "xgb_model.pkl"))
            self.log = joblib.load(os.path.join(base_path, "log_model.pkl"))
            self.scaler = joblib.load(os.path.join(base_path, "scaler.pkl"))
            self.le_dict = joblib.load(os.path.join(base_path, "le_dict.pkl"))
            self.config = joblib.load(os.path.join(base_path, "scoring_config.pkl"))
            print("✅ [MLEngine] Loaded all models successfully.")
        except Exception as e:
            print(f"❌ [MLEngine] Error: {e}")
            print(f"📌 โปรดตรวจสอบว่ามีไฟล์โมเดลอยู่ใน: {base_path}")
            raise e

    def predict(self, data):
        # --- (ส่วนการคำนวณด้านล่างใช้ตามที่คุณเขียนได้เลยครับ ถูกต้องแล้ว) ---
        income = float(data.get('income', 0))
        monthly_debt = float(data.get('debt', 0))
        tenure = int(data.get('tenure', 0))
        mou = str(data.get('mou', 'N'))
        defaults = int(data.get('defaults', 0))

        yearly_debt = monthly_debt * 12
        dti = (yearly_debt / (income * 12)) if income > 0 else 0
        
        def_occ = self.le_dict['occupation_type'].classes_[0]
        mou_valid = mou if mou in self.le_dict['mou_status'].classes_ else self.le_dict['mou_status'].classes_[0]

        ml_input = {
            "net_monthly_income": income,
            "dti_ratio": dti,
            "credit_limit_used_pct": 0.3,
            "prev_defaults": defaults,
            "account_tenure_months": tenure,
            "occupation_type": def_occ,
            "mou_status": mou_valid
        }

        X_df = pd.DataFrame([ml_input])
        for col, le in self.le_dict.items():
            if col in X_df.columns:
                X_df[col] = le.transform(X_df[col].astype(str))
        
        prob_xgb = self.xgb.predict_proba(X_df)[0][1]
        X_scaled = self.scaler.transform(X_df)
        prob_log = self.log.predict_proba(X_scaled)[0][1]
        
        ml_score = int((1 - ((prob_xgb + prob_log) / 2)) * 400) + 450

        logic_score = 0
        logic_score += 0.35 * (1 - min(defaults/1, 1)) * 850
        logic_score += 0.30 * max(0, 1 - dti) * 850
        logic_score += 0.15 * min(tenure / 120, 1) * 850
        logic_score += 0.10 * (1.0 if mou_valid == 'Y' else 0.8) * 850
        logic_score += 0.10 * 0.8 * 850 

        final_score = int(0.6 * logic_score + 0.4 * ml_score)
        
        result = next((g for g in self.config['grade_map'] if final_score >= g['min']), self.config['grade_map'][-1])

        is_approved = True
        if income < 20000: is_approved = False
        if tenure < 12: is_approved = False
        if result.get('grade') in ["C", "HH"]: is_approved = False

        return {
            "score": final_score,
            "grade": result.get('grade', 'N/A'),
            "status": result.get('status', result.get('label', 'N/A')),
            "is_approved": is_approved,
            "multiplier": float(result.get('mult', 0)),
            "rate": float(result.get('rate', 7.95)),
            "dsr": float(dti * 100)
        }