import streamlit as st
import requests
import random
import time

# --- [จุดแก้ไขที่ 1]: ตั้งค่าเริ่มต้นให้ Session State ---
# ต้องทำเพื่อให้ Widget number_input รู้ว่าต้องดึงค่าจากไหนมาแสดงตอนเริ่มต้น
input_keys = ["income_input", "tenure_input", "years_input", "debt_input", "defaults_input", "loan_req_input"]
for key in input_keys:
    if key not in st.session_state:
        st.session_state[key] = 0

st.set_page_config(page_title="iBank Hybrid Credit Score", layout="centered")

# Custom CSS สำหรับ iBank Theme
st.markdown("""
    <style>
    .stApp { background-color: #61C1B1; }
    .stButton>button { width: 100%; border-radius: 25px; background-color: #3E7B4F !important; color: white; font-weight: bold; height: 3.5em; }
    label { color: white !important; font-weight: bold !important; }
    h1, h2, h3 { color: white !important; text-align: center; }
    
    .desc-label {
        color: #F0B042 !important; 
        font-size: 14px !important; 
        font-weight: bold !important; 
        margin-bottom: 5px !important; 
        margin-left: 10px !important;
        text-align: left;
        display: block;
    }
    </style>
""", unsafe_allow_html=True)

# --- [จุดแก้ไขที่ 2]: ฟังก์ชันล้างข้อมูล (Clear Callback) ---
# สร้างฟังก์ชันแยกออกมาเพื่อเรียกใช้ใน on_click
def clear_form():
    st.session_state.income_input = 0
    st.session_state.tenure_input = 0
    st.session_state.years_input = 0
    st.session_state.debt_input = 0
    st.session_state.defaults_input = 0
    st.session_state.loan_req_input = 0

st.title("การคำนวณเครดิต")

# ฟังก์ชันแสดงผลสรุป (Dialog)
@st.dialog("ผลการวิเคราะห์สินเชื่อ iBank", width="large")
def show_result(res_data, requested_loan, requested_years):
    rate = res_data.get('rate', 7.95)
    years = requested_years if requested_years > 0 else 5
    
    total_interest = (requested_loan * (rate / 100) * years)
    monthly_installment = (requested_loan + total_interest) / (years * 12)

    st.markdown("""
        <div style='text-align:center; margin-bottom: 10px;'>
            <div style='background-color: #F0B042; color: black; padding: 10px 40px; 
                        border-radius: 30px; display: inline-block; font-weight: bold; font-size: 24px;'>
                คำนวณค่างวดสินเชื่อ
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div style='display: flex; justify-content: center; margin-bottom: 20px;'>
            <div style='width: 220px; height: 220px; border-radius: 50%; background-color: #61C1B1; 
                        border: 8px solid #F0B042; display: flex; flex-direction: column; 
                        justify-content: center; align-items: center; color: white; text-align: center;'>
                <p style='margin: 0; font-size: 16px;'>จำนวนเงิน<br>ผ่อนชำระรายเดือน</p>
                <h1 style='margin: 5px 0; color: white; font-size: 44px;'>{monthly_installment:,.0f}</h1>
                <p style='margin: 0; font-size: 16px;'>บาท</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    def info_box(desc_text, value, unit):
        st.markdown(f"""
            <div style='margin-bottom: 15px;'>
                <span class="desc-label">{desc_text}</span>
                <div style='background-color: #E0E0E0; padding: 12px 20px; border-radius: 30px; 
                            display: flex; justify-content: space-between; align-items: center;'>
                    <span style='font-size: 18px; font-weight: bold; color: #333;'>{value}</span>
                    <span style='color: #666; font-size: 14px;'>{unit}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        info_box("สรุปวงเงินสินเชื่อ", f"{requested_loan:,.0f}", "บาท")
        info_box("ระยะเวลาผ่อนชำระ", f"{years}", "ปี")
        info_box("อัตรากำไรต่อปี", f"{rate:.2f}", "%")
    
    with c2:
        info_box("คะแนนเครดิตที่ได้", f"{res_data.get('score')}", "คะแนน")
        info_box("ระดับเกรดลูกค้า", f"{res_data.get('grade')}", "เกรด")
        
        is_approved = res_data.get('is_approved', False)
        status_val = res_data.get('status', 'N/A')
        dots = "<span style='color:#FF4B4B;'>●</span><span style='color:#FF4B4B;'>●</span><span style='color:#28A745;'>●</span>" if is_approved else "🔴"
        cust_id = res_data.get('customer_id', 'N/A')
        info_box(f"สถานะพิจารณา (ID: {cust_id})", f"{dots} {status_val}", "")

    dsr_val = res_data.get('dsr', 0.0)
    st.markdown(f"<p style='text-align: right; color: #3E7B4F; font-weight: bold; padding-right: 15px;'>Total DSR: {dsr_val:.2f}%</p>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 11px; color: #666; text-align: center;'>*ผลการคำนวณเบื้องต้นเพื่อใช้ประกอบการพิจารณาเท่านั้น</p>", unsafe_allow_html=True)

# ส่วนรับข้อมูล Input
with st.container():
    st.subheader("กรอกข้อมูล")
    c1, c2 = st.columns(2)
    with c1:
        income = st.number_input("รายได้สุทธิต่อเดือน", min_value=0, key="income_input", step=1000)
        tenure = st.number_input("อายุงาน (เดือน)", min_value=0, key="tenure_input", step=1)
        loan_years = st.number_input("ระยะเวลาที่ต้องการกู้ (ปี)", min_value=0, max_value=30, key="years_input")
    with c2:
        debt = st.number_input("ภาระหนี้เดิมต่อเดือน", min_value=0, key="debt_input", step=1000)
        defaults = st.number_input("ประวัติผิดนัดชำระ (ครั้ง)", min_value=0, key="defaults_input", step=1)
        loan_req = st.number_input("วงเงินที่ต้องการกู้", min_value=0, key="loan_req_input", step=10000)

col_btn1, col_btn2 = st.columns([3, 1])

with col_btn1:
    predict_btn = st.button("วิเคราะห์และคำนวณสินเชื่อ")

with col_btn2:
    # --- [จุดแก้ไขที่ 3]: ใช้ on_click คู่กับฟังก์ชันล้างข้อมูล ---
    st.button("ล้างข้อมูล", on_click=clear_form)

if predict_btn:
    if income == 0 and loan_req == 0:
        st.warning("กรุณากรอกข้อมูลเพื่อทำการวิเคราะห์")
    else:
        unique_id = int(time.time()) % 100000 + random.randint(1000, 9999)
        payload = {
            "customer_id": unique_id,
            "net_monthly_income": float(income),
            "yearly_debt_payments": float(debt * 12),
            "account_tenure_months": int(tenure),
            "prev_defaults": int(defaults),
            "mou_status": "N"
        }

        try:
            response = requests.post("http://127.0.0.1:8000/predict", json=payload)
            if response.status_code == 200:
                res = response.json()
                res['customer_id'] = unique_id 
                show_result(res, loan_req, loan_years)
            else:
                st.error(f"API Error: {response.status_code}")
        except Exception as e:
            st.error(f"ไม่สามารถเชื่อมต่อกับ API ได้: {e}")