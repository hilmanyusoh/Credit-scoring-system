import joblib
import os
import pandas as pd

class MLEngine:
    def __init__(self):
        # กำหนด Path ของไฟล์โมเดล
        self.model_path = "models/xgb_model.pkl"
        self.scaler_path = "models/scaler.pkl"
        self.model = None
        self.scaler = None
        self.load_models()

    def load_models(self):
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
            self.scaler = joblib.load(self.scaler_path)
            print("AI Models loaded successfully")
        else:
            print("Warning: Model files not found!")

    def predict(self, data_dict):
        # รับข้อมูลดิบ (dict) -> แปลงเป็น DataFrame -> Scale -> Predict
        df = pd.DataFrame([data_dict])
        
        # ตัวอย่างการคำนวณง่ายๆ หากยังไม่มีไฟล์โมเดล
        score = 500  # Default score
        if data_dict['net_monthly_income'] > 50000: score += 100
        if data_dict['prev_defaults'] == 0: score += 150
        
        # กำหนดเกรด
        grade = "A" if score > 700 else "B" if score > 500 else "C"
        return score, grade, score > 400 # score, grade, is_approved