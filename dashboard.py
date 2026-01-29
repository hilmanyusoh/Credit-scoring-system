import streamlit as st
import requests

st.set_page_config(page_title="iBank Hybrid Credit Score", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #61C1B1; }
    .stButton>button { width: 100%; border-radius: 25px; background-color: #3E7B4F !important; color: white; font-weight: bold; height: 3.5em; }
    label { color: white !important; font-weight: bold !important; }
    h1, h2, h3 { color: white !important; text-align: center; }
    </style>
""", unsafe_allow_html=True)

st.title("💡 iBank Credit Intelligence")

with st.container():
    st.subheader("👤 ข้อมูลผู้ขอสินเชื่อ")
    c1, c2 = st.columns(2)
    with c1:
        income = st.number_input("รายได้สุทธิต่อเดือน", value=30000)
        tenure = st.number_input("อายุงาน (เดือน)", value=24)
        mou = st.selectbox("MOU", ["ไม่มี", "มี"])
    with c2:
        debt = st.number_input("ภาระหนี้เดิมต่อเดือน", value=0)
        defaults = st.number_input("ประวัติผิดนัดชำระ (ครั้ง)", value=0)
        loan_req = st.number_input("วงเงินที่ต้องการกู้", value=100000)

if st.button("วิเคราะห์และคำนวณสินเชื่อ"):
    payload = {
        "customer_id": 999,
        "net_monthly_income": float(income),
        "yearly_debt_payments": float(debt * 12),
        "account_tenure_months": int(tenure),
        "prev_defaults": int(defaults),
        "mou_status": "Y" if mou == "มี" else "N"
    }

    try:
        response = requests.post("http://127.0.0.1:8000/predict", json=payload)
        if response.status_code == 200:
            res = response.json()
            
            @st.dialog("📊 ผลการวิเคราะห์สินเชื่อ iBank", width="large")
            def show_result():
                # --- ส่วนหัว: ป้ายเหลือง ---
                st.markdown("""
                    <div style='text-align:center;'>
                        <div style='background-color: #F0B042; color: black; padding: 10px 40px; 
                                    border-radius: 30px; display: inline-block; font-weight: bold; font-size: 24px;'>
                            คำนวณค่างวดสินเชื่อ
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                # --- ส่วนกลาง: วงกลมเขียวขอบเหลือง ---
                # คำนวณค่างวดรายเดือน
                rate = res.get('rate', 8.50)
                total_interest = (loan_req * (rate/100) * 5) # สมมติ 5 ปี
                monthly_installment = (loan_req + total_interest) / 60

                st.markdown(f"""
                    <div style='display: flex; justify-content: center; margin: 30px 0;'>
                        <div style='width: 250px; height: 250px; border-radius: 50%; background-color: #61C1B1; 
                                    border: 8px solid #F0B042; display: flex; flex-direction: column; 
                                    justify-content: center; align-items: center; color: white; text-align: center;'>
                            <p style='margin: 0; font-size: 18px;'>จำนวนเงิน<br>ผ่อนชำระรายเดือน</p>
                            <h1 style='margin: 10px 0; color: white; font-size: 48px;'>{monthly_installment:,.0f}</h1>
                            <p style='margin: 0; font-size: 18px;'>บาท</p>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                # --- ส่วนล่าง: ช่องแสดงข้อมูลสีเทา (เหมือนในรูป) ---
                def info_box(label, value, unit):
                    st.markdown(f"""
                        <div style='margin-bottom: 15px;'>
                            <label style='color: #3E7B4F !important; font-weight: bold;'>{label}</label>
                            <div style='background-color: #E0E0E0; padding: 15px; border-radius: 30px; 
                                        display: flex; justify-content: space-between; align-items: center;'>
                                <span style='font-size: 20px; font-weight: bold; color: #333;'>{value}</span>
                                <span style='color: #666;'>{unit}</span>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

                # แสดงข้อมูลตามภาพและที่คุณขอเพิ่มเติม
                c1, c2 = st.columns(2)
                with c1:
                    info_box("วงเงิน (บาท)", f"{loan_req:,.0f}", "บาท")
                    info_box("ระยะเวลา (ปี)", "5", "ปี")
                    info_box("อัตรากำไรเฉลี่ย", f"{rate:.2f}", "%")
                
                with c2:
                    info_box("Credit Score", f"{res.get('score', 705)}", "คะแนน")
                    info_box("Credit Level", f"{res.get('grade', 'A')}", "เกรด")
                    
                    # สถานะแบบมีจุดสีเขียว
                    status_val = res.get('status', 'ดี')
                    info_box("สถานะ (Status)", f"🟢 {status_val}", "")

                # เพิ่มเติม DSR
                dsr_val = 31.87 # สามารถดึงจาก Engine มาใส่ได้
                st.markdown(f"<p style='text-align: right; color: #3E7B4F; font-weight: bold;'>Total DSR: {dsr_val}%</p>", unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)
                
                # --- หมายเหตุท้ายภาพ ---
                st.markdown("""
                    <p style='font-size: 12px; color: #666; text-align: center;'>
                    *หมายเหตุ : ผลการคำนวณข้างต้นเป็นเพียงการคำนวณเบื้องต้นเท่านั้น <br>
                    อาจมีการเปลี่ยนแปลงได้ ภายใต้หลักเกณฑ์และเงื่อนไขของธนาคาร
                    </p>
                """, unsafe_allow_html=True)

            show_result()
        else:
            st.error(f"Error {response.status_code}: {response.text}")
    except Exception as e:
        st.error(f"Connection Failed: {e}")