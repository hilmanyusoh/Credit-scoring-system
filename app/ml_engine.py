import joblib
import os
import pandas as pd
import numpy as np

class MLEngine:
    def __init__(self):
        base_path = os.path.dirname(os.path.dirname(__file__))
        # โหลดโมเดลและตัวแปรเสริม
        self.xgb_model = joblib.load(os.path.join(base_path, "models/xgb_model.pkl"))
        self.log_model = joblib.load(os.path.join(base_path, "models/log_model.pkl"))
        self.scaler = joblib.load(os.path.join(base_path, "models/scaler.pkl"))
        self.le_dict = joblib.load(os.path.join(base_path, "models/le_dict.pkl"))
        
        self.cat_defaults = {'occupation_type': 'Salaried', 'mou_status': 'N'}

    def predict(self, data: dict):
        # 1. รับค่าและทำ Normalization
        income = float(data.get('net_monthly_income', 1)) # ป้องกันหารศูนย์
        
        occ_map = {"พนักงานบริษัท": "Salaried", "ธุรกิจส่วนตัว": "Business Owner", "อิสระ": "Freelance"}
        raw_occ = data.get('occupation_type', 'Salaried')
        occ_type = occ_map.get(raw_occ, raw_occ)

        # 2. เตรียมข้อมูล 7 Features (เรียงลำดับตามที่ Train ใน Notebook)
        ml_input = {
            "net_monthly_income": income,
            "dti_ratio": float(data.get('yearly_debt_payments', 0)) / income,
            "credit_limit_used_pct": float(data.get('credit_limit_used_pct', 0.3)),
            "prev_defaults": int(data.get('prev_defaults', 0)),
            "account_tenure_months": int(data.get('account_tenure_months', 0)),
            "occupation_type": occ_type,
            "mou_status": "Y" if data.get('mou_status') in ['Y', 'มี', 'Yes'] else "N"
        }

        # สร้าง DataFrame และบังคับลำดับ Column ให้เป๊ะ
        feature_order = [
            'net_monthly_income', 'dti_ratio', 'credit_limit_used_pct',
            'prev_defaults', 'account_tenure_months', 'occupation_type', 'mou_status'
        ]
        X_df = pd.DataFrame([ml_input])[feature_order]

        # 3. Label Encoding
        for col, le in self.le_dict.items():
            if col in X_df.columns:
                val = str(X_df[col].iloc[0])
                if val in le.classes_:
                    X_df[col] = le.transform([val])
                else:
                    X_df[col] = le.transform([le.classes_[0]])

        # 4. คำนวณ Risk Probability (Ensemble)
        prob_xgb = self.xgb_model.predict_proba(X_df)[0][1]
        X_scaled = self.scaler.transform(X_df)
        prob_log = self.log_model.predict_proba(X_scaled)[0][1]
        
        avg_risk_prob = (prob_xgb + prob_log) / 2
        repay_prob = 1 - avg_risk_prob

        # 5. คำนวณ Score (300 - 900) และเกรด GE02
        final_score = int(300 + (repay_prob * 600))
        grade = self._get_ge02_grade(final_score)
        
        return {
            "type_of_score": "iB-RMC 2026",
            "score": final_score,
            "grade": grade,
            "repay_probability": f"{repay_prob * 100:.0f}%",
            "is_approved": final_score >= 616, # เกรด GG ขึ้นไป
            "status": self._get_status_text(grade)
        }

    def _get_ge02_grade(self, score):
        if score >= 753: return "AA"
        if score >= 725: return "BB"
        if score >= 699: return "CC"
        if score >= 681: return "DD"
        if score >= 666: return "EE"
        if score >= 646: return "FF"
        if score >= 616: return "GG"
        return "HH"

    def _get_status_text(self, grade):
        good_grades = ["AA", "BB", "CC", "DD"]
        return "ดีมาก" if grade in good_grades else "พอใช้" if grade != "HH" else "ต้องพิจารณาเป็นพิเศษ"