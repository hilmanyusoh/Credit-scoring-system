import streamlit as st
import pandas as pd
import requests
from sqlalchemy import create_engine
import plotly.express as px

# --- Configuration ---
DB_URL = "postgresql://admin:admin123@localhost:5432/credit_score_db"
API_URL = "http://127.0.0.1:8000/predict"
engine = create_engine(DB_URL)

st.set_page_config(page_title="iB-RMC 2026", layout="wide")

# --- Sidebar: Input เฉพาะ Features หลัก ---
st.sidebar.header("📝 กรอกข้อมูลผู้ขอสินเชื่อ")
with st.sidebar.form("predict_form"):
    income = st.number_input("รายได้สุทธิต่อเดือน (บาท)", value=30000, step=1000)
    debt = st.number_input("ภาระหนี้ต่อปี (บาท)", value=50000, step=1000)
    tenure = st.number_input("อายุบัญชี (เดือน)", value=12, step=1)
    defaults = st.number_input("จำนวนครั้งที่ผิดนัดชำระ", value=0, step=1)
    
    occ_list = ["Government", "Private Company", "Business Owner", "Freelance", "Other"]
    occ = st.selectbox("ประเภทอาชีพ", occ_list)
    
    mou = st.radio("สวัสดิการ MOU", ["มี (Y)", "ไม่มี (N)"], index=1)
    
    submit = st.form_submit_button("คำนวณผลอนุมัติ")

if submit:
    # เตรียมข้อมูล (customer_id ใส่ค่าหลอกไว้ เพราะเดี๋ยว DB จะเจน ID ใหม่ให้ใน Logs)
    payload = {
        "customer_id": 999, 
        "net_monthly_income": float(income),
        "yearly_debt_payments": float(debt),
        "account_tenure_months": int(tenure),
        "prev_defaults": int(defaults),
        "credit_limit_used_pct": 0.3, # ค่า Default สำหรับฟิลด์ที่ไม่ได้กรอก
        "occupation_type": occ,
        "mou_status": "Y" if "มี" in mou else "N"
    }
    
    try:
        res = requests.post(API_URL, json=payload)
        if res.status_code == 200:
            data = res.json()
            st.sidebar.success(f"ผลลัพธ์: {data['grade']}")
            st.sidebar.info(f"โอกาสชำระหนี้คืน: {data['repay_probability']}")
        else:
            st.sidebar.error(f"Error: {res.text}")
    except Exception as e:
        st.sidebar.error(f"ไม่สามารถเชื่อมต่อ API ได้: {e}")

# --- Main Dashboard ---
st.title("🛡️ ระบบประเมินความเสี่ยง iB-RMC 2026")

try:
    # ดึงข้อมูลมาเฉพาะที่จำเป็น
    query = """
    SELECT calculated_at, final_score, grade, is_approved 
    FROM credit_score_logs 
    ORDER BY calculated_at DESC
    """
    df = pd.read_sql(query, engine)

    if not df.empty:
        col1, col2, col3 = st.columns(3)
        col1.metric("เคสทั้งหมด", len(df))
        col2.metric("อนุมัติ (Approved)", len(df[df['is_approved'] == True]))
        col3.metric("คะแนนเฉลี่ย", int(df['final_score'].mean()))

        # กราฟแท่งแสดงเกรด
        st.subheader("📊 สรุปสัดส่วนเกรดความเสี่ยง")
        grade_order = ['AA', 'BB', 'CC', 'DD', 'EE', 'FF', 'GG', 'HH']
        fig = px.bar(df['grade'].value_counts().reindex(grade_order).fillna(0).reset_index(), 
                     x='grade', y='count', color='grade',
                     labels={'grade': 'ระดับเกรด', 'count': 'จำนวนราย'},
                     color_discrete_sequence=px.colors.qualitative.Safe)
        st.plotly_chart(fig, use_container_width=True)

        # ตารางประวัติ
        st.subheader("📋 ประวัติการประเมินล่าสุด")
        st.table(df.head(10)) 
    else:
        st.write("ยังไม่มีข้อมูลการคำนวณในระบบ")

except Exception as e:
    st.error(f"ฐานข้อมูลขัดข้อง: {e}")